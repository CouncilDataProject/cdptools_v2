#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

import pandas as pd

from .indexer import Indexer

###############################################################################

log = logging.getLogger(__name__)

###############################################################################


class TFIDFIndexer(Indexer):

    def __init__(self, max_synchronous_jobs: int = 8, **kwargs):
        # Set state
        self.n_workers = max_synchronous_jobs

    @staticmethod
    def count_unique_words(cleaned_transcript_text: str):
        return {}

    def generate_word_event_scores(self, generate_word_event_scores: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        # Instead of using sklearn CountVectorizer/ TfidfVectorizer, we want to do this one transcript at a time
        # to save on memory and storage of the running machine
        # with ThreadPoolExecutor(max_workers=self.n_workers) as exe:
        #     pass

        return {}
