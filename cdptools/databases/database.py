#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, Union

###############################################################################


class WhereCondition(NamedTuple):
    column_name: str
    operator: str
    value: Union[bool, datetime, float, int, str]


class OrderCondition(NamedTuple):
    column_name: str
    operator: str


class Database(ABC):

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
        thumbnail_uri: str,
        video_uri: str
    ) -> Dict:
        """
        Get or upload an event.
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
    def get_or_upload_file(self, uri: str, filename: Optional[str] = None) -> Dict:
        """
        Get or upload a file.
        """
        return {}

    @abstractmethod
    def get_or_upload_run_input(self, run_id: str, type: str, value: Any) -> Dict:
        """
        Get or upload a run input.
        """
        return {}

    @abstractmethod
    def get_or_upload_run_input_file(self, run_input_id: str, file_id: str) -> Dict:
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
    def get_or_upload_run_output_file(self, run_output_id: str, file_id: str) -> Dict:
        """
        Get or upload a run output file.
        """
        return {}
