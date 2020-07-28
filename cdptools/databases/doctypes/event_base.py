#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict
from .doctype import Doctype


class EventBase(Doctype):
    """
    Abbreviated Event for nested instances in documents.
    See .event.py.
    """

    def __init__(
        self,
        event_datetime: datetime,
        id: str = None,
        body_name: str = None
    ):
        self._event_datetime = event_datetime
        self._id = id
        self._body_name = body_name

    @property
    def event_datetime(self):
        return self._event_datetime

    @property
    def id(self):
        return self._id

    @property
    def body_name(self):
        return self._body_name

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Doctype:
        return EventBase(
            event_datetime = source.get("event_datetime"),
            body_name = source.get("body_name"),
            id = source.get("id")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_datetime": self.event_datetime,
            "body_name": self.body_name,
            "id": self.id
        }
