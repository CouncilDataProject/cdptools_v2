#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from pathlib import Path
from typing import Union

import nltk
import pandas as pd

from .indexer import Indexer

# Ensure stopwords are downloaded
try:
    from nltk.corpus import stopwords
    STOPWORDS = stopwords.words("english")
except LookupError:
    nltk.download("stopwords")
    from nltk.corpus import stopwords
    STOPWORDS = stopwords.words("english")

###############################################################################

log = logging.getLogger(__name__)

###############################################################################


class TFIDFIndexer(Indexer):

    def __init__(self, max_synchronous_jobs: int = 8, **kwargs):
        # Set state
        self.n_workers = max_synchronous_jobs

    def generate_word_event_scores(self, generate_word_event_scores: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        return {}
