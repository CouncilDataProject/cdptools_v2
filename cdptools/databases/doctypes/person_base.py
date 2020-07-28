#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Dict
from .doctype import Doctype


class PersonBase(Doctype):
    """
    Abbreviated Person for nested instances in documents.
    See .person.py.
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
        return PersonBase(
            name = source.get("name"),
            id = source.get("id")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "id": self.id
        }
