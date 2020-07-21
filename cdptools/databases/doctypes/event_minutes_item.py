#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Dict, List, Optional
from .doctype import Doctype
from .file import File
from .matter import Matter
from .minutes_item import MinutesItem
from .vote import Vote


class EventMinutesItem(Doctype):
    """
    Source: docs/document_store_schema.md Event Minutes Item.
    """

    def __init__(
        self,
        event_id: str,
        minutes_item: MinutesItem,
        index: int,
        decision: Optional[str],
        matter: Matter,
        votes: List[Vote],
        files: List[File]
    ):
        self.event_id = event_id
        self.minutes_item = minutes_item
        self.index = index
        self.decision = decision
        self.matter = matter
        self.votes = votes
        self.files = files

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Doctype:
        return EventMinutesItem(
            event_id = source.get("event_id"),
            minutes_item = MinutesItem.from_dict(source.get("minutes_item", {})),
            index = source.get("index"),
            decision = source.get("decision"),
            matter = source.get("matter", {}),
            votes = [Vote.from_dict(v) for v in source.get("votes", {})],
            files = [File.from_dict(f) for f in source.get("files", {})]
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "minutes_item": self.minutes_item.to_dict(),
            "index": self.index,
            "decision": self.decision,
            "matter": self.matter.to_dict(),
            "votes": [v.to_dict() for v in self.votes],
            "files": [f.to_dict() for f in self.files]
        }
