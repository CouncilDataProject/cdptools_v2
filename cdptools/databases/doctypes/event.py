#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, List, Optional
from .body import BodyAbbr
from .doctype import Doctype
from .file import FileAbbr
from .matter import MatterAbbr
from .minutes_item import MinutesItemAbbr
from .person import PersonAbbr


class Event(Doctype):
    """
    Source: docs/document_store_schema.md Event.
    """

    def __init__(
        self,
        body: BodyAbbr,
        event_datetime: datetime,
        thumbnail_static_file: FileAbbr,
        thumbnail_hover_file: FileAbbr,
        video_uri: Optional[str],
        keywords: List[Dict[str, str]],
        matters: List[MatterAbbr],
        minutes_items: List[MinutesItemAbbr],
        people: List[PersonAbbr],
        external_source_id: Optional[Any],
        agenda_uri: str,
        minutes_uri: Optional[str],
        updated: datetime,
        created: datetime
    ):
        self._body = body
        self._event_datetime = event_datetime
        self._thumbnail_static_file = thumbnail_static_file
        self._thumbnail_hover_file = thumbnail_hover_file
        self._video_uri = video_uri
        self._keywords = keywords
        self._matters = matters
        self._minutes_items = minutes_itmems
        self._people = people
        self._external_source_id = external_source_id
        self._agenda_uri = agenda_uri
        self._minutes_uri = minutes_uri
        self._updated = updated
        self._created = created

    @property
    def body(self):
        return self._body

    @property
    def event_datetime(self):
        return self._event_datetime

    @property
    def thumbnail_static_file(self):
        return self._thumbnail_static_file

    @property
    def thumbnail_hover_file(self):
        return self.thumbnail_hover_file

    @property
    def video_uri(self):
        return self._video_uri

    @property
    def keywords(self):
        return self._keywords

    @property
    def matters(self):
        return self._matters

    @property
    def minutes_items(self):
        return self._minutes_items

    @property
    def people(self):
        return self._people

    @property
    def external_source_id(self):
        return self._external_source_id

    @property
    def agenda_uri(self):
        return self._agenda_uri

    @property
    def minutes_uri(self):
        return self._minutes_uri

    @property
    def updated(self):
        return self._updated

    @property
    def created(self):
        return self._created

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Doctype:
        return Event(
            body = BodyAbbr.from_dict(source.get("body", {})),
            event_datetime = source.get("event_datetime"),
            thumbnail_static_file = FileAbbr.from_dict(source.get("thumbnail_static_file", {})),
            thumbnail_hover_file = FileAbbr.from_dict(source.get("thumbnail_hover_file", {})),
            video_uri = source.get("video_uri"),
            keywords = source.get("keywords"),
            matters = [MatterAbbr.from_dict(m) for m in source.get("matters", {})],
            minutes_items = [MinutesItemAbbr.from_dict(mi) for mi in source.get("minute_items", {})],
            people = [PersonAbbr.from_dict(p) for p in source.get("people", {})],
            external_source_id = source.get("external_source_id"),
            agenda_uri = source.get("agenda_uri"),
            minutes_uri = source.get("minutes_uri"),
            updated = source.get("updated"),
            created = source.get("created")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "body": self.body.to_dict(),
            "event_datetime": self.event_datetime,
            "thumbnail_static_file": self.thumbnail_static_file.to_dict(),
            "thumbnail_hover_file": self.thumbnail_hover_file.to_dict(),
            "video_uri": self.video_uri,
            "keywords": self.keywords,
            "matters": [m.to_dict() for m in self.matters],
            "minutes_items": [mi.to_dict() for mi in self.minutes_items],
            "people": [p.to_dict() for p in self.people],
            "external_source_id": self.external_source_id,
            "agenda_uri": self.agenda_uri,
            "minutes_uri": self.minutes_uri,
            "updated": self.updated,
            "created": self.created
        }


class EventAbbr(Event):
    """
    Abbreviated Event for nested instances in documents.
    """

    def __init__(
        self,
        id: str,
        body_name: str,
        event_datetime: str
    ):
        super().__init__(body_name = body_name)
        self._id = id
        self._event_datetime = event_datetime

    @property
    def id(self):
        return self._id

    @property
    def event_datetime(self):
        return self._event_datetime

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Event:
        return EventAbbr(
            id = source.get("id"),
            body_name = source.get("body_name"),
            event_datetime = source.get("event_datetime")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "body_name": self.body_name,
            "event_datetime": self.event_datetime
        }
