#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, List, Optional
from .doctype import Doctype
from .event import EventAbbr
from .matter_type import MatterTypeAbbr


class Matter(Doctype):
    """
    Source: /docs/document_store_schema.md Matter.
    """

    def __init__(
        self,
        name: str,
        matter_type: MatterTypeAbbr,
        title: str,
        status: str,
        most_recent_event: EventAbbr,
        next_event: EventAbbr,
        keywords: List[Dict[str, str]],
        external_source_id: Optional[Any],
        updated: datetime,
        created: datetime
    ):
        self._name = name
        self._matter_type = matter_type
        self._title = title
        self._status = status
        self._most_recent_event = most_recent_event
        self._next_event = next_event
        self._keywords = keywords
        self._external_source_id = external_source_id
        self._updated = updated
        self._created = created

    @property
    def name(self):
        return self._name

    @property
    def matter_type(self):
        return self._matter_type

    @property
    def title(self):
        return self._title

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
    def from_dict(source: Dict[str, Any]) -> Doctype:
        return Matter(
            name = source.get("name"),
            matter_type = MatterTypeAbbr.from_dict(source.get("matter_type")),
            title = source.get("title"),
            status = source.get("status"),
            most_recent_event = EventAbbr.from_dict(source.get("most_recent_event", {})),
            next_event = EventAbbr.from_dict(source.get("next_event", {})),
            keywords = source.get("keywords"),
            external_source_id = source.get("external_source_id"),
            updated = source.get("updated"),
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


class MatterAbbr(Matter):
    """
    Abbreviated Matter for nested instances in documents.
    """

    def __init__(
        self,
        id: str,
        name: str,
        title: str,
        type: str,
        decision: str
    ):
        super().__init__(name = name, title = title)
        self._id = id
        self._type = type
        self._decision = decision

    @property
    def id(self):
        return self._id

    @property
    def type(self):
        return self._type

    @property
    def decision(self):
        return self._decision

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Matter:
        return MatterAbbr(
            id = source.get("id"),
            name = source.get("name"),
            title = source.get("title"),
            type = source.get("type"),
            decision = source.get("decision")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "title": self.title,
            "type": self.type,
            "decision": self.decision
        }
