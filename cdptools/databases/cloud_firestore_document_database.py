#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

import requests

import firebase_admin
import pandas as pd
from firebase_admin import credentials, firestore

from . import exceptions
from .document_store_database import (
    DocumentStoreDatabase,
    OrderCondition,
    WhereCondition,
    WhereOperators,
    CDPCollections,
)

###############################################################################

log = logging.getLogger(__name__)

FIRESTORE_BASE_URI = "https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents"  # noqa: E501
FIRESTORE_QUERY_ADDITIONS = "{table}?{attachments}&fields=documents(fields%2Cname)"

###############################################################################


class NoCredResponseTypes:
    boolean: str = "booleanValue"
    double: str = "doubleValue"
    dt: str = "timestampValue"
    integer: str = "integerValue"
    null: str = "nullValue"
    string: str = "stringValue"


class CloudFirestoreWhereOperators:
    eq: str = "EQUAL"
    contains: str = "ARRAY_CONTAINS"
    gt: str = "GREATER_THAN"
    lt: str = "LESS_THAN"
    gteq: str = "GREATER_THAN_OR_EQUAL"
    lteq: str = "LESS_THAN_OR_EQUAL"


class CloudFirestoreDocumentDatabase(DocumentStoreDatabase):
    def _initialize_creds_db(
        self, credentials_path: Union[str, Path], name: Optional[str] = None
    ):
        # Resolve credentials
        credentials_path = Path(credentials_path).resolve(strict=True)

        # Initialize database reference
        cred = credentials.Certificate(str(credentials_path))

        # Check name
        # This is done as if the name is None we just want to initialize the main
        # connection
        if name:
            firebase_admin.initialize_app(cred, name=name)
        else:
            firebase_admin.initialize_app(cred)

        # Store configuration
        self._credentials_path = credentials_path
        self._root = firestore.client()

    def __init__(
        self,
        project_id: Optional[str] = None,
        credentials_path: Optional[Union[str, Path]] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        # With credentials:
        if credentials_path:
            self._initialize_creds_db(credentials_path, name)

            # We fetch all tables in case some tables exist in target, but not in source
            # Path returns a tuple, and root collection path is in first index
            self._tables = [coll._path[0] for coll in self._root.collections()]
        elif project_id:
            self._credentials_path = None
            self._project_id = project_id
            self._db_uri = FIRESTORE_BASE_URI.format(project_id=project_id)
            self._tables = [e.value for e in CDPCollections]
        else:
            raise exceptions.MissingParameterError(["project_id", "credentials_path"])

        self._cdp_table_to_function_dict = {
            "event": self.get_or_upload_event,
            "person": self.get_or_upload_person,
            "body": self.get_or_upload_body,
            "file": self.get_or_upload_file,
            "transcript": self.get_or_upload_transcript,
            "seat": self.get_or_upload_seat,
            "role": self.get_or_upload_role,
            "minutes_item": self.get_or_upload_minutes_item,
            "event_minutes_item": self.get_or_upload_event_minutes_item,
            "vote": self.get_or_upload_vote,
            "matter": self.get_or_upload_matter,
            "matter_type": self.get_or_upload_matter_type,
        }

    @staticmethod
    def _jsonify_firestore_response(fields: Dict) -> Dict:
        formatted = {}

        # Cast or parse values from returned
        for k, type_and_value in fields.items():
            if NoCredResponseTypes.boolean in type_and_value:
                formatted[k] = type_and_value[NoCredResponseTypes.boolean]
            elif NoCredResponseTypes.null in type_and_value:
                formatted[k] = type_and_value[NoCredResponseTypes.null]
            elif NoCredResponseTypes.string in type_and_value:
                formatted[k] = type_and_value[NoCredResponseTypes.string]
            elif NoCredResponseTypes.double in type_and_value:
                formatted[k] = float(type_and_value[NoCredResponseTypes.double])
            elif NoCredResponseTypes.integer in type_and_value:
                formatted[k] = int(type_and_value[NoCredResponseTypes.integer])
            elif NoCredResponseTypes.dt in type_and_value:
                if "." in type_and_value[NoCredResponseTypes.dt]:
                    formatted[k] = datetime.strptime(
                        type_and_value[NoCredResponseTypes.dt], "%Y-%m-%dT%H:%M:%S.%fZ"
                    )
                else:
                    formatted[k] = datetime.strptime(
                        type_and_value[NoCredResponseTypes.dt], "%Y-%m-%dT%H:%M:%SZ"
                    )
            else:
                formatted[k] = type_and_value

        return formatted

    def _select_document_by_id_with_creds(self, table: str, id: str) -> Dict:
        # Get result
        result = self._root.collection(table).document(id).get().to_dict()

        # Found, return expansion
        if result:
            return {f"{table}_id": id, **result}

        # Not found, return None
        return None

    def _select_document_by_id_no_creds(self, table: str, id: str) -> Dict:
        # Fill target uri
        target_uri = f"{self._db_uri}/{table}/{id}"

        # Get
        response = requests.get(target_uri)

        # Raise errors
        response.raise_for_status()

        # To json
        response = response.json()

        # Check for error
        if "fields" in response:
            # Format response
            return {
                f"{table}_id": id,
                **self._jsonify_firestore_response(response["fields"]),
            }

        raise KeyError(f"No document with id: {id} exists.")

    def select_document_by_id(self, table: str, id: str, **kwargs) -> Dict:
        # With credentials
        if self._credentials_path:
            return self._select_document_by_id_with_creds(table=table, id=id)

        return self._select_document_by_id_no_creds(table=table, id=id)

    def _select_documents_as_list_with_creds(
        self,
        table: str,
        filters: Optional[List[Union[WhereCondition, List, Tuple]]] = None,
        order_by: Optional[Union[List, OrderCondition, str, Tuple]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        # Create base table ref
        ref = self._root.collection(table)

        # Apply filters
        if filters:
            for f in filters:
                # Construct WhereCondition
                f = self._construct_where_condition(f)
                # Apply
                # Returns type Query
                ref = ref.where(f.column_name, f.operator, f.value)

        # Apply order by
        if order_by:
            order_by = self._construct_orderby_condition(order_by)
            ref = ref.order_by(order_by.column_name, direction=order_by.operator)

        # Apply limit
        if limit:
            ref = ref.limit(limit)

        # Get and expand
        return [{f"{table}_id": i.id, **i.to_dict()} for i in ref.stream()]

    @staticmethod
    def _convert_base_where_operator_to_cloud_firestore_where_operator(op: str) -> str:
        if op == WhereOperators.eq:
            return CloudFirestoreWhereOperators.eq
        if op == WhereOperators.contains:
            return CloudFirestoreWhereOperators.contains
        if op == WhereOperators.gt:
            return CloudFirestoreWhereOperators.gt
        if op == WhereOperators.lt:
            return CloudFirestoreWhereOperators.lt
        if op == WhereOperators.gteq:
            return CloudFirestoreWhereOperators.gteq
        if op == WhereOperators.lteq:
            return CloudFirestoreWhereOperators.lteq

        raise ValueError(
            f"Unsure how to convert where operator: {op}. "
            f"No mapping exists between base operators and "
            f"cloud firestore specific operators."
        )

    @staticmethod
    def _get_cloud_firestore_value_type(
        val: Union[bool, float, datetime, int, str, None]
    ) -> str:
        if isinstance(val, bool):
            return NoCredResponseTypes.boolean
        if isinstance(val, float):
            return NoCredResponseTypes.double
        if isinstance(val, datetime):
            return NoCredResponseTypes.dt
        if isinstance(val, int):
            return NoCredResponseTypes.integer
        if isinstance(val, str):
            return NoCredResponseTypes.string
        if val is None:
            return NoCredResponseTypes.null

        raise ValueError(
            f"Unsure how to determine cloud firestore type from object: {val} "
            f"(type: {type(val)})"
        )

    def _select_documents_as_list_no_creds(
        self,
        table: str,
        filters: Optional[List[Union[WhereCondition, List, Tuple]]] = None,
        order_by: Optional[Union[List, OrderCondition, str, Tuple]] = None,
        limit: int = 1000,
    ) -> List[Dict]:
        # https://cloud.google.com/firestore/docs/reference/rest/v1/projects.databases.documents/runQuery
        structuredQuery = {"from": [{"collectionId": table, "allDescendants": False}]}

        # Apply filters
        if filters:
            # Empty list to store constructed filters in
            constructed_filters = []
            for f in filters:
                # Construct WhereCondition
                f = self._construct_where_condition(f)

                # Handle datetimes
                filter_val = f.value
                if isinstance(filter_val, datetime):
                    filter_val = f"{filter_val.isoformat()}Z"

                # Add filter to structuredQuery
                constructed_filters.append(
                    {
                        "fieldFilter": {
                            "field": {"fieldPath": f.column_name},
                            "op": self._convert_base_where_operator_to_cloud_firestore_where_operator(  # noqa: E501
                                f.operator
                            ),
                            "value": {
                                self._get_cloud_firestore_value_type(
                                    f.value
                                ): filter_val
                            },
                        }
                    }
                )

            # Add filters to the structuredQuery
            structuredQuery["where"] = {
                "compositeFilter": {"op": "AND", "filters": constructed_filters}
            }

        # Format order by
        if order_by:
            order_condition = self._construct_orderby_condition(order_by)
            structuredQuery["orderBy"] = [
                {
                    "field": {"fieldPath": order_condition.column_name},
                    "direction": order_condition.operator,
                }
            ]

        # Override limit from None to default 1000
        if limit is None:
            limit = 1000

        # Format limit
        structuredQuery["limit"] = limit

        # Post
        response = requests.post(
            f"{self._db_uri}:runQuery",
            data=json.dumps({"structuredQuery": structuredQuery}),
        )

        # Raise errors
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            raise exceptions.FailedRequestError(response.json())

        # To json
        response = response.json()

        # Return formatted
        try:
            return [
                {
                    f"{table}_id": document["document"]["name"].split("/")[
                        -1
                    ],  # Get last item in the uri
                    **self._jsonify_firestore_response(document["document"]["fields"]),
                }
                for document in response
            ]
        except KeyError:
            return []

    def select_documents_as_list(
        self,
        table: str,
        filters: Optional[List[Union[WhereCondition, List, Tuple]]] = None,
        order_by: Optional[Union[List, OrderCondition, str, Tuple]] = None,
        limit: Optional[int] = None,
        **kwargs,
    ) -> List[Dict]:
        # With credentials
        if self._credentials_path:
            return self._select_documents_as_list_with_creds(
                table=table, filters=filters, order_by=order_by, limit=limit
            )

        return self._select_documents_as_list_no_creds(
            table=table, filters=filters, order_by=order_by, limit=limit
        )

    def select_documents_as_dictionary(
        self,
        table: str,
        filters: Optional[List[Union[WhereCondition, List, Tuple]]] = None,
        order_by: Optional[Union[OrderCondition, List, Tuple, str]] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get a dictionary of documents from a table optionally using filters 
        (a list of where conditions), ordering, and limit.

        Parameters
        ----------
        table: str
            The name of the table to retrieve data from.
        filters: Optional[List[Union[WhereCondition, List, Tuple]]]
            A list of filters (where conditions) to add filter down the query.
        order_by: Optional[Union[OrderCondition, List, Tuple, str]]
            An order by condition to order the results by before returning.
        limit: Optional[int]
            An integer limit to how many documents should be returned that match the 
            query provided. 
            Commonly, running queries without credentials will have a default
            limit value.

        Returns
        -------
        results: Dict[str, Dict[str, Any]]
            The results of the query returned as a dictionary mapping unique id to a
            dictionary of that documents data from the table queried. If no documents 
            are found, returns an empty dictionary.
        """
        # Get, format, and return
        return self._reshape_list_of_documents_to_dict(
            self.select_documents_as_list(
                table=table, filters=filters, order_by=order_by, limit=limit
            )
        )

    def select_documents_as_dataframe(
        self,
        table: str,
        filters: Optional[List[Union[WhereCondition, List, Tuple]]] = None,
        order_by: Optional[Union[OrderCondition, List, Tuple, str]] = None,
        limit: Optional[int] = None,
        set_id_to_index: bool = False,
    ) -> pd.DataFrame:
        """
        Get a dataframe of documents from a table optionally using filters 
        (a list of where conditions), ordering, and limit.

        Parameters
        ----------
        table: str
            The name of the table to retrieve data from.
        filters: Optional[List[Union[WhereCondition, List, Tuple]]]
            A list of filters (where conditions) to add filter down the query.
        order_by: Optional[Union[OrderCondition, List, Tuple, str]]
            An order by condition to order the results by before returning.
        limit: Optional[int]
            An integer limit to how many documents should be returned that match 
            the query provided. 
            Commonly, running queries without credentials will have a default
            limit value.
        set_id_to_index: bool
            Boolean value to determine whether or not the unique id values for this
            data should be used as the index of the dataframe.

        Returns
        -------
        results: pandas.DataFrame
            The results of the query returned as a pandas DataFrame, where each row is
            a unique document from the table queried. 
            If no documents are found, returns an empty DataFrame.
        """
        # Get data
        data = self.select_documents_as_list(
            table=table, filters=filters, order_by=order_by, limit=limit
        )

        # Format
        if set_id_to_index:
            return self._reshape_list_of_documents_to_dataframe(data, table)

        return self._reshape_list_of_documents_to_dataframe(data)

    def _select_documents_with_max_results_expectation(
        self,
        table: str,
        pks: List[Union[WhereCondition, List, Tuple]],
        expected_max_documents: int,
    ):
        # Find matching
        pks = [self._construct_where_condition(pk) for pk in pks]
        matching = self.select_documents_as_list(table=table, filters=pks)

        # Handle expectation
        if len(matching) > expected_max_documents:
            raise exceptions.UniquenessError(
                table, [pk.column_name for pk in pks], matching
            )
        elif len(matching) == 0:
            return None
        else:
            return matching

    def _get_or_upload_document(
        self, table: str, pks: List[Union[WhereCondition, List, Tuple]], values: Dict
    ) -> Dict:
        # Reject any upload without credentials
        if self._credentials_path is None:
            raise exceptions.MissingCredentialsError()

        # Fast return for already stored
        found = self._select_documents_with_max_results_expectation(
            table=table, pks=pks, expected_max_documents=1
        )
        # Return or upload
        if found:
            return found[0]
        else:
            # Create id
            id = str(uuid4())
            # Store the document
            self._root.collection(table).document(id).set(values)
            log.debug(
                f"Uploaded values: {values} " f"To id: {id} " f"On table: {table}"
            )

            # Return document
            return {f"{table}_id": id, **values}

    def get_or_upload_body(
        self,
        name: str,
        tag: str,
        start_date: datetime,
        is_active: bool,
        chair_person_id: str,
        description: Optional[str] = None,
        end_date: Optional[datetime] = None,
        external_source_id: Optional[Any] = None,
    ) -> Dict:
        return self._get_or_upload_document(
            table="body",
            pks=[("name", name)],
            values={
                "name": name,
                "description": description,
                "tag": tag,
                "start_date": start_date,
                "end_date": end_date,
                "is_active": is_active,
                "chair_person_id": chair_person_id,
                "external_source_id": external_source_id,
                "created": datetime.utcnow(),
            },
        )

    def get_or_upload_minutes_item(
        self,
        name: str,
        matter: Dict[str, str],
        description: Optional[str] = None,
        external_source_id: Optional[Any] = None,
    ) -> Dict:
        return self._get_or_upload_document(
            table="minutes_item",
            pks=[("name", name)],
            values={
                "name": name,
                "description": description,
                "matter": matter,
                "external_source_id": external_source_id,
                "created": datetime.utcnow(),
            },
        )

    def get_event(self, video_uri: str) -> Dict:
        # Try find
        found = self._select_documents_with_max_results_expectation(
            table="event", pks=[("video_uri", video_uri)], expected_max_documents=1
        )
        if found:
            return found[0]

        return None

    def get_or_upload_event(
        self,
        body: Dict[str, str],
        event_datetime: datetime,
        thumbnail_static_file: Dict[str, str],
        thumbnail_hover_file: Dict[str, str],
        keywords: List[Dict[str, str]],
        keyword_ids: List[str],
        matters: List[Dict[str, str]],
        matter_ids: List[str],
        minutes_items: List[Dict[str, str]],
        minutes_item_ids: List[str],
        people: List[Dict[str, str]],
        person_ids: List[str],
        agenda_uri: str,
        video_uri: Optional[str] = None,
        external_source_id: Optional[str] = None,
        minutes_uri: Optional[str] = None,
    ) -> Dict:
        return self._get_or_upload_document(
            table="event",
            pks=[("video_uri", video_uri)],
            values={
                "body": body,
                "event_datetime": event_datetime,
                "thumnail_static_file": thumbnail_static_file,
                "video_uri": video_uri,
                "keywords": keywords,
                "keyword_ids": keyword_ids,
                "matters": matters,
                "matter_ids": matter_ids,
                "minutes_items": minutes_items,
                "minutes_item_ids": minutes_item_ids,
                "people": people,
                "person_ids": person_ids,
                "external_source_id": external_source_id,
                "agenda_uri": agenda_uri,
                "minutes_uri": minutes_uri,
                "created": datetime.utcnow(),
            },
        )

    def get_or_upload_event_minutes_item(
        self,
        event_id: str,
        minutes_item: Dict[str, str],
        index: int,
        matter: Dict[str, str],
        votes: List[Dict[str, str]],
        vote_ids: List[str],
        files: List[Dict[str, str]],
        file_ids: List[str],
        decision: Optional[str] = None,
    ) -> Dict:
        return self._get_or_upload_document(
            table="event_minutes_item",
            pks=[("event_id", event_id), ("minutes_item.id", minutes_item["id"])],
            values={
                "event_id": event_id,
                "minutes_item": minutes_item,
                "index": index,
                "decision": decision,
                "matter": matter,
                "votes": votes,
                "vote_ids": vote_ids,
                "files": files,
                "file_ids": file_ids,
                "created": datetime.utcnow(),
            },
        )

    def get_or_upload_matter(
        self,
        name: str,
        matter_type: Dict[str, str],
        title: str,
        status: str,
        most_recent_event: Dict[str, Any],
        next_event: Dict[str, Any],
        keywords: List[Dict[str, str]],
        keyword_ids: List[str],
        updated: datetime,
        external_source_id: Optional[Any] = None,
    ) -> Dict:
        return self._get_or_upload_document(
            table="matter",
            pks=[("name", name)],
            values={
                "name": name,
                "matter_type": matter_type,
                "title": title,
                "status": status,
                "most_recent_event": most_recent_event,
                "next_event": next_event,
                "keywords": keywords,
                "keyword_ids": keyword_ids,
                "external_source_id": external_source_id,
                "updated": updated,
                "created": datetime.utcnow(),
            },
        )

    def get_or_upload_matter_type(
        self, name: str, external_source_id: Optional[Any] = None,
    ) -> Dict:
        return self._get_or_upload_document(
            table="matter_type",
            pks=[("name", name)],
            values={
                "name": name,
                "external_source_id": external_source_id,
                "created": datetime.utcnow(),
            },
        )

    def get_or_upload_person(
        self,
        name: str,
        is_active: bool,
        is_council_president: bool,
        most_recent_seat: Dict[str, str],
        most_recent_chair_body: Dict[str, str],
        terms_serving_in_current_seat_role: int,
        terms_serving_in_current_committee_chair_role: int,
        picture_file: Dict[str, str],
        router_id: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        website: Optional[str] = None,
        external_source_id: Optional[Any] = None,
    ) -> Dict:
        return self._get_or_upload_document(
            table="person",
            pks=[("name", name), ("email", email)],
            values={
                "name": name,
                "email": email,
                "phone": phone,
                "website": website,
                "picture_file": picture_file,
                "is_active": is_active,
                "is_council_president": is_council_president,
                "most_recent_seat": most_recent_seat,
                "most_recent_chair_body": most_recent_chair_body,
                "terms_serving_in_current_seat_role": terms_serving_in_current_seat_role,  # noqa: E501
                "terms_serving_in_current_committee_chair_role": terms_serving_in_current_committee_chair_role,  # noqa: E501
                "external_source_id": external_source_id,
                "created": datetime.utcnow(),
            },
        )

    def get_or_upload_vote(
        self,
        matter: Dict[str, str],
        event: Dict[str, Any],
        event_minutes_item: Dict[str, str],
        person: Dict[str, str],
        vote_decision: str,
        is_majority: bool,
        external_vote_item_id: Optional[any] = None,
    ) -> Dict:
        return self._get_or_upload_document(
            table="vote",
            pks=[
                ("person.id", person["id"]),
                ("event_minutes_item.id", event_minutes_item["id"]),
            ],
            values={
                "matter": matter,
                "event": event,
                "event_minutes_item": event_minutes_item,
                "person": person,
                "vote_decision": vote_decision,
                "is_majority": is_majority,
                "external_vote_item_id": external_vote_item_id,
                "created": datetime.utcnow(),
            },
        )

    def get_or_upload_file(
        self,
        uri: str,
        filename: Optional[str] = None,
        description: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Dict:
        if filename is None:
            filename = uri.split("/")[-1]

        return self._get_or_upload_document(
            table="file",
            pks=[("uri", uri)],
            values={
                "uri": uri,
                "filename": filename,
                "description": description,
                "content_type": content_type,
                "created": datetime.utcnow(),
            },
        )

    def get_or_upload_seat(
        self, electoral_area: str, electoral_type: str, map_file_id: str, map_uri: str,
    ) -> Dict:
        return self._get_or_upload_document(
            table="seat",
            pks=[
                ("electoral_area", electoral_area),
                ("electoral_type", electoral_type),
            ],  # noqa: E501
            values={
                "electoral_area": electoral_area,
                "electoral_type": electoral_type,
                "map_file_id": map_file_id,
                "map_uri": map_uri,
                "created": datetime.utcnow(),
            },
        )

    def get_or_upload_transcript(
        self, event_id: str, file_id: str, confidence: Optional[float] = None
    ) -> Dict:
        return self._get_or_upload_document(
            table="transcript",
            pks=[("event_id", event_id), ("file_id", file_id)],
            values={
                "event_id": event_id,
                "file_id": file_id,
                "confidence": confidence,
                "created": datetime.utcnow(),
            },
        )

    def get_or_upload_role(
        self,
        person: Dict[str, str],
        title: str,
        body: Dict[str, str],
        seat_id: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        external_source_id: Optional[any] = None,
    ) -> Dict:
        return self._get_or_upload_document(
            table="role",
            pks=[("title", title), ("body.id", body["id"])],
            values={
                "person": person,
                "title": title,
                "body": body,
                "start_date": start_date,
                "end_date": end_date,
                "seat_id": seat_id,
                "external_source_id": external_source_id,
                "created": datetime.utcnow(),
            },
        )

    def update_collection_with_field(
        self, collection: str, document_id: str, field: str, value: any,
    ) -> Dict:
        document = self._root.collection(collection).document(document_id)
        document.update({field: value})

    def drop_collection(self, table, batch_size):
        docs = self._root.collection(table).list_documents(batch_size)

        total_del = 0
        while docs:
            deleted_count = 0
            for doc in docs:
                doc.delete()
                deleted_count += 1
                total_del += 1

            # If there could potentially be more documents in the table
            if deleted_count >= batch_size:
                docs = self._root.collection(table).list_documents(batch_size)
            else:
                log.info(
                    "Deleted {} docs from {} table in batches of {} docs".format(
                        total_del, table, batch_size
                    )
                )
                return

    @property
    def collections(self) -> List[str]:
        log.info("Fetched the following tables: {}".format(str(self._tables)))
        return self._tables

    def __str__(self):
        if self._credentials_path:
            return f"<CloudFirestoreDatabase [{self._credentials_path}]>"

        return f"<CloudFirestoreDatabase [{self._project_id}]>"

    def __repr__(self):
        return str(self)
