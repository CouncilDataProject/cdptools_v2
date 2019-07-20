#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import string
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Union

from nltk.stem import PorterStemmer

# Ensure stopwords are downloaded
try:
    from nltk.corpus import stopwords
    STOPWORDS = stopwords.words("english")
except LookupError:
    import nltk
    nltk.download("stopwords")
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
            cleaned_transcript[-1] == cleaned_transcript[:-1]

        # Clean words by stems
        words = cleaned_transcript.split(" ")
        stemmed = []
        ps = PorterStemmer()
        for word in words:
            stemmed.append(ps.stem(word))

        # Rejoin transcript
        cleaned_transcript = " ".join(stemmed)

        return cleaned_transcript

    @abstractmethod
    def generate_word_event_scores(self, event_corpus_map: Dict[str, str], **kwargs) -> Dict[str, Dict[str, float]]:
        """
        Given an event corpus map, compute word event scores that will act as a search index.

        Parameters
        ----------
        event_corpus_map: Dict[str, str]
            A dictionary that maps event id to a local path with transcript to use for indexing.

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
