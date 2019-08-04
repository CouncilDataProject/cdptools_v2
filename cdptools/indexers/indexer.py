#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import re
import string
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Union

from nltk.stem import PorterStemmer

###############################################################################

log = logging.getLogger(__name__)

# Ensure stopwords are downloaded
try:
    from nltk.corpus import stopwords
    STOPWORDS = stopwords.words("english")
except LookupError:
    import nltk
    nltk.download("stopwords")
    log.info("Downloaded nltk stopwords")
    from nltk.corpus import stopwords
    STOPWORDS = stopwords.words("english")

###############################################################################


class Indexer(ABC):
    """
    Why is this not just a single function?

    Like audio splitters, to pass arguments to the instance of the class and retain state may be useful. In this case,
    while computing the scores for every meeting memory may be a constrant, or in the case where a developer wants to
    artifically inflate the scores for certain events or words to highlight something that can be done on an object
    instance rather than just a function instance.
    """

    @staticmethod
    def get_raw_transcript(transcipt_path: Union[str, Path]) -> str:
        """
        Attempts to open either a raw or annotated json transcript format and return the raw transcript as a string.
        If the file format is not supported or if the data contained in the transcript does not follow the specification
        a TypeError is raised.

        Parameters
        ----------
        transcipt_path: Union[str, Path]
            Path to the transcript

        Returns
        -------
        transcript: str
            The raw text of the opened transcript.
        """
        # Enforce path
        transcipt_path = Path(transcipt_path).expanduser().resolve(strict=True)

        # Check that the transcript follows a known format
        if transcipt_path.suffix == ".json":
            with open(transcipt_path, "r") as read_in:
                transcript = json.load(read_in)

            # Join all text items into a single string
            try:
                transcript = " ".join([portion["text"] for portion in transcript["data"]])
            except KeyError:
                raise TypeError(
                    f"Unsure how to handle annotated JSON transcript provided: {transcipt_path}"
                    f"Please refer to the `transcript_formats.md` file in the documentation for details."
                )

        # Raise error for all other file formats
        else:
            raise TypeError(
                f"Unsure how to handle transcript file format: {transcipt_path}"
                f"Please refer to the `transcript_formats.md` file in the documentation for details."
            )

        return transcript

    @staticmethod
    def clean_text_for_indexing(raw_transcript: str) -> str:
        """
        Run basic cleaning operations against the raw text of the transcript.

        Parameters
        ----------
        raw_transcript: str
            The raw text of a transcript as a single string.

        Returns
        -------
        cleaned_transcript: str
            The cleaned version of the transcript text.
        """
        # Send to lowercase
        cleaned_transcript = raw_transcript.lower()

        # Remove new line and tab characters
        cleaned_transcript = cleaned_transcript.replace("\n", " ").replace("\t", " ")

        # Remove punctuation
        cleaned_transcript = re.sub(f"[{re.escape(string.punctuation)}]", "", cleaned_transcript)

        # Remove stopwords
        joined_stopwords = "|".join(STOPWORDS)
        cleaned_transcript = re.sub(r"\b("+joined_stopwords+r")\b", "", cleaned_transcript)

        # Remove gaps in string
        cleaned_transcript = re.sub(r" {2,}", " ", cleaned_transcript)
        if cleaned_transcript[0] == " ":
            cleaned_transcript = cleaned_transcript[1:]
        if cleaned_transcript[-1] == " ":
            cleaned_transcript = cleaned_transcript[:-1]

        # Clean words by stems
        words = cleaned_transcript.split(" ")
        stemmed = []
        ps = PorterStemmer()
        for word in words:
            stemmed.append(ps.stem(word))

        # Rejoin transcript
        cleaned_transcript = " ".join(stemmed)

        return cleaned_transcript

    @staticmethod
    def drop_terms_from_index_below_value(
        index: Dict[str, Dict[str, float]],
        minimum_value_allowed: float = 0.0
    ) -> Dict[str, Dict[str, float]]:
        """
        Drop any terms from an index that have a value less than or equal to the provided.

        Parameters
        ----------
        index: Dict[str, Dict[str, float]]
            An index dictionary, the output of an `Indexer.generate_index` run.

        minimum_value_allowed: float
            The float value that all term event values should be compared against. Any term event value less than or
            equal to the received value will be dropped from the index.

        Returns
        -------
        cleaned_index: Dict[str, Dict[str, float]]
            The cleaned index that has had values removed based off the received minimum value allowed.
        """
        cleaned = {}
        dropped_count = 0
        # For each term in the index
        for term in index:
            # For each event value given to that term
            for event_id, value in index[term].items():
                # If the value is strictly greater than the minimum value allowed
                if value > minimum_value_allowed:
                    # If the term is already in the cleaned index, add the event and value as a new pair
                    if term in cleaned:
                        cleaned[term][event_id] = value
                    # If the term is not already in the cleaned index, add a new dictionary to store the pair
                    else:
                        cleaned[term] = {event_id: value}
                else:
                    dropped_count += 1

        log.debug(f"Dropped {dropped_count} terms during index cleaning")
        return cleaned

    @abstractmethod
    def generate_index(self, event_corpus_map: Dict[str, Path], **kwargs) -> Dict[str, Dict[str, float]]:
        """
        Given an event corpus map, compute word event values that will act as a search index.

        Parameters
        ----------
        event_corpus_map: Dict[str, str]
            A dictionary that maps event id to a local path with transcript to use for indexing.

        Returns
        -------
        word_event_scores: Dict[str, Dict[str, float]]
            A dictionary of values per event per word that will be stored in the CDP instance's database and used as a
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
