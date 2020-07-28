#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Dict
from .doctype import Doctype


class MatterTypeBase(Doctype):
    """
    Abbreviated MatterType for nested instances in documents.
    See .matter_type.py.
    """

    def __init__(
        self,
        name: str,
        id: str = None
    ):
        self._name = name
        self._id = id

    @property
    def name(self):
        return self._name

    @property
    def id(self):
        return self._id

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Doctype:
        return MatterTypeBase(
            name = source.get("name"),
            id = source.get("id")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "id": self.id
        }
