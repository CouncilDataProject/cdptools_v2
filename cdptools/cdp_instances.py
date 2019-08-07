#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Dict, Type

from . import databases, file_stores


class _CDPInstance:
    def __init__(
        self,
        database_type: Type,
        database_config: Dict[str, Any],
        file_store_type: Type,
        file_store_config: Dict[str, Any]
    ):
        # Store types and lambdas
        self._database_type = database_type
        self._database_config = database_config
        self._file_store_type = file_store_type
        self._file_store_config = file_store_config

        # Lazy loaded initialize
        self._database = None
        self._file_store = None

    @property
    def database(self) -> databases.Database:
        if self._database is None:
            self._database = self._database_type(**self._database_config)

        return self._database

    @property
    def file_store(self) -> file_stores.FileStore:
        if self._file_store is None:
            self._file_store = self._file_store_type(**self._file_store_config)

        return self._file_store


# City instances
Seattle = _CDPInstance(
    database_type=databases.CloudFirestoreDatabase,
    database_config={"project_id": "stg-cdp-seattle"},
    file_store_type=file_stores.GCSFileStore,
    file_store_config={"bucket_name": "stg-cdp-seattle.appspot.com"}
)
