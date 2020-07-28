#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Dict
from .doctype import Doctype


class SeatBase(Doctype):
    """
    Abbreviated Seat for nested instances in documents.
    See .seat.py.
    """

    def __init__(
        self,
        name: str,
        electoral_area: str,
        map_file_id: str,
        map_uri: str,
        id: str = None
    ):
        self._name = name
        self._electoral_area = electoral_area
        self._map_file_id = map_file_id
        self._map_uri = map_uri
        self._id = id

    @property
    def name(self):
        return self._name

    @property
    def electoral_area(self):
        return self._electoral_area

    @property
    def map_file_id(self):
        return self._map_file_id

    @property
    def map_uri(self):
        return self._map_uri

    @property
    def id(self):
        return self._id

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Doctype:
        return SeatBase(
            name = source.get("name"),
            electoral_area = source.get("electoral_area"),
            map_file_id = source.get("map_file_id"),
            map_uri = source.get("map_uri"),
            id = source.get("id")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "electoral_area": self.electoral_area,
            "map_file_id": self.map_file_id,
            "map_uri": self.map_uri,
            "id": self.id
        }
