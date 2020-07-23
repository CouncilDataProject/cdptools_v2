#!/src/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, Optional
from .doctype import Doctype
from .event import EventAbbr
from .event_minutes_item import EventMinutesItemAbbr
from .matter import MatterAbbr
from .person import PersonAbbr


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
        self._matter = matter
        self._event = event
        self._event_minutes_item = event_minutes_item
        self._person = person
        self._vote_decision = vote_decision
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
    def vote_decision(self):
        return self._vote_decision

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
    def from_dict(source: Dict[str, Any]) -> Doctype:
        return Vote(
            matter = VoteAbbr.from_dict(source.get("matter", {})),
            event = EventAbbr.from_dict(source.get("event", {})),
            event_minutes_item = EventMinutesItemAbbr.from_dict(source.get("event_minutes_item", {})),
            person = PersonAbbr.from_dict(source.get("person", {})),
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


class VoteAbbr(Vote):
    """
    Abbreviated Vote for nested instances in documents.
    """

    def __init__(
        self,
        vote_id: str,
        person_id: str,
        person_name: str,
        vote_decision: str
    ):
        super().__init__(vote_decision = vote_decision)
        self._vote_id = vote_id
        self._person_id = person_id
        self._person_name = person_name

    @property
    def vote_id(self):
        return self._vote_id

    @property
    def person_id(self):
        return self._person_id

    @property
    def person_name(self):
        return self._person_name

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Vote:
        return VoteAbbr(
            vote_id = source.get("vote_id"),
            person_id = source.get("person_id"),
            person_name = source.get("person_name"),
            vote_decision = source.get("vote_decision")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vote_id": self.vote_id,
            "person_id": self.person_id,
            "person_name": self.person_name,
            "vote_decision": self.vote_decision
        }
