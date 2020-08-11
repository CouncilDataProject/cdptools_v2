#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, Union

import pandas as pd

from . import exceptions

###############################################################################


class CDPCollections(Enum):
    EVENT = "event"
    PERSON = "person"
    BODY = "body"
    FILE = "file"
    TRANSCRIPT = "transcript"
    SEAT = "seat"
    ROLE = "role"
    MINUTES_ITEM = "minutes_item"
    EVENT_MINUTES_ITEM = "event_minutes_item"
    VOTE = "vote"
    MATTER = "matter"
    MATTER_TYPE = "matter_type"


class WhereCondition(NamedTuple):
    column_name: str
    operator: str
    value: Union[bool, datetime, float, int, str]


class OrderCondition(NamedTuple):
    column_name: str
    operator: str


class WhereOperators:
    eq: str = "=="
    contains: str = "in"
    gt: str = ">"
    lt: str = "<"
    gteq: str = ">="
    lteq: str = "<="


class OrderOperators:
    desc: str = "DESCENDING"
    asce: str = "ASCENDING"


class TermResult(NamedTuple):
    term: str
    contribution: float


class Match:
    def __init__(self, unique_id, terms: List[TermResult], data: Dict[str, Any]):
        self._unique_id = unique_id
        self._terms = terms
        self._data = data

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def data(self):
        return self._data

    @property
    def terms(self):
        return self._terms

    @property
    def relevance(self):
        return sum(t.contribution for t in self.terms)

    def __str__(self):
        return f"<Match [unique_id: {self.unique_id}, relevance: {self.relevance}]>"

    def __repr__(self):
        return str(self)


###############################################################################


class DocumentStoreDatabase(ABC):
    @staticmethod
    def _construct_where_condition(filt: Union[WhereCondition, List, Tuple]):
        """
        Construct a where condition from the passed filter object.

        For available where condition operators, please view the WhereOperators class 
        attributes.

        Parameters
        ----------
        filt: Union[WhereCondition, List, Tuple]
            The filter to construct a WhereCondition for.

        Returns
        -------
        filt: WhereCondition
            If provided an already constructed WhereCondition, simply returns the 
            provided object.
            If provided a List or Tuple of length two, constructs a WhereCondition 
            with an equal operator.
            If provided a List or Tuple of length three, constructs a WhereCondition 
            with the contents of the provided.
            Provided List or Tuple objects should follow the format:
                {target_to_filter}, {operator}, {target_value}
            Unless provided a List or Tuple of length two, in which case, should 
            follow the format:
                {target_to_filter}, {target_value}

        Examples
        --------
        >>> condition = Database._construct_where_condition(WhereCondition(
        ...    column_name="event_id",
        ...    operator=">=",
        ...    value="abcd"
        ... ))
        WhereCondition("event_id", ">=", "abcd")


        # Returns the same WhereCondition that was passed in


        >>> condition = Database._construct_where_condition(["event_id", 
        ...                                                 WhereOperators.gteq, 
        ...                                                 value="abcd"])
        WhereCondition("event_id", ">=", "abcd")


        # Returns the same WhereCondition as above


        >>> condition = Database._construct_where_condition(("event_id", "abcd"))
        WhereCondition("event_id", "==", "abcd")

        # Returns a WhereCondition similar to above but the operator is set to equal 
        rather than greater than or equal.

        """
        if isinstance(filt, WhereCondition):
            return filt
        elif isinstance(filt, (list, tuple)):
            # Assume equal
            if len(filt) == 2:
                return WhereCondition(filt[0], WhereOperators.eq, filt[1])
            elif len(filt) == 3:
                return WhereCondition(*filt)
            else:
                raise exceptions.UnstructuredWhereConditionError(filt)
        else:
            raise exceptions.UnknownTypeWhereConditionError(filt)

    @staticmethod
    def _construct_orderby_condition(by: Union[OrderCondition, List, Tuple, str]):
        """
        Construct an orderby condition from the passed by object.

        For available order condition operators, please view the OrderOperators class 
        attributes.

        Parameters
        ----------
        by: Union[OrderCondition, List, Tuple, str]
            The order by data to construct an OrderCondition for.

        Returns
        -------
        by: OrderCondition
            If provided an already constructed OrderCondition, simply 
            returns the provided object.
            If provided a string, returns and OrderCondition with the provided 
            string being used as the column name and defaults to descending as the 
            operator.
            If provided a List or Tuple of length two, constructs an OrderCondition 
            with the provided data.
            Provided List or Tuple objects should follow the format:
                {target_to_order}, {operator}

        Examples
        --------
        >>> condition = Database._construct_orderby_condition(OrderCondition(
        ...     column_name="event_id",
        ...     operator="DESCENDING",
        ... ))
        OrderCondition("event_id", "DESCENDING")


        # Returns the same OrderCondition that was passed in


        >>> condition = Database._construct_orderby_condition("event_id")
        OrderCondition("event_id", "DESCENDING")


        # Returns the same OrderCondition as above


        >>> condition = Database._construct_orderby_condition(["event_id", 
        ...                                                   OrderOperators.desc])
        OrderCondition("event_id", "DESCENDING")


        # Returns the same OrderCondition as above


        >>> condition = Database._construct_where_condition(("event_id", "ASCENDING")
        OrderCondition("event_id", "ASCENDING")


        # Returns an OrderCondition similar to above but the operator is set to 
        ascending rather than descending.

        """
        if isinstance(by, OrderCondition):
            return by
        if isinstance(by, str):
            # Assume descending
            return OrderCondition(by, OrderOperators.desc)
        elif isinstance(by, (list, tuple)):
            # Assume descending
            if len(by) == 1:
                return OrderCondition(by[0], OrderOperators.desc)
            elif len(by) == 2:
                return OrderCondition(*by)
            else:
                raise exceptions.UnstructuredOrderConditionError(by)
        else:
            raise exceptions.UnknownTypeOrderConditionError(by)

    @abstractmethod
    def select_document_by_id(
        self, collection: str, id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get document from a collection by looking up the value by id.

        Parameters
        ----------
        collection: str
            The name of the collection to retrieve data by id from.
        id: str
            The id of the data to retrieve data for.

        Returns
        -------
        If the document was found, the data from that document is returned as a 
        dictionary. 
        If not found, None is returned.
        """
        return {}

    @abstractmethod
    def select_documents_as_list(
        self,
        collection: str,
        filters: Optional[List[Union[WhereCondition, List, Tuple]]] = None,
        order_by: Optional[Union[OrderCondition, List, Tuple, str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get a list of documents from a collection optionally using 
        filters (a list of where conditions), ordering, and limit.

        Parameters
        ----------
        collection: str
            The name of the collection to retrieve data from.
        filters: Optional[List[Union[WhereCondition, List, Tuple]]]
            A list of filters (where conditions) to add filter down the query.
        order_by: Optional[Union[OrderCondition, List, Tuple, str]]
            An order by condition to order the results by before returning.
        limit: Optional[int]
            An integer limit to how many documents should be returned that match the 
            query provided.
            Commonly, running queries without credentials will have a default limit 
            value.

        Returns
        -------
        results: List[Dict[str, Any]]
            The results of the query returned as a List of Dictionaries, where each 
            dictionary is a unique document from the collection queried. 
            If no documents are found, returns an empty list.
        """
        return []

    @staticmethod
    def _reshape_list_of_documents_to_dict(
        documents: List[Dict[str, Any]], collection: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Reshape a list of documents to a dictionary of documents.

        Parameters
        ----------
        documents: List[Dict[str, Any]]
            The documents returned from a `select_documents_as_list call`.
        collection: str
            The name of the collection to retrieve data from.

        Returns
        -------
        formatted: Dict[str, Dict[str, Any]]
            The documents returned as a dictionary mapping unique id to a dictionary 
            of that documents data from the collection queried. If no documents are 
            provided, returns an empty dictionary.
        """
        # Format
        formatted = {}
        for document in documents:
            unique_id = document[f"{collection}_id"]
            formatted[unique_id] = document

        return formatted

    @staticmethod
    def _reshape_list_of_documents_to_dataframe(
        documents: List[Dict[str, Any]], collection: Optional[str] = None
    ):
        """
        Simply cast a list of documents to a dataframe.

        Parameters
        ----------
        documents: List[Dict[str, Any]]
            The documents returned from a `select_documents_as_list_call`.
        collection: Optional[str]
            If provided, the unique id for each document will be used as the index 
            value.

        Returns
        -------
        formatted: pandas.DataFrame
            The documents returned as a pandas DataFrame object. If collection was 
            provided the index of the dataframe will be the unique id's 
            for that collection.
        """
        # Cast to dataframe
        formatted = pd.DataFrame(documents)

        # Optionally set the index based on the collection name
        if collection:
            formatted = formatted.set_index(f"{collection}_id")

        return formatted

    @abstractmethod
    def get_or_upload_body(
        self,
        name: str,
        tag: str,
        description: Optional[str],
        start_date: datetime,
        end_date: Optional[datetime],
        is_active: bool,
        chair_person_id: str,
        external_source_id: Optional[Any],
    ) -> Dict[str, Any]:
        """
        Get or upload a body.

        Parameters
        ----------
        name: str
            The name of the body (council, subcommittee, etc).
        tag: str
            The tag of the body.
        description: Optional[str]:
            An optional description of the body.
        start_date: datetime
            A datetime representing the chronological start date of a body.
        end_date: Optional[datetime]
            A datetime representing the end date (if not active) of a body.
        is_active: bool
            A bool describing whether a body is active or not.
        chair_person_id: str
            The id of the body chair's person document.
        external_source_id: Optional[Any]
            An id in the external source this data comes from.

        Returns
        -------
        details: Dict[str, Any]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_minutes_item(
        self,
        name: str,
        description: Optional[str],
        matter: Dict[str, str],
        external_source_id: Optional[Any],
    ) -> Dict[str, Any]:
        """
        Get or upload a minutes item. In Legistar this is commonly referred to 
        as an event item.

        Parameters
        ---------
        name: str
            A name for the minutes item. Ex: "Appointment of Rene J. Peters, Jr."
        description: Optional[str]
            An optional description of the minutes_item.
        matter: Optional[str]
            A dictionary that contains information of the matter for the minutes item.
        external_source_id: Optional[Any]
            An id in the external source this data comes from.

        Returns
        -------
        details: Dict[str, Any]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_event(
        self,
        body: Dict[str, str],
        event_datetime: datetime,
        thumbnail_static_file: Dict[str, str],
        thumbnail_hover_file: Dict[str, str],
        video_uri: Optional[str],
        keywords: List[Dict[str, str]],
        keyword_ids: List[str],
        matters: List[Dict[str, str]],
        matter_ids: List[str],
        minutes_items: List[Dict[str, str]],
        minutes_item_ids: List[str],
        people: List[Dict[str, str]],
        person_ids: List[str],
        external_source_id: Optional[str],
        agenda_uri: str,
        minutes_uri: Optional[str],
    ) -> Dict[str, Any]:
        """
        Find an event using the primary key for events, a video uri.

        Parameters
        ----------
        video_uri: str
            A uri that can be used to access the video file used to generate all 
            downstream data for an event.
        body: Dict[str, str]
            A dictionary that contains the event's body information.
        event_datetime: datetime
            Date of the event.
        thumbnail_static_file: Dict[str, str]
            A dictionary containing thumbnail static file information.
        thumbnail_hover_file: Dict[str, str]
            A dictionary containing thumbnail hover file information.
        video_uri: Optional[str]
            An optional video uri for the event.
        keywords: Dict[str, str]
            A dictionary containing information on the event's keywords.
        keyword_ids: List[str]
            A list containing the keyword ids.
        matters: Dict[str, str]
            A dictionary containing information on the event's matters.
        matter_ids: List[str]
            A list containing the matter ids.
        minutes_items: Dict[str, str]
            A dictionary containing information on the event's minutes_items.
        minutes_item_ids: List[str]
            A list containing the minutes_item ids.
        people: Dict[str, str]
            A dictionary containing information on the event's involved people.
        person: List[str]
            A list containing the person ids.
        external_source_id: Optional[str]
            An id in the external source this data comes from.
        agenda_uri: str
            The agenda uri for the event.
        minutes_uri: Optional[str]
            An optional uri for the event's minutes.

        Returns
        -------
        details: Dict[str, Any]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_person(
        self,
        router_id: Optional[str],
        name: str,
        email: Optional[str],
        phone: Optional[str],
        website: Optional[str],
        picture_file: Dict[str, str],
        is_active: bool,
        is_council_president: bool,
        most_recent_seat: Dict[str, str],
        most_recent_chair_body: Dict[str, str],
        terms_serving_in_current_seat_role: int,
        terms_serving_in_current_committee_chair_role: int,
        external_source_id: Optional[Any],
    ) -> Dict[str, Any]:
        """
        Get or upload a city council member (person).

        Parameters
        ----------
        router_id: Optional[str]
            An optional router id.
        name: str
            The name of the person.
        email: Optional[str]
            An optional email.
        phone: Optional[str]
            An optional phone number.
        website: Optional[str]
            An optional website.
        picture_file: Dict[str, str]
            A dictionary containing picture file information.
        is_active: bool
            A boolean indicating whether this person is active.
        is_council_president: bool
            A boolean indicating whether this person is council president.
        most_recent_seat: Dict[str,str]
            A dictionary containing information on this person's most recent seat.
        most_recent_chair_body: Dict[str,str]
            A dictionary containing information on this person's most recent body they 
            were chair of.
        terms_serving_in_current_seat_role: int
            An int for how many terms this person has served in their current seat role.
        terms_serving_in_current_committee_chair_role: int
            An int for how many terms this person has served in their current 
            committee chair role.
        external_source_id: Optional[Any]
            An id in the external source this data comes from.

        Returns
        -------
        details: Dict[str, Any]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_vote(
        self,
        matter: Dict[str, str],
        event: Dict[str, Any],
        event_minutes_item: Dict[str, str],
        person: Dict[str, str],
        vote_decision: str,
        is_majority: bool,
        external_vote_item_id: Optional[any],
    ) -> Dict[str, Any]:
        """
        Get or upload a person's vote on a minutes item.

        Parameters
        ----------
        matter: Dict[str, str]
            Information on this vote's matter.
        event: Dict[str, Any]
            Information on this vote's event.
        event_minutes_item: Dict[str, str]
            Information on this vote's event minutes item.
        person: Dict[str, str]
            Information on who casted this vote.
        vote_decision: str
            The decision of this vote.
        is_majority: bool
            Whether this vote was a majority vote or not.
        external_vote_item_id: Optional[any]
            An optional id for an external vote item.

        Returns
        -------
        details: Dict[str, Any]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_file(
        self,
        uri: str,
        filename: Optional[str] = None,
        description: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Dict:
        """
        Get or upload a file (to the database collection, not a file store).

        Parameters
        ----------
        uri: str
            A uri to the file.
        filename: Optional[str]
            An optional filename to store with the file.
        description: Optional[str]
            An optional description for the file.
        content_type: Optional[str]
            An optional content type for the file.
            Preferred to use MIME types: 
            https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types

        Returns
        -------
        details: Dict[str, Union[str, Optional[int]]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_seat(
        self,
        electoral_area: str,
        electoral_type: str,
        map_file_id: str,
        map_uri: str,
        created: datetime,
    ) -> Dict[str, Any]:
        """
        Get or upload a seat (to the database, a file store).

        Parameters
        ----------
        electoral_area: str
            The electoral area of the seat.
        electoral_type: str
            The electoral type of the seat.
        map_file_id: str
            The map file id.
        map_uri: str
            The map uri.

        Returns
        -------
        details: Dict[str, Union[str, Optional[float]]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_transcript(
        self, event_id: str, file_id: str, confidence: Optional[float] = None
    ) -> Dict:
        """
        Get or upload a transcript (to the database, a file store).

        Parameters
        ----------
        event_id: str
            The id for the event that this transcript is for.
        file_id: str
            The id for the file that contains the transcript data.
        confidence: Optional[float]
            If available, a float / double value to store with the transcript 
            for the confidence of the transcription.

        Returns
        -------
        details: Dict[str, Union[str, Optional[float]]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_role(
        self,
        person: Dict[str, str],
        title: str,
        body: Dict[str, str],
        start_date: datetime,
        end_date: Optional[datetime],
        seat_id: str,
        external_source_id: Optional[any],
        created: datetime,
    ) -> Dict[str, Any]:
        """
        Get or upload a role (to the database, a file store).

        Parameters
        ----------
        person: Dict[str, str]
            Person that holds this role.
        title: str
            Title of this role.
        body: Dict[str, str]
            Information about the body this role is for.
        start_date: datetime
            Start time of the role.
        end_date: Optional[datetime]
            End time of the role if it has ended.
        seat_id: str
            Seat id of the role.
        external_source_id: Optional[any]
            An id in the external source this data comes from.

        Returns
        -------
        details: Dict[str, Any]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_event_minutes_item(
        self,
        event_id: str,
        minutes_item: Dict[str, str],
        index: int,
        decision: Optional[str],
        matter: Dict[str, str],
        votes: List[Dict[str, str]],
        vote_ids: List[str],
        files: List[Dict[str, str]],
        file_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Get or upload a event minute item (to the database, a file store).

        Parameters
        ----------
        event_id: str
            Id of the event this was for.
        minutes_item: Dict[str, str]
            Information for the corresponding minutes item.
        index: int
            Order of the event_minutes_item id within the event.
        decision: Optional[str]
            The decision of this event minutes item if there was one.
        matter: Dict[str, str]
            Information on the matter of this event_minutes_item.
        votes: List[Dict[str, str]]
            Information on the votes of this event_minutes_item.
        vote_ids: List[str]
            A list of vote ids.
        files: List[Dict[str, str]]
            Information on the files of this event_minutes_item.
        file_ids: List[str]
            A list of file ids.

        Returns
        -------
        details: Dict[str, Any]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
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
        external_source_id: Optional[Any],
        updated: datetime,
        created: datetime,
    ) -> Dict[str, Any]:
        """
        Get or upload a matter (to the database, a file store).

        Parameters
        ----------
        name: str
            Name of the matter.
        matter_type: Dict[str, str]
            Information on the matter type.
        title: str
            Title of the matter.
        status: str
            Status of the matter.
        most_recent_event: Dict[str, Any]
            Information on the most recent event regarding this matter.
        next_event: Dict[str, Any]
            Information on the next event regarding this matter.
        keywords: List[Dict[str, str]]
            Information on the keywords of this matter.
        keyword_ids: List[str]
            A list of keyword ids.
        external_source_id: Optional[Any]
            An id in the external source this data comes from.

        Returns
        -------
        details: Dict[str, Any]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_matter_type(
        self, name: str, external_source_id: Optional[Any], created: datetime
    ) -> Dict[str, Any]:
        """
        Get or upload a matter (to the database, a file store).

        Parameters
        ----------
        name: str
            Name of the matter type.
        external_source_id: Optional[Any]
            An id in the external source this data comes from.

        Returns
        -------
        details: Dict[str, Any]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def drop_collection(self, collection: str):
        """
        Wipe the input collection.

        Parameters
        ----------
        collection: str
            A string collectionname in the database to be deleted.

        Returns
        -------
        None
        """
        return

    @property
    @abstractmethod
    def collections(self) -> List[str]:
        """
        A generic database collections property.

        Returns
        -------
        _collections: List[str]
            A list of collection names.
        """
        return []
