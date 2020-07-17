#!/src/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, Optional
from .doctype import Doctype
from .event import Event
from .event_minutes_item import EventMinutesItem
from .matter import Matter
from .person import Person


class Vote(Doctype):
    """
    Source: docs/document_store_schema.md Vote.
    """

    def __init__(
        self,
        matter: Matter,
        event: Event,
        event_minutes_item: EventMinutesItem,
        person: Person,
        vote_decision: str,
        is_majority: bool,
        external_vote_item_id: Optional[Any],
        created: datetime
    ):
        self.matter = matter
        self.event = event
        self.event_minutes_item = event_minutes_item
        self.person = person
        self.vote_decision = vote_decision
        self.is_majority = is_majority
        self.external_vote_item_id = external_vote_item_id
        self.created = created

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Vote:
        return Vote(
            matter = Vote.from_dict(source.get("matter", {})),
            event = Event.from_dict(source.get("event", {})),
            event_minutes_item = EventMinutesItem.from_dict(source.get("event_minutes_item", {})),
            person = Person.from_dict(source.get("person", {})),
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
