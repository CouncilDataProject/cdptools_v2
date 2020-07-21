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
        self.event_id = event_id
        self.file_id = file_id
        self.confidence = confidence
        self.created = created

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
