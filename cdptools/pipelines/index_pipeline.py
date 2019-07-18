#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import json
import logging
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .. import get_module_version
from ..utils import RunManager, research_utils
from .pipeline import Pipeline

###############################################################################

log = logging.getLogger(__name__)

###############################################################################


class IndexPipeline(Pipeline):

    def __init__(self, config_path: Union[str, Path]):
        # Resolve config path
        config_path = config_path.resolve(strict=True)

        # Read
        with open(config_path, "r") as read_in:
            self.config = json.load(read_in)

        # Get workers
        self.n_workers = self.config.get("max_synchronous_jobs")

        # Load modules
        self.database = self.load_custom_object(
            module_path=self.config["database"]["module_path"],
            object_name=self.config["database"]["object_name"],
            object_kwargs={**self.config["database"].get("object_kwargs", {})}
        )
        self.file_store = self.load_custom_object(
            module_path=self.config["file_store"]["module_path"],
            object_name=self.config["file_store"]["object_name"],
            object_kwargs=self.config["file_store"].get("object_kwargs", {})
        )
        self.indexer = self.load_custom_object(
            module_path=self.config["indexer"]["module_path"],
            object_name=self.config["indexer"]["object_name"],
            object_kwargs=self.config["indexer"].get("object_kwargs", {})
        )

    def task_generate_word_event_scores(self, transcript_manifest: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """
        Generate word event scores dictionary.
        """
        with RunManager(
            database=self.database,
            file_store=self.file_store,
            algorithm_name="IndexPipeline.task_generate_word_event_scores",
            algorithm_version=get_module_version()
        ):
            return self.indexer.generate_word_event_scores(transcript_manifest)

    def task_upload_word_event_scores(self, word_event_scores: Dict[str, Dict[str, float]]):
        """
        Upload a word event scores dictionary. This will completely replace a previous index.
        """
        with RunManager(
            database=self.database,
            file_store=self.file_store,
            algorithm_name="IndexPipeline.task_upload_word_event_scores",
            algorithm_version=get_module_version()
        ):
            return

    def run(self):
        log.info("Starting index creation.")
        with RunManager(self.database, self.file_store, "IndexPipeline.run", get_module_version()):
            # Get transcript manifest
            with RunManager(
                database=self.database,
                file_store=self.file_store,
                algorithm_name="cdptools.utils.research_utils.get_most_recent_transcript_manifest",
                algorithm_version=get_module_version()
            ):
                transcript_manifest = research_utils.get_most_recent_transcript_manifest(db=self.database)

            # Compute word event scores
            word_event_scores = self.task_generate_word_event_scores(transcript_manifest)

            # Upload word event scores
            self.task_upload_word_event_scores(word_event_scores)


        log.info("Completed index creation.")
        log.info("=" * 80)
