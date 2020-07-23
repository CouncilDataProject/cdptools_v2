#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Dict, List, Optional
from .doctype import Doctype
from .file import FileAbbr
from .matter import MatterAbbr
from .minutes_item import MinutesItemAbbr
from .vote import Votes


class EventMinutesItem(Doctype):
    """
    Source: docs/document_store_schema.md Event Minutes Item.
    """

    def __init__(
        self,
        event_id: str,
        minutes_item: MinutesItemAbbr,
        index: int,
        decision: Optional[str],
        matter: MatterAbbr,
        votes: List[VoteAbbr],
        files: List[FileAbbr]
    ):
        self._event_id = event_id
        self._minutes_item = minutes_item
        self._index = index
        self._decision = decision
        self._matter = matter
        self._votes = votes
        self._files = files

    @property
    def event_id(self):
        return self._event_id

    @property
    def minutes_item(self):
        return self._minutes_item

    @property
    def index(self):
        return self._index

    @property
    def decision(self):
        return self._decision

    @property
    def matter(self):
        return self._matter

    @property
    def votes(self):
        return self._votes

    @property
    def files(self):
        return self._files

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Doctype:
        return EventMinutesItem(
            event_id = source.get("event_id"),
            minutes_item = MinutesItemAbbr.from_dict(source.get("minutes_item", {})),
            index = source.get("index"),
            decision = source.get("decision"),
            matter = MatterAbbr.from_dict(source.get("matter", {})),
            votes = [VoteAbbr.from_dict(v) for v in source.get("votes", {})],
            files = [FileAbbr.from_dict(f) for f in source.get("files", {})]
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


class EventMinutesItemAbbr(EventMinutesItem):
    """
    Abbreviated EventMinutesItem for nested instances in documents.
    """

    def __init__(
        self,
        id: str,
        decision: str
    ):
        super().__init__(decision = decision)
        self._id = id

    @property
    def id(self):
        return self._id

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> EventMinutesItem:
        return EventMinutesItemAbbr(
            id = source.get("id"),
            decision = source.get("decision")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "decision": self.decision
        }
