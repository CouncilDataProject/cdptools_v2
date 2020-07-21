#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, List, Optional
from .body import Body
from .doctype import Doctype
from .file import File
from .matter import Matter
from .minute_item import MinuteItem
from .person import Person


class Event(Doctype):
    """
    Source: docs/document_store_schema.md Event.
    """

    def __init__(
        self,
        body: Body,
        event_datetime: datetime,
        thumbnail_static_file: File,
        thumbnail_hover_file: File,
        video_uri: Optional[str],
        keywords: List[Dict[str, str]],
        matters: List[Matter],
        minutes_items: List[MinuteItem],
        people: List[Person],
        external_source_id: Optional[Any],
        agenda_uri: str,
        minutes_uri: Optional[str],
        updated: datetime,
        created: datetime
    ):
        self.body = body
        self.event_datetime = event_datetime
        self.thumbnail_static_file = thumbnail_static_file
        self.thumbnail_hover_file = thumbnail_hover_file
        self.video_uri = video_uri
        self.keywords = keywords
        self.matters = matters
        self.minutes_items = minutes_itmems
        self.people = people
        self.external_source_id = external_source_id
        self.agenda_uri = agenda_uri
        self.minutes_uri = minutes_uri
        self.updated = updated
        self.created = created

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Doctype:
        return Event(
            body = Body.from_dict(source.get("body", {})),
            event_datetime = source.get("event_datetime"),
            thumbnail_static_file = File.from_dict(source.get("thumbnail_static_file", {})),
            thumbnail_hover_file = File.from_dict(source.get("thumbnail_hover_file", {})),
            video_uri = source.get("video_uri"),
            keywords = source.get("keywords"),
            matters = [Matter.from_dict(m) for m in source.get("matters", {})],
            minutes_items = [MinuteItem.from_dict(mi) for mi in source.get("minute_items", {})],
            people = [Person.from_dict(p) for p in source.get("people", {})],
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
