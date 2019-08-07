#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

import firebase_admin
import requests
from firebase_admin import credentials, firestore

from ..indexers import Indexer
from . import exceptions
from .database import (Database, Match, OrderCondition, TermResult,
                       WhereCondition, WhereOperators)

###############################################################################

log = logging.getLogger(__name__)

FIRESTORE_BASE_URI = "https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents"
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


class CloudFirestoreDatabase(Database):

    def _initialize_creds_db(self, credentials_path: Union[str, Path], name: Optional[str] = None):
        # Resolve credentials
        credentials_path = Path(credentials_path).resolve(strict=True)

        # Initialize database reference
        cred = credentials.Certificate(str(credentials_path))

        # Check name
        # This is done as if the name is None we just want to initialize the main connection
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
        **kwargs
    ):
        # With credentials:
        if credentials_path:
            self._initialize_creds_db(credentials_path, name)
        elif project_id:
            self._credentials_path = None
            self._project_id = project_id
            self._db_uri = FIRESTORE_BASE_URI.format(project_id=project_id)
        else:
            raise exceptions.MissingParameterError(["project_id", "credentials_path"])

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
                        type_and_value[NoCredResponseTypes.dt],
                        "%Y-%m-%dT%H:%M:%S.%fZ"
                    )
                else:
                    formatted[k] = datetime.strptime(
                        type_and_value[NoCredResponseTypes.dt],
                        "%Y-%m-%dT%H:%M:%SZ"
                    )
            else:
                formatted[k] = type_and_value

        return formatted

    def _select_row_by_id_with_creds(self, table: str, id: str) -> Dict:
        # Get result
        result = self._root.collection(table).document(id).get().to_dict()

        # Found, return expansion
        if result:
            return {f"{table}_id": id, **result}

        # Not found, return None
        return None

    def _select_row_by_id_no_creds(self, table: str, id: str) -> Dict:
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
            return {f"{table}_id": id, **self._jsonify_firestore_response(response["fields"])}

        raise KeyError(f"No row with id: {id} exists.")

    def select_row_by_id(self, table: str, id: str, **kwargs) -> Dict:
        # With credentials
        if self._credentials_path:
            return self._select_row_by_id_with_creds(table=table, id=id)

        return self._select_row_by_id_no_creds(table=table, id=id)

    def _select_rows_as_list_with_creds(
        self,
        table: str,
        filters: Optional[List[Union[WhereCondition, List, Tuple]]] = None,
        order_by: Optional[Union[List, OrderCondition, str, Tuple]] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        # Create base table ref
        ref = self._root.collection(table)

        # Apply filters
        if filters:
            for f in filters:
                # Construct WhereCondition
                f = self._construct_where_condition(f)
                # Apply
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

        raise ValueError(f"Unsure how to convert where operator: {op}. "
                         f"No mapping exists between base operators and cloud firestore specific operators.")

    @staticmethod
    def _get_cloud_firestore_value_type(val: Union[bool, float, datetime, int, str, None]) -> str:
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

        raise ValueError(f"Unsure how to determine cloud firestore type from object: {val} (type: {type(val)})")

    def _select_rows_as_list_no_creds(
        self,
        table: str,
        filters: Optional[List[Union[WhereCondition, List, Tuple]]] = None,
        order_by: Optional[Union[List, OrderCondition, str, Tuple]] = None,
        limit: int = 1000
    ) -> List[Dict]:
        # https://cloud.google.com/firestore/docs/reference/rest/v1/projects.databases.documents/runQuery
        structuredQuery = {
            "from": [
                {
                    "collectionId": table,
                    "allDescendants": False
                }
            ]
        }

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
                constructed_filters.append({
                    "fieldFilter": {
                        "field": {
                            "fieldPath": f.column_name
                        },
                        "op": self._convert_base_where_operator_to_cloud_firestore_where_operator(f.operator),
                        "value": {
                            self._get_cloud_firestore_value_type(f.value): filter_val
                        }
                    }
                })

            # Add filters to the structuredQuery
            structuredQuery["where"] = {
                "compositeFilter": {
                    "op": "AND",
                    "filters": constructed_filters
                }
            }

        # Format order by
        if order_by:
            order_condition = self._construct_orderby_condition(order_by)
            structuredQuery["orderBy"] = [
                {
                    "field": {
                        "fieldPath": order_condition.column_name
                    },
                    "direction": order_condition.operator
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
            data=json.dumps({
                "structuredQuery": structuredQuery
            })
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
                    f"{table}_id": document["document"]["name"].split("/")[-1],  # Get last item in the uri
                    **self._jsonify_firestore_response(document["document"]["fields"])
                } for document in response
            ]
        except KeyError:
            return []

    def select_rows_as_list(
        self,
        table: str,
        filters: Optional[List[Union[WhereCondition, List, Tuple]]] = None,
        order_by: Optional[Union[List, OrderCondition, str, Tuple]] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> List[Dict]:
        # With credentials
        if self._credentials_path:
            return self._select_rows_as_list_with_creds(table=table, filters=filters, order_by=order_by, limit=limit)

        return self._select_rows_as_list_no_creds(table=table, filters=filters, order_by=order_by, limit=limit)

    def _select_rows_with_max_results_expectation(
        self,
        table: str,
        pks: List[Union[WhereCondition, List, Tuple]],
        expected_max_rows: int
    ):
        # Find matching
        pks = [self._construct_where_condition(pk) for pk in pks]
        matching = self.select_rows_as_list(table=table, filters=pks)

        # Handle expectation
        if len(matching) > expected_max_rows:
            raise exceptions.UniquenessError(table, [pk.column_name for pk in pks], matching)
        elif len(matching) == 0:
            return None
        else:
            return matching

    def _get_or_upload_row(self, table: str, pks: List[Union[WhereCondition, List, Tuple]], values: Dict) -> Dict:
        # Reject any upload without credentials
        if self._credentials_path is None:
            raise exceptions.MissingCredentialsError()

        # Fast return for already stored
        found = self._select_rows_with_max_results_expectation(
            table=table,
            pks=pks,
            expected_max_rows=1
        )
        # Return or upload
        if found:
            return found[0]
        else:
            # Create id
            id = str(uuid4())
            # Store the row
            self._root.collection(table).document(id).set(values)
            log.debug(
                f"Uploaded values: {values} "
                f"To id: {id} "
                f"On table: {table}"
            )

            # Return row
            return {f"{table}_id": id, **values}

    def get_or_upload_body(self, name: str, description: Optional[str] = None) -> Dict:
        return self._get_or_upload_row(
            table="body",
            pks=[("name", name)],
            values={
                "name": name,
                "description": description,
                "created": datetime.utcnow()
            }
        )

    def get_or_upload_minutes_item(
        self,
        name: str,
        matter: Optional[str],
        legistar_event_item_id: Optional[int] = None
    ) -> Dict:
        return self._get_or_upload_row(
            table="minutes_item",
            pks=[("name", name)],
            values={
                "name": name,
                "matter": matter,
                "legistar_event_item_id": legistar_event_item_id,
                "created": datetime.utcnow()
            }
        )

    def get_or_upload_minutes_item_file(
        self,
        minutes_item_id: str,
        uri: str,
        name: Optional[str] = None,
        legistar_matter_attachment_id: Optional[int] = None
    ) -> Dict:
        return self._get_or_upload_row(
            table="minutes_item_file",
            pks=[("minutes_item_id", minutes_item_id), ("uri", uri)],
            values={
                "minutes_item_id": minutes_item_id,
                "name": name,
                "uri": uri,
                "legistar_matter_attachment_id": legistar_matter_attachment_id,
                "created": datetime.utcnow()
            }
        )

    def get_event(self, video_uri: str) -> Dict:
        # Try find
        found = self._select_rows_with_max_results_expectation(
            table="event",
            pks=[("video_uri", video_uri)],
            expected_max_rows=1
        )
        if found:
            return found[0]

        return None

    def get_or_upload_event(
        self,
        body_id: str,
        event_datetime: datetime,
        source_uri: str,
        video_uri: str,
        agenda_file_uri: Optional[str] = None,
        minutes_file_uri: Optional[str] = None,
        legistar_event_id: Optional[int] = None,
        legistar_event_link: Optional[int] = None
    ) -> Dict:
        return self._get_or_upload_row(
            table="event",
            pks=[("video_uri", video_uri)],
            values={
                "body_id": body_id,
                "event_datetime": event_datetime,
                "source_uri": source_uri,
                "video_uri": video_uri,
                "agenda_file_uri": agenda_file_uri,
                "minutes_file_uri": minutes_file_uri,
                "legistar_event_id": legistar_event_id,
                "legistar_event_link": legistar_event_link,
                "created": datetime.utcnow()
            }
        )

    def get_or_upload_event_minutes_item(
        self,
        event_id: str,
        minutes_item_id: str,
        index: int,
        decision: Optional[str] = None
    ) -> Dict:
        return self._get_or_upload_row(
            table="event_minutes_item",
            pks=[("event_id", event_id), ("minutes_item_id", minutes_item_id)],
            values={
                "event_id": event_id,
                "minutes_item_id": minutes_item_id,
                "index": index,
                "decision": decision,
                "created": datetime.utcnow()
            }
        )

    def get_or_upload_person(
        self,
        full_name: str,
        email: str,
        phone: Optional[str] = None,
        website: Optional[str] = None,
        legistar_person_id: Optional[int] = None
    ) -> Dict:
        return self._get_or_upload_row(
            table="person",
            pks=[("full_name", full_name), ("email", email)],
            values={
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "website": website,
                "legistar_person_id": legistar_person_id,
                "created": datetime.utcnow()
            }
        )

    def get_or_upload_vote(
        self,
        person_id: str,
        event_minutes_item_id: str,
        decision: str,
        legistar_event_item_vote_id: Optional[int] = None
    ) -> Dict:
        return self._get_or_upload_row(
            table="vote",
            pks=[("person_id", person_id), ("event_minutes_item_id", event_minutes_item_id)],
            values={
                "person_id": person_id,
                "event_minutes_item_id": event_minutes_item_id,
                "decision": decision,
                "legistar_event_item_vote_id": legistar_event_item_vote_id,
                "created": datetime.utcnow()
            }
        )

    def get_or_upload_file(
        self,
        uri: str,
        filename: Optional[str] = None,
        description: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> Dict:
        if filename is None:
            filename = uri.split("/")[-1]

        return self._get_or_upload_row(
            table="file",
            pks=[("uri", uri)],
            values={
                "uri": uri,
                "filename": filename,
                "description": description,
                "content_type": content_type,
                "created": datetime.utcnow()
            }
        )

    def get_or_upload_transcript(
        self,
        event_id: str,
        file_id: str,
        confidence: Optional[float] = None
    ) -> Dict:
        return self._get_or_upload_row(
            table="transcript",
            pks=[("event_id", event_id), ("file_id", file_id)],
            values={
                "event_id": event_id,
                "file_id": file_id,
                "confidence": confidence,
                "created": datetime.utcnow()
            }
        )

    def get_or_upload_algorithm(
        self,
        name: str,
        version: str,
        description: Optional[str] = None,
        source: Optional[str] = None
    ) -> Dict:
        return self._get_or_upload_row(
            table="algorithm",
            pks=[("name", name), ("version", version)],
            values={
                "name": name,
                "version": version,
                "description": description,
                "source": source,
                "created": datetime.utcnow()
            }
        )

    def get_or_upload_run(self, algorithm_id: str, begin: datetime, completed: datetime) -> Dict:
        return self._get_or_upload_row(
            table="run",
            pks=[("algorithm_id", algorithm_id), ("begin", begin), ("completed", completed)],
            values={
                "algorithm_id": algorithm_id,
                "begin": begin,
                "completed": completed,
                "created": datetime.utcnow()
            }
        )

    def get_or_upload_run_input(self, run_id: str, dtype: str, value: Any) -> Dict:
        return self._get_or_upload_row(
            table="run_input",
            pks=[("run_id", run_id), ("dtype", dtype), ("value", value)],
            values={
                "run_id": run_id,
                "dtype": dtype,
                "value": value,
                "created": datetime.utcnow()
            }
        )

    def get_or_upload_run_input_file(self, run_id: str, file_id: str) -> Dict:
        return self._get_or_upload_row(
            table="run_input_file",
            pks=[("run_id", run_id), ("file_id", file_id)],
            values={
                "run_id": run_id,
                "file_id": file_id,
                "created": datetime.utcnow()
            }
        )

    def get_or_upload_run_output(self, run_id: str, dtype: str, value: Any) -> Dict:
        return self._get_or_upload_row(
            table="run_output",
            pks=[("run_id", run_id), ("dtype", dtype), ("value", value)],
            values={
                "run_id": run_id,
                "dtype": dtype,
                "value": value,
                "created": datetime.utcnow()
            }
        )

    def get_or_upload_run_output_file(self, run_id: str, file_id: str) -> Dict:
        return self._get_or_upload_row(
            table="run_output_file",
            pks=[("run_id", run_id), ("file_id", file_id)],
            values={
                "run_id": run_id,
                "file_id": file_id,
                "created": datetime.utcnow()
            }
        )

    def get_indexed_event_term(self, term: str, event_id: str) -> Dict:
        # Try find
        found = self._select_rows_with_max_results_expectation(
            table="indexed_event_term",
            pks=[("term", term), ("event_id", event_id)],
            expected_max_rows=1
        )
        if found:
            return found[0]

        return None

    def upload_or_update_indexed_event_term(self, term: str, event_id: str, value: float) -> Dict:
        # Reject any upload without credentials
        if self._credentials_path is None:
            raise exceptions.MissingCredentialsError()

        # Check if index term already exists
        found = self.get_indexed_event_term(term, event_id)

        # If found, use the already stored id
        if found:
            id = found["indexed_event_term_id"]
        # Else, create a new id
        else:
            id = str(uuid4())

        # Create values dictionary
        values = {
            "term": term,
            "event_id": event_id,
            "value": value,
            "updated": datetime.utcnow()
        }

        # Store the row
        self._root.collection("indexed_event_term").document(id).set(values)

        # Return the newly created row
        return {f"indexed_event_term_id": id, **values}

    def _search_for_term(self, term: str, table: str) -> List[Dict[str, Union[str, float, datetime]]]:
        """
        Helper function for multithreaded query of terms.
        """
        return self.select_rows_as_list(table, filters=[("term", term)])

    def _search(self, query: str, table: str, match_on: str, data_table: str) -> List[Match]:
        # Clean and tokenize the query
        query = Indexer.clean_text_for_indexing(query)
        query_terms = set(query.split(" "))

        # First query for the terms
        search_for_term_from_table = partial(self._search_for_term, table=table)
        with ThreadPoolExecutor() as exe:
            term_results = list(exe.map(search_for_term_from_table, query_terms))

        # Combine the term results into table results
        table_results = {}
        for term_result in term_results:
            # Join the results into a main results dictionary where they top level key is the table row id
            for term_details in term_result:
                if term_details[match_on] in table_results:
                    table_results[term_details[match_on]].append(term_details)
                else:
                    table_results[term_details[match_on]] = [term_details]

        # Clean and format the results
        table_matches = []
        for unique_id, term_results in table_results.items():
            table_matches.append(Match(
                unique_id=unique_id,
                terms=[
                    TermResult(term=t["term"], contribution=t["value"]) for t in term_results
                ],
                data=self.select_row_by_id(table=data_table, id=unique_id)
            ))

        # Sort by relevance
        table_matches = sorted(table_matches, key=lambda m: m.relevance, reverse=True)

        return table_matches

    def search_events(self, query: str) -> List[Match]:
        return self._search(query, table="indexed_event_term", match_on="event_id", data_table="event")

    def get_indexed_minutes_item_term(self, term: str, minutes_item_id: str) -> Dict:
        # Try find
        found = self._select_rows_with_max_results_expectation(
            table="indexed_minutes_item_term",
            pks=[("term", term), ("minutes_item_id", minutes_item_id)],
            expected_max_rows=1
        )
        if found:
            return found[0]

        return None

    def upload_or_update_indexed_minutes_item_term(self, term: str, minutes_item_id: str, value: float) -> Dict:
        # Reject any upload without credentials
        if self._credentials_path is None:
            raise exceptions.MissingCredentialsError()

        # Check if index term already exists
        found = self.get_indexed_minutes_item_term(term, minutes_item_id)

        # If found, use the already stored id
        if found:
            id = found["indexed_minutes_item_term_id"]
        # Else, create a new id
        else:
            id = str(uuid4())

        # Create values dictionary
        values = {
            "term": term,
            "minutes_item_id": minutes_item_id,
            "value": value,
            "updated": datetime.utcnow()
        }

        # Store the row
        self._root.collection("indexed_minutes_item_term").document(id).set(values)

        # Return the newly created row
        return {f"indexed_minutes_item_term_id": id, **values}

    def search_minutes_items(self, query: str) -> List[Match]:
        return self._search(
            query,
            table="indexed_minutes_item_term",
            match_on="minutes_item_id",
            data_table="minutes_item"
        )

    def __str__(self):
        if self._credentials_path:
            return f"<CloudFirestoreDatabase [{self._credentials_path}]>"

        return f"<CloudFirestoreDatabase [{self._project_id}]>"

    def __repr__(self):
        return str(self)
