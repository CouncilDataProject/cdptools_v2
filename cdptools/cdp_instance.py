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

    def get_transcript_manifest(self, order_by_field: str = "confidence") -> pd.DataFrame:
        """
        Get a pandas dataframe that can act as a manifest of a transcript available for each event stored in a CDP
        instance's database.

        Parameters
        ----------
        order_by_field: str
            Which field to order the transcripts by to select the first (highest value) of.
            Default: "confidence"
            Choices: ["created", "confidence"]

        Returns
        -------
        manifest: pandas.DataFrame
            A dataframe where each row has transcript, event, body, and file details for the event at that row.
        """

        return transcripts_utils.get_transcript_manifest(
            db=self.database,
            order_by_field=order_by_field
        )

    def download_transcripts(
        self,
        order_by_field: str = "confidence",
        save_dir: Optional[Path] = None,
    ) -> Dict[str, Path]:
        """
        Download a transcript for each event found in a CDP instance. Additionally saves the manifest as a CSV.

        Parameters
        ----------
        order_by_field: str
            Which field to order the transcripts by to select the first (highest value) of.
            Default: "confidence"
            Choices: ["created", "confidence"]
        save_dir: Optional[Union[str, Path]]
            An optional path of where to save the transcripts and manifest CSV.
            If None provided, uses current directory.
            Always overwrites existing transcripts with the same name if they already exist in the provided directory.

        Returns
        -------
        event_corpus_map: Dict[str, Path]
            A dictionary mapping event id to a local Path for a transcript for that event.
        """

        return transcripts_utils.download_transcripts(
            db=self.database,
            fs=self.file_store,
            order_by_field=order_by_field,
            save_dir=save_dir
        )

    def __str__(self):
        return f"<CDPInstance [database: {self.database}, file_store: {self.file_store}]>"

    def __repr__(self):
        return str(self)
