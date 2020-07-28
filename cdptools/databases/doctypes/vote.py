#!/src/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, Optional
from .event_base import EventBase
from .event_minutes_item_base import EventMinutesItemBase
from .matter_base import MatterBase
from .person_base import PersonBase
from .vote_base import VoteBase


class Vote(VoteBase):
    """
    Source: docs/document_store_schema.md Vote.
    """

    def __init__(
        self,
        matter: MatterBase,
        event: EventBase,
        event_minutes_item: EventMinutesItemBase,
        person: PersonBase,
        vote_decision: str,
        is_majority: bool,
        external_vote_item_id: Optional[Any],
        created: datetime
    ):
        super().__init__(vote_decision = vote_decision)
        self._matter = matter
        self._event = event
        self._event_minutes_item = event_minutes_item
        self._person = person
        self._is_majority = is_majority
        self._external_vote_item_id = external_vote_item_id
        self._created = created

    @property
    def matter(self):
        return self._matter

    @property
    def event(self):
        return self._event

    @property
    def event_minutes_item(self):
        return self._event_minutes_item

    @property
    def person(self):
        return self._person

    @property
    def is_majority(self):
        return self._is_majority

    @property
    def external_vote_item_id(self):
        return self._external_vote_item_id

    @property
    def created(self):
        return self._created

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> VoteBase:
        return Vote(
            matter = MatterBase.from_dict(source.get("matter", {})),
            event = EventBase.from_dict(source.get("event", {})),
            event_minutes_item = EventMinutesItemBase.from_dict(source.get("event_minutes_item", {})),
            person = PersonBase.from_dict(source.get("person", {})),
            vote_decision = source.get("vote_decision"),
            is_majority = source.get("is_majority"),
            external_vote_item_id = source.get("external_vote_item_id"),
            created = source.get("created")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "matter": self.matter.to_dict(),
            "event": self.event.to_dict(),
            "event_minutes_item": self.event_minutes_item.to_dict(),
            "person": self.person.to_dict(),
            "vote_decision": self.vote_decision,
            "is_majority": self.is_majority,
            "external_vote_item_id": self.external_vote_item_id,
            "created": self.created
        }
