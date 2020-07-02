#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import re
import string
from abc import ABC, abstractmethod
from collections import deque
from pathlib import Path
from typing import Dict, List, Union

from nltk.stem import PorterStemmer
from tika import parser

from ..sr_models.constants import TranscriptFormats
from . import exceptions

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

    Like audio splitters, to pass arguments to the instance of the class and retain
    state may be useful. In this case, while computing the scores for every meeting
    memory may be a constrant, or in the case where a developer wants to artifically
    inflate the scores for certain events or words to highlight something that can be
    done on an object instance rather than just a function instance.
    """

    @staticmethod
    def get_raw_transcript(transcript_path: Union[str, Path]) -> str:
        """
        Attempts to open either a raw or annotated json transcript format and return
        the raw transcript as a string. If the file format is not supported or if the
        data contained in the transcript does not follow the specification a TypeError
        is raised.

        Parameters
        ----------
        transcript_path: Union[str, Path]
            Path to the transcript

        Returns
        -------
        transcript: str
            The raw text of the opened transcript.
        """
        # Enforce path
        transcript_path = Path(transcript_path).expanduser().resolve(strict=True)

        # Check that the transcript follows a known format
        if transcript_path.suffix == ".json":
            with open(transcript_path, "r") as read_in:
                transcript = json.load(read_in)

            # Join all text items into a single string
            try:
                # Handle simple transcripts
                if transcript["format"] in [
                    TranscriptFormats.raw,
                    TranscriptFormats.timestamped_words,
                    TranscriptFormats.timestamped_sentences,
                ]:
                    transcript = " ".join(
                        [portion["text"] for portion in transcript["data"]]
                    )
                # Handle speaker turns transcripts
                elif (
                    transcript["format"] == TranscriptFormats.timestamped_speaker_turns
                ):
                    text_blocks = []
                    for speaker_turn in transcript["data"]:
                        for portion in speaker_turn["data"]:
                            text_blocks.append(portion["text"])
                    transcript = " ".join(text_blocks)
                else:
                    raise exceptions.UnrecognizedTranscriptFormatError(transcript_path)

            # Catch any errors
            except (KeyError, exceptions.UnrecognizedTranscriptFormatError):
                raise exceptions.UnrecognizedTranscriptFormatError(transcript_path)

        # Raise error for all other file formats
        else:
            raise exceptions.UnrecognizedTranscriptFormatError(transcript_path)

        return transcript

    @staticmethod
    def get_text_from_file(path: Union[str, Path]) -> str:
        # Ensure path exists
        path = Path(path).resolve(strict=True)

        # Parse
        parsed = parser.from_file(str(path))

        # Sometimes the content isn't a supported type by tika 🤷
        return parsed.get("content", None)

    @staticmethod
    def term_is_end_of_sentence(term: str) -> bool:
        """
        Does the term provided mark the end of a sentence.

        Parameters
        ----------
        term: str
            The term to check for end of sentence punctuation characters
            (".", "!", and "?").

        Returns:
        --------
        is_end_of_sentence: bool
            The boolean value indicating whether or not an end of sentence punctuation
            character was found in the term.
        """
        return any(punc in term for punc in [".", "!", "?"])

    @staticmethod
    def get_context_span_for_index(
        terms: List[str], index: int, max_span_size: int = 10
    ) -> str:
        """
        Get the contextual sentence information for an index given an ordered list of
        terms.

        Parameters
        ----------
        terms: List[str]
            The ordered list of terms to use for contextual information.
        index: int
            The index to use as the starting point for exploration for contextual
            sentence terms.
        max_span_size: int
            The max contextual span size.
            Default: 10

        Returns
        -------
        span: str
            The contextual sentence span surrounding the index provided.

        Example
        -------
        ```
        get_context_span_for_index(
            terms=[
                "Hello",
                "and",
                "good",
                "morning."
            ],
            index=0
        )

        >> "Hello and good morning."
        ```

        ```
        get_context_span_for_index(
            terms=[
                "But",
                "I",
                "don't",
                "think",
                "the",
                "barrier",
                "is",
                "so",
                "high",
                "to",
                "allow",
                "individuals",
                "to",
                "use",
                "the",
                "service."
            ],
            index=0
        )

        >> "But I don't think the barrier is so high to ..."
        ```

        ```
        get_context_span_for_index(
            terms=[
                "But",
                "I",
                "don't",
                "think",
                "the",
                "barrier",
                "is",
                "so",
                "high",
                "to",
                "allow",
                "individuals",
                "to",
                "use",
                "the",
                "service."
            ],
            index=6
        )

        >> "... I don't think the barrier is so high to allow ..."
        ```

        """
        # Check index provided
        if index < 0:
            raise IndexError(
                "For simplicity's sake, we don't support negative index context span "
                "retrieval. Sorry."
            )

        # Window to store valid terms in
        window = deque()
        window.append(terms[index])

        # Check if the current term is the last in the sentence already
        if Indexer.term_is_end_of_sentence(terms[index]):
            right_side_valid = False
        else:
            right_side_valid = True
            right_side_index = index + 1

        # We can always check left side initially
        left_side_valid = True
        left_side_index = index - 1
        current_exploration_direction = "left"

        # Keep appending items to the window until it his max_span_size and both sides
        # are still valid
        while len(window) < max_span_size and (left_side_valid or right_side_valid):
            # If the current exploration direction is leftwards and the left side is
            # still valid, check the left term
            if current_exploration_direction == "left" and left_side_valid:
                # If the term is the end of the prior sentence, mark the current
                # position as no longer valid to explore
                # Also catch if we have hit the beginning of the terms
                if (
                    Indexer.term_is_end_of_sentence(terms[left_side_index])
                    or left_side_index < 0
                ):
                    left_side_valid = False
                # It wasn't the end of the prior sentence so we can append the term to
                # the window
                else:
                    window.appendleft(terms[left_side_index])
                    left_side_index -= 1

            # If the current exploration direction wasn't leftwards, we must be going
            # right
            # Check if right side is still valid
            elif right_side_valid:
                # Check if the right_side_index is greater than or equal to the len of
                # the term list
                if right_side_index >= len(terms):
                    right_side_valid = False

                # If the term is the end of the sentence, append it and mark right side
                # as no longer valid
                elif (
                    Indexer.term_is_end_of_sentence(terms[right_side_index])
                    or right_side_index >= len(terms) - 1
                ):
                    window.append(terms[right_side_index])
                    right_side_valid = False
                # If the term wasn't the end of the sentence, append it and move the
                # index
                else:
                    window.append(terms[right_side_index])
                    right_side_index += 1

            # Rotate which direction we were exploring
            # If we were heading left and the right side is valid, explore right
            # We do this because if we were provided an index that is completely in the
            # center of a long sentence we want a balanced context string
            if current_exploration_direction == "left" and right_side_valid:
                current_exploration_direction = "right"
            # Otherwise we were heading right, set to explore left
            else:
                current_exploration_direction = "left"

        # We hit max span size or captured a full sentence
        if left_side_valid:
            window.appendleft("...")
        if right_side_valid:
            window.append("...")

        return " ".join(window)

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
        cleaned_transcript = re.sub(
            f"[{re.escape(string.punctuation)}]", "", cleaned_transcript
        )

        # Remove stopwords
        joined_stopwords = "|".join(STOPWORDS)
        cleaned_transcript = re.sub(
            r"\b(" + joined_stopwords + r")\b", "", cleaned_transcript
        )

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
    def clean_doc(raw_doc: str) -> str:
        """
        Run basic cleaning operations against the raw text of a document.

        Parameters
        ----------
        raw_doc: str
            The raw text of a document as a single string.

        Returns
        -------
        cleaned_doc: str
            The cleaned version of the text.
        """
        # Remove new line and tab characters
        cleaned_doc = raw_doc.replace("\n", " ").replace("\t", " ")

        # Remove punctuation except periods
        cleaned_doc = re.sub(f"[{re.escape(string.punctuation)}]", "", cleaned_doc)

        # Remove stopwords
        joined_stopwords = "|".join(STOPWORDS)
        cleaned_doc = re.sub(
            r"\b(" + joined_stopwords + r")\b", "", cleaned_doc
        )

        # Remove gaps in string
        try:
            cleaned_doc = re.sub(r" {2,}", " ", cleaned_doc)
            if cleaned_doc[0] == " ":
                cleaned_doc = cleaned_doc[1:]
            if cleaned_doc[-1] == " ":
                cleaned_doc = cleaned_doc[:-1]

        # IndexError occurs when the string was cleaned and it contained entirely stop
        # words or punctuation for some reason
        except IndexError:
            return None

        return cleaned_doc

    @staticmethod
    def drop_terms_from_index_below_value(
        index: Dict[str, Dict[str, float]], minimum_value_allowed: float = 0.0
    ) -> Dict[str, Dict[str, float]]:
        """
        Drop any terms from an index that have a value less than or equal to the
        provided.

        Parameters
        ----------
        index: Dict[str, Dict[str, float]]
            An index dictionary, the output of an `Indexer.generate_index` run.

        minimum_value_allowed: float
            The float value that all term event values should be compared against. Any
            term event value less than or equal to the received value will be dropped
            from the index.

        Returns
        -------
        cleaned_index: Dict[str, Dict[str, float]]
            The cleaned index that has had values removed based off the received
            minimum value allowed.
        """
        cleaned = {}
        dropped_count = 0
        # For each term in the index
        for term in index:
            # For each event value given to that term
            for event_id, value in index[term].items():
                # If the value is strictly greater than the minimum value allowed
                if value > minimum_value_allowed:
                    # If the term is already in the cleaned index, add the event and
                    # value as a new pair
                    if term in cleaned:
                        cleaned[term][event_id] = value
                    # If the term is not already in the cleaned index, add a new
                    # dictionary to store the pair
                    else:
                        cleaned[term] = {event_id: value}
                else:
                    dropped_count += 1

        log.debug(f"Dropped {dropped_count} terms during index cleaning")
        return cleaned

    @abstractmethod
    def generate_index(
        self, event_corpus_map: Dict[str, Path], **kwargs
    ) -> Dict[str, Dict[str, float]]:
        """
        Given an event corpus map, compute word event values that will act as a search
        index.

        Parameters
        ----------
        event_corpus_map: Dict[str, str]
            A dictionary that maps event id to a local path with transcript to use for
            indexing.

        Returns
        -------
        word_event_scores: Dict[str, Dict[str, float]]
            A dictionary of values per event per word that will be stored in the CDP
            instance's database and used as a method for searching for events.

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
