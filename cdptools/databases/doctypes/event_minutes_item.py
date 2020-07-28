#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Dict, List, Optional
from .event_minutes_item_base import EventMinutesItemBase
from .file_base import FileBase
from .matter_base import MatterBase
from .minutes_item_base import MinutesItemBase
from .vote_base import VoteBase


class EventMinutesItem(EventMinutesItemBase):
    """
    Source: docs/document_store_schema.md Event Minutes Item.
    """

    def __init__(
        self,
        event_id: str,
        minutes_item: MinutesItemBase,
        index: int,
        decision: Optional[str],
        matter: MatterBase,
        votes: List[VoteBase],
        files: List[FileBase]
    ):
        super().__init__(decision = decision)
        self._event_id = event_id
        self._minutes_item = minutes_item
        self._index = index
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
    def matter(self):
        return self._matter

    @property
    def votes(self):
        return self._votes

    @property
    def files(self):
        return self._files

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> EventMinutesItemBase:
        return EventMinutesItem(
            event_id = source.get("event_id"),
            minutes_item = MinutesItemBase.from_dict(source.get("minutes_item", {})),
            index = source.get("index"),
            decision = source.get("decision"),
            matter = MatterBase.from_dict(source.get("matter", {})),
            votes = [VoteBase.from_dict(v) for v in source.get("votes", {})],
            files = [FileBase.from_dict(f) for f in source.get("files", {})]
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
