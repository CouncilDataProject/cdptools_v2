#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, Optional
from .file_base import FileBase


class File(FileBase):
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
        super().__init__(name = filename, uri = uri)
        self._filename = filename
        self._description = description
        self._content_type = content_type
        self._created = created

    @property
    def filename(self):
        return self._filename

    @property
    def description(self):
        return self._description

    @property
    def content_type(self):
        return self._content_type

    @property
    def created(self):
        return self._created

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> FileBase:
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
