#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict
from .seat_base import SeatBase


class Seat(SeatBase):
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
        super().__init__(
            name = name,
            electoral_area = electoral_area,
            map_file_id = map_file_id,
            map_uri = map_uri
        )
        self._electoral_type = electoral_type
        self._created = created

    @property
    def electoral_type(self):
        return self._electoral_type

    @property
    def created(self):
        return self._created

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> SeatBase:
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
