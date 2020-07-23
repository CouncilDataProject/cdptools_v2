#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, Optional
from .doctype import Doctype
from .matter import MatterAbbr


class MinutesItem(Doctype):
    """
    Source: /docs/document_store_schema.md Minutes Item.
    """

    def __init__(
        self,
        name: str,
        description: Optional[str],
        matter: Matter,
        external_source_id: Optional[Any],
        created: datetime
    ):
        self._name = name
        self._description = description
        self._matter = matter
        self._external_source_id = external_source_id
        self._created = created

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def matter(self):
        return self._matter

    @property
    def external_source_id(self):
        return self._external_source_id

    @property
    def created(self):
        return self._created

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Doctype:
        return MinutesItem(
            name = source.get("name"),
            description = source.get("description"),
            matter = MatterAbbr.from_dict(source.get("matter", {})),
            external_source_id = source.get("external_source_id"),
            created = source.get("created")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "matter": self.matter.to_dict(),
            "external_source_id": self.external_source_id,
            "created": self.created
        }


class MinutesItemAbbr(MinutesItem):
    """
    Abbreviated MinutesItem for nested instances in documents.
    """

    def __init__(
        self,
        id: str,
        name: str
    ):
        super().__init__(name = name)
        self._id = id

    @property
    def id(self):
        return self._id

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> MinutesItem:
        return MinutesItemAbbr(
            id = source.get("id"),
            name = source.get("name")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name
        }
