#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, Optional
from .matter_type_base import MatterTypeBase


class MatterType(MatterTypeBase):
    """
    Source: /docs/document_store_schema.md Matter Type.
    """

    def __init__(
        self,
        name: str,
        external_source_id: Optional[Any],
        created: datetime
    ):
        super().__init__(name = name)
        self._external_source_id = external_source_id
        self._created = created

    @property
    def external_source_id(self):
        return self._external_source_id

    @property
    def created(self):
        return self._created

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> MatterTypeBase:
        return MatterType(
            name = source.get("name"),
            external_source_id = source.get("external_source_id"),
            created = source.get("created")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "external_source_id": self.external_source_id,
            "created": self.created
        }
