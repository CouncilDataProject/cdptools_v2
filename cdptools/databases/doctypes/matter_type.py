#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, Optional
from .doctype import Doctype


class MatterType(Doctype):
    """
    Source: /docs/document_store_schema.md Matter Type.
    """

    def __init__(
        self,
        name: str,
        external_source_id: Optional[Any],
        created: datetime
    ):
        self.name = name
        self.external_source_id = external_source_id
        self.created = created

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Doctype:
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
