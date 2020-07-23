#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict
from .doctype import Doctype


class Transcript(Doctype):
    """
    Source: docs/document_store_schema.md Transcript.
    """

    def __init__(
        self,
        event_id: str,
        file_id: str,
        confidence: float,
        created: datetime
    ):
        self._event_id = event_id
        self._file_id = file_id
        self._confidence = confidence
        self._created = created

    @property
    def event_id(self):
        return self._event_id

    @property
    def file_id(self):
        return self._file_id

    @property
    def confidence(self):
        return self._confidence

    @property
    def created(self):
        return self._created

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> Doctype:
        return Transcript(
            event_id = source.get("event_id"),
            file_id = source.get("file_id"),
            confidence = source.get("confidence"),
            created = source.get("created")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "file_id": self.file_id,
            "confidence": self.confidence,
            "created": self.created
        }
