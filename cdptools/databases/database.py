#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, NamedTuple, Optional, Union

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
    def get_or_upload_body(
        self,
        name: str,
        description: Optional[str]
    ) -> Dict:
        """
        Get or upload a body.
        """

        return {}

    @abstractmethod
    def get_or_upload_event(
        self,
        body_id: int,
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
