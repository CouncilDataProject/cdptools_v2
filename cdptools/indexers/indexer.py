#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Union

import pandas as pd

###############################################################################


class Indexer(ABC):
    """
    Why is this not just a single function?

    Like audio splitters, to pass arguments to the instance of the class and retain state may be useful. In this case,
    while computing the scores for every meeting memory may be a constrant, or in the case where a developer wants to
    artifically inflate the scores for certain events or words to highlight something that can be done on an object
    instance rather than just a function instance.
    """

    @abstractmethod
    def generate_word_event_scores(self, transcript_manifest: pd.DataFrame, **kwargs) -> Dict[str, Dict[str, float]]:
        """
        Given a transcript manifest (cdptools.utils.research_utils.get_most_recent_transcript_manifest),
        compute word event scores that will act as a search index.

        Parameters
        ----------
        transcript_manifest: pandas.DataFrame
            A manifest of the most recent primary transcript for each event stored in the CDP instance.
            Created from cdptools.utils.research_utils.get_most_recent_transcript_manifest

        Returns
        -------
        word_event_scores: Dict[str, Dict[str, float]]
            A dictionary of scores per word per event that will be stored in the CDP instance's database and used as a
            method for searching for events.

            Example:
            ```json
            {
                "hello": {
                    "15ce0a20-3688-4ebd-bf3f-24f6e8d12ad9": 12.3781,
                    "3571c871-6f7d-41b5-85d1-ced0589f9220": 56.7922,
                },
                "world": {
                    "15ce0a20-3688-4ebd-bf3f-24f6e8d12ad9": 8.0016,
                    "3571c871-6f7d-41b5-85d1-ced0589f9220": 33.9152,
                }
            }
            ```
        """

        return {}
