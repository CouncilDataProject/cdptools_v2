#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from .databases import Database
from .dev_utils import load_custom_object
from .file_stores import FileStore
from .research_utils import transcripts as transcripts_utils


class CDPInstanceConfig:
    def __init__(
        self,
        database_module_path: str,
        database_object_name: str,
        database_object_kwargs: Dict[str, Any],
        file_store_module_path: str,
        file_store_object_name: str,
        file_store_object_kwargs: Dict[str, Any]
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
                self._config.database_object_kwargs
            )

        return self._database

    @property
    def file_store(self) -> FileStore:
        if self._file_store is None:
            self._file_store = load_custom_object.load_custom_object(
                self._config.file_store_module_path,
                self._config.file_store_object_name,
                self._config.file_store_object_kwargs
            )

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
