#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict


class Doctype(ABC):
    """
    Doctype is a schema as a class.
    Source: docs/document_store_schema.md.
    """

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> object:
        """
        Convert schema dict to custom object.
        """
        return object()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert custom object to schema dict.
        """
        return {}
