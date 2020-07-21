#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, Optional
from .doctype import Doctype


class File(Doctype):
    """
    Source: docs/document_store_schema.md File.
    """

    def __init__(
        self,
        uri: str,
        filename: str,
        description: Optional[str],
        content_type: Optional[str],
        created: datetime
    ):
        self.uri = uri
        self.filename = filename
        self.description = description
        self.content_type = content_type
        self.created = created

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Doctype:
        return File(
            uri = source.get("uri"),
            filename = source.get("filename"),
            description = source.get("description"),
            content_type = source.get("content_type"),
            created = source.get("created")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uri": self.uri,
            "filename": self.filename,
            "description": self.description,
            "content_type": self.content_type,
            "created": self.created
        }
