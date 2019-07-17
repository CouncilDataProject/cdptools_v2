#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import json
import logging
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import nltk

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

        # Load event scraper
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

        # Ensure stopwords are downloaded
        try:
            from nltk.corpus import stopwords
            stopwords = stopwords.words("english")
        except LookupError:
            nltk.download("stopwords")
            from nltk.corpus import stopwords
            stopwords = stopwords.words("english")

    def task_create_word_frequencies(self) -> Dict[str, Dict[str, int]]:
        """
        Generate a dictionary of word -> {event: count} for all words and all events.

        We could use sklearn CountVectorizer/ TfIdfVectorizer but because this happens on a server with minimal memory
        and local storage we do this one event at a time.
        """
        with RunManager(
            database=self.database,
            file_store=self.file_store,
            algorithm_name="IndexPipeline.task_create_word_frequencies",
            algorithm_version=get_module_version()
        ):
            # Pull most recent transcript manifest for events
            transcript_manifest = research_utils.get_most_recent_transcript_manifest(self.database)

            # Construct word frequencies per event
            # {
            #   word: {
            #       event: frequency,
            #       event: frequency
            #   },
            #   word: {
            #       event: frequency,
            #       event: frequency
            #   }
            # }
            word_frequencies = {}
            # for i, row in transcript_manifest.iterrows()

            return word_frequencies

    def run(self):
        # Get events
        log.info("Starting index creation.")
        with RunManager(self.database, self.file_store, "IndexPipeline.run", get_module_version(), remove_files=True):
            pass

        log.info("Completed event processing.")
        log.info("=" * 80)
