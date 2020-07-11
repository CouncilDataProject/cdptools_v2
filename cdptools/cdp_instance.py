#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Dict

from .databases import Database
from .dev_utils import load_custom_object
from .file_stores import FileStore


class CDPInstanceConfig:
    def __init__(
        self,
        database_module_path: str,
        database_object_name: str,
        database_object_kwargs: Dict[str, Any],
        file_store_module_path: str,
        file_store_object_name: str,
        file_store_object_kwargs: Dict[str, Any],
    ):
        # Store values
        self.database_module_path = database_module_path
        self.database_object_name = database_object_name
        self.database_object_kwargs = database_object_kwargs
        self.file_store_module_path = file_store_module_path
        self.file_store_object_name = file_store_object_name
        self.file_store_object_kwargs = file_store_object_kwargs


class CDPInstance:
    def __init__(self, config: CDPInstanceConfig):
        # Store config
        self._config = config

        # Lazy loaded initialize
        self._database = None
        self._file_store = None

    @property
    def database(self) -> Database:
        if self._database is None:
            self._database = load_custom_object.load_custom_object(
                self._config.database_module_path,
                self._config.database_object_name,
                self._config.database_object_kwargs,
            )

        return self._database

    @property
    def file_store(self) -> FileStore:
        if self._file_store is None:
            self._file_store = load_custom_object.load_custom_object(
                self._config.file_store_module_path,
                self._config.file_store_object_name,
                self._config.file_store_object_kwargs,
            )

        return self._file_store

    def __str__(self):
        return (
            f"<CDPInstance [database: {self.database}, file_store: {self.file_store}]>"
        )

    def __repr__(self):
        return str(self)
