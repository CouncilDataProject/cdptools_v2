#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, Optional
from .doctype import Doctype
from .file import File
from .seat import Seat


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
        picture_file: File,
        is_active: bool,
        is_council_president: bool,
        most_recent_seat: Seat,
        most_recent_chair_body: Body,
        terms_serving_in_current_seat_role: int,
        terms_serving_in_current_committee_chair_role: int,
        external_source_id: Optional[Any],
        updated: datetime,
        created: datetime
    ):
        self.router_id = router_id
        self.name = name
        self.email = email
        self.phone = phone
        self.website = website
        self.picture_file = picture_file
        self.is_active = is_active
        self.is_council_president = is_council_president
        self.most_recent_seat = most_recent_seat
        self.most_recent_chair_body = most_recent_chair_body
        self.terms_serving_in_current_seat_role = terms_serving_in_current_seat_role
        self.terms_serving_in_current_committee_chair_role = terms_serving_in_current_committee_chair_role
        self.external_source_id = external_source_id
        self.updated = updated
        self.created = created

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Person:
        return Person(
            router_id = source.get("router_id"),
            name = source.get("name"),
            email = source.get("email"),
            phone = source.get("phone"),
            website = source.get("website"),
            picture_file = File.from_dict(source.get("picture_file", {})),
            is_active = source.get("is_active"),
            is_council_president = source.get("is_council_president"),
            most_recent_seat = Seat.from_dict(source.get("most_recent_seat", {})),
            most_recent_chair_body = Body.from_dict(source.get("most_recent_chair_body", {})),
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
            "most_recent_seat": self.most_recent_seat,
            "most_recent_chair_body": self.most_recent_chair_body,
            "terms_serving_in_current_seat_role": self.terms_serving_in_current_seat_role,
            "terms_serving_in_current_committee_chair_role": self.terms_serving_in_current_committee_chair_role,
            "external_source_id": self.external_source_id,
            "updated": self.updated,
            "created": self.created
        }
