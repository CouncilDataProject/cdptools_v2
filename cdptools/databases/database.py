#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from typing import Dict

###############################################################################


class Database(ABC):

    @abstractmethod
    def upload_event(self, event: Dict) -> str:
        """
        Upload an event dictionary and return the event id.
        """

        return ""

    @abstractmethod
    def get_event(self, event_id: str) -> Dict:
        """
        Get an event dictionary from the event id.
        """

        return {}

    @abstractmethod
    def get_indexed_words(self) -> Dict[str, Dict]:
        """
        Get all preprocessed words.
        """

        return {}

    @abstractmethod
    def upload_indexed_words(self, words: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Provided a dictionary of dictionaries with {word: {indexing results}} update or add index results for each one.
        """

        return {}

    @abstractmethod
    def get_transcript(self, transcript_id: str) -> Dict:
        """
        Get a transcript from the transcript id.
        """

        return ""

    @abstractmethod
    def upload_transcript(self, transcript: str) -> str:
        """
        Upload a transcript and return the transcript id.
        """

        return ""
