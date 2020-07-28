#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, Optional
from .body_base import BodyBase


class Body(BodyBase):
    """
    Source: docs/document_store_schema.md Body.
    """

    def __init__(
        self,
        name: str,
        tag: str,
        description: Optional[str],
        start_date: datetime,
        end_date: Optional[datetime],
        is_active: bool,
        chair_person_id: str,
        external_source_id: Optional[Any],
        updated: datetime,
        created: datetime
    ):
        super().__init__(name = name)
        self._tag = tag
        self._description = description
        self._start_date = start_date
        self._end_date = end_date
        self._is_active = is_active
        self._chair_person_id = chair_person_id
        self._external_source_id = external_source_id
        self._updated = updated
        self._created = created

    @property
    def tag(self):
        return self._tag

    @property
    def description(self):
        return self._description

    @property
    def start_date(self):
        return self._start_date

    @property
    def end_date(self):
        return self._end_date

    @property
    def is_active(self):
        return self._is_active

    @property
    def chair_person_id(self):
        return self._chair_person_id

    @property
    def external_source_id(self):
        return self._external_source_id

    @property
    def updated(self):
        return self._updated

    @property
    def created(self):
        return self._created

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> BodyBase:
        return Body(
            name = source.get("name"),
            tag = source.get("tag"),
            description = source.get("description"),
            start_date = source.get("start_date"),
            end_date = source.get("end_date"),
            is_active = source.get("is_active"),
            chair_person_id = source.get("chair_person_id"),
            external_source_id = source.get("external_source_id"),
            updated = source.get("updated"),
            created = source.get("created")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "tag": self.tag,
            "description": self.description,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "is_active": self.is_active,
            "chair_person_id": self.chair_person_id,
            "external_source_id": self.external_source_id,
            "updated": self.updated,
            "created": self.created
        }
