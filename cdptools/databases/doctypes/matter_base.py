#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Dict
from .doctype import Doctype


class MatterBase(Doctype):
    """
    Abbreviated Matter for nested instances in documents.
    See .matter.py.
    """

    def __init__(
        self,
        name: str,
        title: str,
        type: str = None,
        decision: str = None,
        id: str = None
    ):
        self._name = name
        self._title = title
        self._type = type
        self._decision = decision
        self._id = id

    @property
    def name(self):
        return self._name

    @property
    def matter_type(self):
        return self._matter_type

    @property
    def title(self):
        return self._title

    @property
    def type(self):
        return self._type

    @property
    def decision(self):
        return self._decision

    @property
    def id(self):
        return self._id

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Doctype:
        return MatterBase(
            name = source.get("name"),
            title = source.get("title"),
            type = source.get("type"),
            decision = source.get("decision"),
            id = source.get("id")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "title": self.title,
            "type": self.type,
            "decision": self.decision,
            "id": self.id
        }
