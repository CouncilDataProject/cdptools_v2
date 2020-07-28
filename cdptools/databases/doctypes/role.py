#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, Optional
from .body_base import BodyBase
from .doctype import Doctype
from .person_base import PersonBase


class Role(Doctype):
    """
    Source: /docs/document_store_schema.md Role.
    """

    def __init__(
        self,
        person: PersonBase,
        title: str,
        body: BodyBase,
        start_date: datetime,
        end_date: datetime,
        seat_id: str,
        external_source_id: Optional[Any],
        created: datetime
    ):
        self._person = person
        self._title = title
        self._body = body
        self._start_date = start_date
        self._end_date = end_date
        self._seat_id = seat_id
        self._external_source_id = external_source_id
        self._created = created

    @property
    def person(self):
        return self._person

    @property
    def title(self):
        return self._title

    @property
    def body(self):
        return self._body

    @property
    def start_date(self):
        return self._start_date

    @property
    def end_date(self):
        return self._end_date

    @property
    def seat_id(self):
        return self._seat_id

    @property
    def external_source_id(self):
        return self._external_source_id

    @property
    def created(self):
        return self._created

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Doctype:
        return Role(
            person = PersonBase.from_dict(source.get("person", {})),
            title = source.get("title"),
            body = BodyBase.from_dict(source.get("body", {})),
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
            "created": self.created
        }
