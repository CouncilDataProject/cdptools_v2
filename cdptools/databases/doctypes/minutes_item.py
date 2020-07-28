#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, Optional
from .matter_base import MatterBase
from .minutes_item_base import MinutesItemBase


class MinutesItem(MinutesItemBase):
    """
    Source: /docs/document_store_schema.md Minutes Item.
    """

    def __init__(
        self,
        name: str,
        description: Optional[str],
        matter: MatterBase,
        external_source_id: Optional[Any],
        created: datetime
    ):
        super().__init__(name = name)
        self._description = description
        self._matter = matter
        self._external_source_id = external_source_id
        self._created = created

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
    def from_dict(source: Dict[str, Any]) -> MinutesItemBase:
        return MinutesItem(
            name = source.get("name"),
            description = source.get("description"),
            matter = MatterBase.from_dict(source.get("matter", {})),
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
