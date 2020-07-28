#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, List, Optional
from .event_base import EventBase
from .matter_base import MatterBase
from .matter_type_base import MatterTypeBase


class Matter(MatterBase):
    """
    Source: /docs/document_store_schema.md Matter.
    """

    def __init__(
        self,
        name: str,
        matter_type: MatterTypeBase,
        title: str,
        status: str,
        most_recent_event: EventBase,
        next_event: EventBase,
        keywords: List[Dict[str, str]],
        external_source_id: Optional[Any],
        updated: datetime,
        created: datetime
    ):
        super().__init__(name = name, title = title)
        self._matter_type = matter_type
        self._status = status
        self._most_recent_event = most_recent_event
        self._next_event = next_event
        self._keywords = keywords
        self._external_source_id = external_source_id
        self._updated = updated
        self._created = created

    @property
    def matter_type(self):
        return self._matter_type

    @property
    def status(self):
        return self._status

    @property
    def most_recent_event(self):
        return self._most_recent_event

    @property
    def next_event(self):
        return self._next_event

    @property
    def keywords(self):
        return self._keywords

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
    def from_dict(source: Dict[str, Any]) -> MatterBase:
        return Matter(
            name = source.get("name"),
            matter_type = MatterTypeBase.from_dict(source.get("matter_type")),
            title = source.get("title"),
            status = source.get("status"),
            most_recent_event = EventBase.from_dict(source.get("most_recent_event", {})),
            next_event = EventBase.from_dict(source.get("next_event", {})),
            keywords = source.get("keywords"),
            external_source_id = source.get("external_source_id"),
            updated = source.get("updated"),
            created = source.get("created")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
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
