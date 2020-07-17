#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, Optional
from .doctype import Doctype
from .matter import Matter


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
        self.name = name
        self.description = description
        self.matter = matter
        self.external_source_id = external_source_id
        self.created = created

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> MinutesItem:
        return MinutesItem(
            name = source.get("name"),
            description = source.get("description"),
            matter = Matter.from_dict(source.get("matter", {})),
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
