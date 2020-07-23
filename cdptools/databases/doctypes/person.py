#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, Optional
from .body import BodyAbbr
from .doctype import Doctype
from .file import FileAbbr
from .seat import SeatAbbr


class Person(Doctype):
    """
    Source: docs/document_store_schema.md Person.
    """

    def __init__(
        self,
        router_id: Optional[str],
        name: str,
        email: Optional[str],
        phone: Optional[str],
        website: Optional[str],
        picture_file: FileAbbr,
        is_active: bool,
        is_council_president: bool,
        most_recent_seat: SeatAbbr,
        most_recent_chair_body: BodyAbbr,
        terms_serving_in_current_seat_role: int,
        terms_serving_in_current_committee_chair_role: int,
        external_source_id: Optional[Any],
        updated: datetime,
        created: datetime
    ):
        self._router_id = router_id
        self._name = name
        self._email = email
        self._phone = phone
        self._website = website
        self._picture_file = picture_file
        self._is_active = is_active
        self._is_council_president = is_council_president
        self._most_recent_seat = most_recent_seat
        self._most_recent_chair_body = most_recent_chair_body
        self._terms_serving_in_current_seat_role = terms_serving_in_current_seat_role
        self._terms_serving_in_current_committee_chair_role = terms_serving_in_current_committee_chair_role
        self._external_source_id = external_source_id
        self._updated = updated
        self._created = created

    @property
    def router_id(self):
        return self._router_id

    @property
    def name(self):
        return self._name

    @property
    def email(self):
        return self._email

    @property
    def phone(self):
        return self._phone

    @property
    def website(self):
        return self._website

    @property
    def picture_file(self):
        return self._picture_file

    @property
    def is_active(self):
        return self._is_active

    @property
    def is_council_president(self):
        return self._is_council_president

    @property
    def most_recent_seat(self):
        return self._most_recent_seat

    @property
    def most_recent_chair_body(self):
        return self._most_recent_chair_body

    @property
    def terms_serving_in_current_seat_role(self):
        return self._terms_serving_in_current_seat_role

    @property
    def terms_serving_in_current_committee_chair_role(self):
        return self._terms_serving_in_current_committee_chair_role

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
        return Person(
            router_id = source.get("router_id"),
            name = source.get("name"),
            email = source.get("email"),
            phone = source.get("phone"),
            website = source.get("website"),
            picture_file = FileAbbr.from_dict(source.get("picture_file", {})),
            is_active = source.get("is_active"),
            is_council_president = source.get("is_council_president"),
            most_recent_seat = SeatAbbr.from_dict(source.get("most_recent_seat", {})),
            most_recent_chair_body = BodyAbbr.from_dict(source.get("most_recent_chair_body", {})),
            terms_serving_in_current_seat_role = source.get("terms_serving_in_current_seat_role"),
            terms_serving_in_current_committee_chair_role = source.get("terms_serving_in_current_committee_chair_role"),
            external_source_id = source.get("external_source_id"),
            updated = source.get("updated"),
            created = source.get("created")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "router_id": self.router_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "website": self.website,
            "picture_file": self.picture_file.to_dict(),
            "is_active": self.is_active,
            "is_council_president": self.is_council_president,
            "most_recent_seat": self.most_recent_seat.to_dict(),
            "most_recent_chair_body": self.most_recent_chair_body.to_dict(),
            "terms_serving_in_current_seat_role": self.terms_serving_in_current_seat_role,
            "terms_serving_in_current_committee_chair_role": self.terms_serving_in_current_committee_chair_role,
            "external_source_id": self.external_source_id,
            "updated": self.updated,
            "created": self.created
        }


class PersonAbbr(Person):
    """
    Abbreviated Person for nested instances in documents.
    """

    def __init__(
        self,
        id: str,
        name: str
    ):
        super.__init__(name = name)
        self._id = id

    @property
    def id(self):
        return self._id

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Person:
        return PersonAbbr(
            id = source.get("id"),
            name = source.get("name")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name
        }
