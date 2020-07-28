#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Dict
from .doctype import Doctype


class EventMinutesItemBase(Doctype):
    """
    Abbreviated EventMinutesItem for nested instances in documents.
    See .event_minutes_item.py.
    """

    def __init__(
        self,
        decision: str,
        id: str = None
    ):
        self._decision = decision
        self._id = id

    @property
    def decision(self):
        return self._decision

    @property
    def id(self):
        return self._id

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Doctype:
        return EventMinutesItemBase(
            decision = source.get("decision"),
            id = source.get("id")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "id": self.id
        }
