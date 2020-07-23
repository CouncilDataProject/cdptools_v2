#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict
from .doctype import Doctype


class Seat(Doctype):
    """
    Source: docs/document_store_schema.md Seat.
    """

    def __init__(
        self,
        name: str,
        electoral_area: str,
        electoral_type: str,
        map_file_id: str,
        map_uri: str,
        created: datetime
    ):
        self._name = name
        self._electoral_area = electoral_area
        self._electoral_type = electoral_type
        self._map_file_id = map_file_id
        self._map_uri = map_uri
        self._created = created

    @property
    def name(self):
        return self._name

    @property
    def electoral_area(self):
        return self._electoral_area

    @property
    def electoral_type(self):
        return self._electoral_type

    @property
    def map_file_id(self):
        return self._map_file_id

    @property
    def map_uri(self):
        return self._map_uri

    @property
    def created(self):
        return self._created

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Doctype:
        return Seat(
            name = source.get("name"),
            electoral_area = source.get("electoral_area"),
            electoral_type = source.get("electoral_type"),
            map_file_id = source.get("map_file_id"),
            map_uri = source.get("map_uri"),
            created = source.get("created")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "electoral_area": self.electoral_area,
            "electoral_type": self.electoral_type,
            "map_file_id": self.map_file_id,
            "map_uri": self.map_uri,
            "created": self.created
        }


class SeatAbbr(Seat):
    """
    Abbreviated Seat for nested instances in documents.
    """

    def __init__(
        self,
        id: str,
        name: str,
        electoral_area: str,
        map_file: str,
        map_uri: str
    ):
        super().__init__(
            name = name,
            electoral_area = electoral_area,
            map_file_id = map_file,
            map_uri = map_uri
        )
        self._id = id

    @property
    def id(self):
        return self._id

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Seat:
        return SeatAbbr(
            id = source.get("id"),
            name = source.get("name"),
            electoral_area = source.get("electoral_area"),
            map_file = source.get("map_file"),
            map_uri = source.get("map_uri")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "electoral_area": self.electoral_area,
            "map_file_id": self.map_file_id,
            "map_uri": self.map_uri
        }
