#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, Optional
from .doctype import Doctype


class Body(Doctype):
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
        self.name = name
        self.tag = tag
        self.description = description
        self.start_date = start_date
        self.end_date = end_date
        self.is_active = is_active
        self.chair_person_id = chair_person_id
        self.external_source_id = external_source_id
        self.updated = updated
        self.created = created

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Body:
        return Body(
            name = source.get("name"),
            tag = source.get("tag"),
            description = source.get("description"),
            start_date = source.get("datetime"),
            end_date = source.get("end_date"),
            is_active = source.get("bool"),
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
