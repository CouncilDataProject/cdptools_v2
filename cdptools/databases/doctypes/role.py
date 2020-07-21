#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, Optional
from .body import Body
from .doctype import Doctype
from .person import Person


class Role(Doctype):
    """
    Source: /docs/document_store_schema.md Role.
    """

    def __init__(
        self,
        person: Person,
        title: str,
        body: Body,
        start_date: datetime,
        end_date: datetime,
        seat_id: str,
        external_source_id: Optional[Any],
        created: datetime
    ):
        self.person = person
        self.title = title
        self.body = body
        self.start_date = start_date
        self.end_date = end_date
        self.seat_id = seat_id
        self.external_source_id = external_source_id
        self.created = created

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Doctype:
        return Role(
            person = Person.from_dict(source.get("person", {})),
            title = source.get("title"),
            body = source.get("body", {}),
            start_date = source.get("start_date"),
            end_date = source.get("end_date"),
            seat_id = source.get("seat_id"),
            external_source_id = source.get("external_source_id"),
            created = source.get("created")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "person": self.person.to_dict(),
            "title": self.title,
            "body": self.body.to_dict(),
            "start_date": self.start_date,
            "end_date": self.end_date,
            "seat_id": self.seat_id,
            "external_source_id": self.external_source_id,
            "created": source.created
        }
