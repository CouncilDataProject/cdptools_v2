#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, Union

from . import exceptions

###############################################################################


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


class Database(ABC):

    @staticmethod
    def _construct_where_condition(filt: Union[WhereCondition, List, Tuple]):
        """
        Construct a where condition from the passed filter object.

        For available where condition operators, please view the WhereOperators class attributes.

        Parameters
        ----------
        filt: Union[WhereCondition, List, Tuple]
            The filter to construct a WhereCondition for.

        Returns
        -------
        filt: WhereCondition
            If provided an already constructed WhereCondition, simply returns the provided object.
            If provided a List or Tuple of length two, constructs a WhereCondition with an equal operator.
            If provided a List or Tuple of length three, constructs a WhereCondition with the contents of the provided.
            Provided List or Tuple objects should follow the format:
                {target_to_filter}, {operator}, {target_value}
            Unless provided a List or Tuple of length two, in which case, should follow the format:
                {target_to_filter}, {target_value}

        Examples
        --------
        ```
        condition = Database._construct_where_condition(WhereCondition(
            column_name="event_id",
            operator=">=",
            value="abcd"
        ))
        # Returns the same WhereCondition that was passed in

        condition = Database._construct_where_condition(["event_id", WhereOperators.gteq, value="abcd"])
        # Returns the same WhereCondition as above

        condition = Database._construct_where_condition(("event_id", "abcd"))
        # Returns a WhereCondition similar to above but the operator is set to equal rather than greater than or equal.
        ```
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

        For available order condition operators, please view the OrderOperators class attributes.

        Parameters
        ----------
        by: Union[OrderCondition, List, Tuple, str]
            The order by data to construct an OrderCondition for.

        Returns
        -------
        by: OrderCondition
            If provided an already constructed OrderCondition, simply returns the provided object.
            If provided a string, returns and OrderCondition with the provided string being used as the column name
                and defaults to descending as the operator.
            If provided a List or Tuple of length two, constructs an OrderCondition with the provided data.
            Provided List or Tuple objects should follow the format:
                {target_to_order}, {operator}

        Examples
        --------
        ```
        condition = Database._construct_orderby_condition(OrderCondition(
            column_name="event_id",
            operator="DESCENDING",
        ))
        # Returns the same OrderCondition that was passed in

        condition = Database._construct_orderby_condition("event_id")
        # Returns the same OrderCondition as above

        condition = Database._construct_orderby_condition(["event_id", OrderOperators.desc])
        # Returns the same OrderCondition as above

        condition = Database._construct_where_condition(("event_id", "ASCENDING")
        # Returns an OrderCondition similar to above but the operator is set to ascending rather than descending.
        ```
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
    def select_row_by_id(self, table: str, id: str) -> Optional[Dict[str, Any]]:
        """
        Get row from a table by looking up the value by id.

        Parameters
        ----------
        table: str
            The name of the table to retrieve data by id from.
        id: str
            The id of the data to retrieve data for.

        Returns
        -------
        If the row was found, the data from that row is returned as a dictionary. If not found, None is returned.
        """
        return {}

    @abstractmethod
    def select_rows_as_list(
        self,
        table: str,
        filters: Optional[List[Union[WhereCondition, List, Tuple]]] = None,
        order_by: Optional[Union[OrderCondition, List, Tuple, str]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get a list of rows from a table optionally using filters (a list of where conditions), ordering, and limit.

        Parameters
        ----------
        table: str
            The name of the table to retrieve data from.
        filters: Optional[List[Union[WhereCondition, List, Tuple]]]
            A list of filters (where conditions) to add filter down the query.
        order_by: Optional[Union[OrderCondition, List, Tuple, str]]
            An order by condition to order the results by before returning.
        limit: Optional[int]
            An integer limit to how many rows should be returned that match the query provided.
            Commonly, running queries without credentials will have a default limit value.

        Returns
        -------
        results: List[Dict[str, Any]]
            The results of the query returned as a List of Dictionaries, where each dictionary is a unique row from the
            table queried. If no rows are found, returns an empty list.
        """
        return []

    @abstractmethod
    def get_or_upload_body(self, name: str, description: Optional[str]) -> Dict[str, str]:
        """
        Get or upload a body.

        Parameters
        ----------
        name: str
            The name of the body (council, subcommittee, etc).
        description: Optional[str]:
            An optional description of the body.

        Returns
        -------
        details: Dict[str, str]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_minutes_item(
        self,
        name: str,
        matter: Optional[str],
        legistar_event_item_id: Optional[int] = None
    ) -> Dict:
        """
        Get or upload a minutes item. In Legistar this is commonly referred to as an event item.

        Parameters
        ---------
        name: str
            A name for the minutes item. Ex: "Appointment of Rene J. Peters, Jr."
        matter: str
            A matter name for the minutes item. Ex: "Appt 01373"
        legistar_event_item_id: Optional[int]
            If the CDP instance is deployed for a city with Legistar, it is recommended to also store the `EventItemId`.

        Returns
        -------
        details: Dict[str, Union[str, Optional[int]]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_minutes_item_file(
        self,
        minutes_item_id: str,
        uri: str,
        name: Optional[str] = None,
        legistar_matter_attachment_id: Optional[int] = None
    ) -> Dict:
        """
        Get or upload a minutes item file. Commonly, minutes items have an associated file such as a presentation.

        Parameters
        ----------
        minutes_item_id: str
            A minutes item id this file is associated with.
        uri: str
            A uri that can be used to access this file.
        name: Optional[str]
            A name for the file.
        legistar_matter_attachment_id: Optional[int]
            If the CDP instance is deployed for a city with Legistar, it is recommended to also store the
            `MatterAttachmentId`.

        Returns
        -------
        details: Dict[str, Union[str, Optional[int]]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_event(self, video_uri: str) -> Dict:
        """
        Find an event using the primary key for events, a video uri.

        Parameters
        ----------
        video_uri: str
            A uri that can be used to access the video file used to generate all downstream data for an event.

        Returns
        -------
        details: Dict[str, Union[str, Optional[int]]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_event(
        self,
        body_id: str,
        event_datetime: datetime,
        source_uri: str,
        video_uri: str,
        agenda_file_uri: Optional[str] = None,
        minutes_file_uri: Optional[str] = None,
        legistar_event_id: Optional[int] = None,
        legistar_event_link: Optional[str] = None
    ) -> Dict:
        """
        Get or upload an event.

        Parameters
        ----------
        body_id: str
            The id for the body this event occured in.
        event_datetime: datetime
            The datetime this event occured at.
        source_uri: str
            The primary uri for where this event info or video was retrieved from.
        video_uri: str
            A uri that can be used to access the video file used to generate all downstream data for an event.
        agenda_file_uri: Optional[str]
            If an agenda file is available for the event, it is recommended to store a uri to the file.
        minutes_file_uri: Optional[str]
            If a minutes file is available for the event, it is recommened to store a uri to the file.
        legistar_event_id: Optional[int]
            If the CDP instance is deployed for a city with Legistar, it is recommended to also store the `EventId`.
        legistar_event_link: Optional[str]
            If the CDP instance is deployed for a city with Legistar, it is recommended to also store a link to the
            event details for this event but in Legistar's system.

        Returns
        -------
        details: Dict[str, Union[str, datetime, Optional[int]]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_event_minutes_item(
        self,
        event_id: str,
        minutes_item_id: str,
        index: int,
        decision: Optional[str] = None
    ) -> Dict:
        """
        Get or upload the join of an event and a minutes item.

        Parameters
        ---------
        event_id: str
            The id for the event this minutes item was referenced in.
        minutes_item:id: str
            The id for the minutes item that was referenced.
        index: int
            The integer index for when this minutes item should be placed in the minutes of an event.
        decision: Optional[str]
            If the minutes item was a vote, what was the overall outcome for this minutes item.

        Returns
        -------
        details: Dict[str, Union[str, int]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_person(
        self,
        full_name: str,
        email: str,
        phone: Optional[str] = None,
        website: Optional[str] = None,
        legistar_person_id: Optional[int] = None
    ) -> Dict:
        """
        Get or upload a city council member (person).

        Parameters
        ----------
        full_name: str
            The full name of the city council member.
        email: str
            The email of the city council member.
        phone: Optional[str]
            The phone number of the city council member.
        website: Optional[str]
            The website url of the city council member.
        legistar_person_id: Optional[int]
            If the CDP instance is deployed for a city with Legistar, it is recommended to also store the `PersonId`.

        Returns
        -------
        details: Dict[str, Union[str, Optional[int]]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_vote(
        self,
        person_id: str,
        event_minutes_item_id: str,
        decision: str,
        legistar_event_item_vote_id: Optional[int] = None
    ) -> Dict:
        """
        Get or upload a person's vote on a minutes item.

        Parameters
        ----------
        person_id: str
            The id of the person who voted on an minutes item already tied to an event. (event_minutes_item)
        event_minutes_item_id: str
            The id of the minutes item and event join that was voted on.
        decision: str
            This individual's personal decision on the minutes item.
        legistar_event_item_vote_id: Optional[int]
            If the CDP instance is deployed for a city with Legistar, it is recommended to also store the `PersonId`.

        Returns
        -------
        details: Dict[str, Union[str, Optional[int]]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_file(
        self,
        uri: str,
        filename: Optional[str] = None,
        description: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> Dict:
        """
        Get or upload a file (to the database table, not a file store).

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
            Preferred to use MIME types: https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types

        Returns
        -------
        details: Dict[str, Union[str, Optional[int]]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_transcript(event_id: str, file_id: str, confidence: Optional[float] = None) -> Dict:
        """
        Get or upload a transcript (to the database, a file store).

        Parameters
        ----------
        event_id: str
            The id for the event that this transcript is for.
        file_id: str
            The id for the file that contains the transcript data.
        confidence: Optional[float]
            If available, a float / double value to store with the transcript for the confidence of the transcription.

        Returns
        -------
        details: Dict[str, Union[str, Optional[float]]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_algorithm(
        self,
        name: str,
        version: str,
        description: Optional[str] = None,
        source: Optional[str] = None
    ) -> Dict:
        """
        Get or upload an algorithm.

        Parameters
        ----------
        name: str
            A name for the algorithm. Preferred, the full module path for the algorithm.
        version: str
            A version string for the algorithm.
        description: Optional[str]
            An optional description for the algorithm.
        source: Optional[str]
            An optional source uri for the algorithm.

        Returns
        -------
        details: Dict[str, Union[str, Optional[float]]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_run(self, algorithm_id: str, begin: datetime, completed: datetime) -> Dict:
        """
        Get or upload a run.

        Used as a method for log tracking.

        Parameters
        ----------
        algorithm_id: str
            The id for the algorithm that ran.
        begin: datetime
            The datetime that the algorithm started processing.
        completed: datetime
            The datetime that the algorithm finished processing.

        Returns
        -------
        details: Dict[str, Union[str, datetime]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_run_input(self, run_id: str, dtype: str, value: Any) -> Dict:
        """
        Get or upload a run input.

        Parameters
        ----------
        run_id: str
            The id for which run this parameter was used for.
        dtype: str
            The data type for the value used.
        value: Any
            The value for the input.

        Returns
        -------
        details: Dict[str, Union[str, Any]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_run_input_file(self, run_id: str, file_id: str) -> Dict:
        """
        Get or upload a run input file.

        Parameters
        ----------
        run_id: str
            The id for which run this file was used for.
        file_id: str
            The id for the file used as an input.

        Returns
        -------
        details: Dict[str, str]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_run_output(self, run_id: str, dtype: str, value: Any) -> Dict:
        """
        Get or upload a run output.

        Parameters
        ----------
        run_id: str
            The id for which run this parameter was output from.
        dtype: str
            The data type for the value used.
        value: Any
            The value for the output.

        Returns
        -------
        details: Dict[str, Union[str, Any]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_or_upload_run_output_file(self, run_id: str, file_id: str) -> Dict:
        """
        Get or upload a run output file.

        Parameters
        ----------
        run_id: str
            The id for which run this file was created from.
        file_id: str
            The id for the file created.

        Returns
        -------
        details: Dict[str, str]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def get_indexed_event_term(self, term: str, event_id: str) -> Dict:
        """
        Get a single indexed event term.

        Parameters
        ----------
        term: str
            The string term to retrieve.
        event_id: str
            The id for the event that term was used during.

        Returns
        -------
        details: Dict[str, str]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def upload_or_update_indexed_event_term(self, term: str, event_id: str, value: float) -> Dict:
        """
        Upload or update a single indexed event term.

        Parameters
        ----------
        term: str
            A term used during an event.
        event_id: str
            The id for the event the term was used during.
        value: float
            The value that term should be given for that event that indicates that terms relevance to that event.

        Returns
        -------
        details: Dict[str, Union[str, float]]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def search_events(self, query: str) -> List[Match]:
        """
        Use the stored indexed event terms to query for events given a query.

        Parameters
        ----------
        query: str
            A query string to be used to search for events using the already stored indexed event term table.

        Returns
        -------
        matches: List[Match]
            An list of match objects sorted in most to least relevant order.
        """
        return []

    @abstractmethod
    def get_indexed_minutes_item_term(self, term: str, minutes_item_id: str) -> Dict:
        """
        Get a single indexed minutes item term.

        Parameters
        ----------
        term: str
            The string term to retrieve.
        minutes_item_id: str
            The id for the minutes item that term was used in or discussed about.

        Returns
        -------
        details: Dict[str, str]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def upload_or_update_indexed_minutes_item_term(self, term: str, minutes_item_id: str, value: float) -> Dict:
        """
        Upload or update a single indexed minutes_item item term.

        Parameters
        ----------
        term: str
            A term used during an event.
        minutes_item_id: str
            The id for the minutes item that term was used in or discussed about.
        value: float
            The value that term should be given for that minutes item that indicates that terms relevance to that
            minutes item.

        Returns
        -------
        details: Dict[str, Union[str, float]]
            A dictionary containing the data that was either uploaded or found.
        """
        return {}

    @abstractmethod
    def search_minutes_items(self, query: str) -> List[Match]:
        """
        Use the stored indexed minutes item terms to query for events given a query.

        Parameters
        ----------
        query: str
            A query string to be used to search for minutes items using the already stored indexed minutes items term
            table.

        Returns
        -------
        matches: List[Match]
            An list of match objects sorted in most to least relevant order.
        """
        return []
