#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, List, Optional
from .doctype import Doctype
from .event import Event
from .matter_type import MatterType


class Matter(Doctype):
    """
    Source: /docs/document_store_schema.md Matter.
    """

    def __init__(
        self,
        name: str,
        matter_type: MatterType,
        title: str,
        status: str,
        most_recent_event: Event,
        next_event: Event,
        keywords: List[Dict[str, str]],
        external_source_id: Optional[Any],
        updated: datetime,
        created: datetime
    ):
        self.name = name
        self.matter_type = matter_type
        self.title = title
        self.status = status
        self.most_recent_event = most_recent_event
        self.next_event = next_event
        self.keywords = keywords
        self.external_source_id = external_source_id
        self.updated = updated
        self.created = created

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Matter:
        return Matter(
            name = source.get("name"),
            matter_type = MatterType.from_dict(source.get("matter_type")),
            title = source.get("title"),
            status = source.get("status"),
            most_recent_event = Event.from_dict(source.get("most_recent_event", {})),
            next_event = Event.from_dict(source.get("next_event", {})),
            keywords = source.get("keywords"),
            external_source_id = source.get("external_source_id"),
            updated = source.get("updated")
            created = source.get("created")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name.to_dict(),
            "matter_type": self.matter_type.to_dict(),
            "title": self.title,
            "status": self.status,
            "most_recent_event": self.most_recent_event.to_dict(),
            "next_event": self.next_event.to_dict(),
            "keywords": self.keywords,
            "external_source_id": self.external_source_id,
            "updated": self.updated,
            "created": self.created
        }
