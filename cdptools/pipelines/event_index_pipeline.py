#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Union

from .. import get_module_version
from ..dev_utils import RunManager
from ..research_utils import transcripts as transcript_tools
from .pipeline import Pipeline, ValuesForTerm

###############################################################################

log = logging.getLogger(__name__)

###############################################################################


class EventIndexPipeline(Pipeline):

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

    def task_generate_index(self, event_corpus_map: Dict[str, Path]) -> Dict[str, Dict[str, float]]:
        """
        Generate word event scores dictionary.
        """
        with RunManager(
            database=self.database,
            file_store=self.file_store,
            algorithm_name="EventIndexPipeline.task_generate_index",
            algorithm_version=get_module_version()
        ):
            return self.indexer.generate_index(event_corpus_map)

    def task_clean_index(self, index: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        """
        Clean the generated index prior to upload.
        """
        with RunManager(
            database=self.database,
            file_store=self.file_store,
            algorithm_name="EventIndexPipeline.task_clean_index",
            algorithm_version=get_module_version()
        ):
            return self.indexer.drop_terms_from_index_below_value(index)

    def _upload_indexed_event_term_event_values(self, evft: ValuesForTerm):
        # Loop through each event and value tied to this term and upload to database
        for event_id, value in evft.values.items():
            self.database.upload_or_update_indexed_event_term(
                term=evft.term,
                event_id=event_id,
                value=value
            )

    def task_upload_index(self, index: Dict[str, Dict[str, float]]):
        """
        Upload a word event scores dictionary. This will completely replace a previous index.
        """
        with RunManager(
            database=self.database,
            file_store=self.file_store,
            algorithm_name="EventIndexPipeline.task_upload_index",
            algorithm_version=get_module_version()
        ):
            # Create upload items
            # This list of objects is just useful for making it easier to multithread the upload
            indexed_event_term_event_values = []
            for term, event_values in index.items():
                indexed_event_term_event_values.append(ValuesForTerm(term, event_values))

            # Multithread the upload/ update of the index
            with ThreadPoolExecutor(self.n_workers) as exe:
                exe.map(self._upload_indexed_event_term_event_values, indexed_event_term_event_values)

    def run(self):
        log.info("Starting index creation.")
        with RunManager(self.database, self.file_store, "EventIndexPipeline.run", get_module_version()):
            # Store the transcripts locally in a temporary directory
            with tempfile.TemporaryDirectory() as tmpdir:
                # Get the event corpus map and download most recent transcripts to local machine
                log.info("Downloading most recent transcripts")
                event_corpus_map = transcript_tools.download_most_recent_transcripts(
                    db=self.database,
                    fs=self.file_store,
                    save_dir=tmpdir
                )

                # Compute word event scores
                log.info("Generating index")
                index = self.task_generate_index(event_corpus_map)

                # Clean the index
                log.info("Dropping event terms with limited value")
                index = self.task_clean_index(index)

            # Upload word event scores
            log.info("Uploading index")
            self.task_upload_index(index)

        log.info("Completed index creation.")
        log.info("=" * 80)
