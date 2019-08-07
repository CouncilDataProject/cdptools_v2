#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from typing import Any, Dict, Optional, Type

import pandas as pd

from . import databases, file_stores
from .research_utils import transcripts as transcripts_utils


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

    def get_most_recent_transcript_manifest(self) -> pd.DataFrame:
        """
        Get a pandas dataframe that can act as a manifest of the most recent transcript available for each
        event stored in a CDP instance's database.

        Returns
        -------
        manifest: pandas.DataFrame
            A dataframe with transcript, event, body, and file details where each row is the
            most recent transcript for the event of that row.
        """
        return transcripts_utils.get_most_recent_transcript_manifest(self.database)

    def download_most_recent_transcripts(self, save_dir: Optional[Path] = None) -> Dict[str, Path]:
        """
        Download the most recent versions of event transcripts.

        Parameters
        ----------
        save_dir: Optional[Union[str, Path]]
            An optional path of where to save the transcripts and manifest CSV.
            If None provided, uses current directory.
            Always overwrites existing transcripts with the same name if they already exist in the provided directory.

        Returns
        -------
        event_corpus_map: Dict[str, Path]
            A dictionary mapping event id to local Path of the most recent transcript for that event.
        """
        return transcripts_utils.download_most_recent_transcripts(self.database, self.file_store, save_dir)

    def __str__(self):
        return f"<CDPInstance [database: {self.database}, file_store: {self.file_store}]>"

    def __repr__(self):
        return str(self)


# City instances
seattle = _CDPInstance(
    database_type=databases.CloudFirestoreDatabase,
    database_config={"project_id": "cdp-seattle"},
    file_store_type=file_stores.GCSFileStore,
    file_store_config={"bucket_name": "cdp-seattle.appspot.com"}
)
