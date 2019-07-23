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


class EventTerm(NamedTuple):
    term: str
    contribution: float


class EventMatch:
    def __init__(self, event_id, event_terms: List[EventTerm]):
        self._event_id = event_id
        self._terms = event_terms

    @property
    def event_id(self):
        return self._event_id

    @property
    def terms(self):
        return self._terms

    @property
    def relevance(self):
        return sum(t.contribution for t in self.terms)

    def __str__(self):
        return f"<EventMatch [event_id: {self.event_id}, relevance: {self.relevance}]>"

    def __repr__(self):
        return str(self)


###############################################################################


class Database(ABC):

    @staticmethod
    def _construct_where_condition(filt: Union[WhereCondition, List, Tuple]):
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
    def _construct_orderby_condition(by: Union[List, OrderCondition, str, Tuple]):
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
    def select_row_by_id(self, table: str, id: str) -> Dict:
        """
        Get row from a table by looking up it's id.
        """
        return {}

    @abstractmethod
    def select_rows_as_list(
        self,
        table: str,
        filters: Optional[List[Union[WhereCondition, List, Tuple]]] = None,
        order_by: Optional[Union[List, OrderCondition, str, Tuple]] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get a list of rows from a table optionally using filters, ordering, and limit.
        """
        return []

    @abstractmethod
    def get_or_upload_body(self, name: str, description: Optional[str]) -> Dict:
        """
        Get or upload a body.
        """
        return {}

    @abstractmethod
    def get_or_upload_minutes_item(self, name: str, matter: str, legistar_event_item_id: Optional[int] = None) -> Dict:
        """
        Get or upload a minutes item. In Legistar this is commonly referred to as an event item.
        (Minutes item, in my opinion, is a better definition for the goals of CDP.)
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
        Get or upload a minutes item file.
        """
        return {}

    @abstractmethod
    def get_event(self, video_uri: str) -> Dict:
        """
        Find an event using the video uri.
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
        legistar_event_link: Optional[int] = None
    ) -> Dict:
        """
        Get or upload an event.
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
        Get or upload a person.
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
        Get or upload a file.
        """
        return {}

    @abstractmethod
    def get_or_upload_transcript(event_id: str, file_id: str, confidence: Optional[float] = None) -> Dict:
        """
        Get or upload a transcript.
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
        """
        return {}

    @abstractmethod
    def get_or_upload_run(self, algorithm_id: str, begin: datetime, completed: datetime) -> Dict:
        """
        Get or upload a run.
        """
        return {}

    @abstractmethod
    def get_or_upload_run_input(self, run_id: str, type: str, value: Any) -> Dict:
        """
        Get or upload a run input.
        """
        return {}

    @abstractmethod
    def get_or_upload_run_input_file(self, run_id: str, file_id: str) -> Dict:
        """
        Get or upload a run input file.
        """
        return {}

    @abstractmethod
    def get_or_upload_run_output(self, run_id: str, type: str, value: Any) -> Dict:
        """
        Get or upload a run output.
        """
        return {}

    @abstractmethod
    def get_or_upload_run_output_file(self, run_id: str, file_id: str) -> Dict:
        """
        Get or upload a run output file.
        """
        return {}

    @abstractmethod
    def get_index_term(self, term: str, event_id: str) -> Dict:
        """
        Get a single index term.
        """
        return {}

    @abstractmethod
    def upload_or_update_index_term(self, term: str, event_id: str, value: float) -> Dict:
        """
        Upload or update a single index term.
        """
        return {}

    @abstractmethod
    def search_events(self, query: str) -> List[EventMatch]:
        """
        Use the stored index terms to query for events given a query.
        """
        return []
