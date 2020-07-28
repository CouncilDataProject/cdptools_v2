#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Dict
from .doctype import Doctype


class FileBase(Doctype):
    """
    Abbreviated File for nested instances in documents.
    See .file.py.
    """

    def __init__(
        self,
        name: str,
        uri: str,
        id: str = None
    ):
        self._name = name
        self._uri = uri
        self._id = id

    @property
    def name(self):
        return self._name

    @property
    def uri(self):
        return self._uri

    @property
    def id(self):
        return self._id

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Doctype:
        return FileBase(
            name = source.get("name"),
            uri = source.get("uri"),
            id = source.get("id")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "uri": self.uri,
            "id": self.id
        }
