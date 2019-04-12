#!/usr/bin/env python
# -*- coding: utf-8 -*-

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import logging
from pathlib import Path
from typing import Dict, Union

from .database import Database

###############################################################################

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)4s:%(lineno)4s %(asctime)s] %(message)s'
)
log = logging.getLogger()

###############################################################################


class CloudFirestoreDatabase(Database):

    def __init__(self, credentials_path: Union[str, Path]):
        # Initialize database reference
        cred = credentials.Certificate(str(credentials_path))
        firebase_admin.initialize_app(cred)

        # Store configuration
        self.credentials_path = credentials_path
        self.root = firestore.client()

    def get_event(self, event_id: str) -> Dict:
        # Construct ref
        ref = self.root.collection(u"events").document(event_id)
        log.debug(f"Created reference: {ref}")

        # Attempt get
        return ref.get().to_dict()

    def upload_event(self, event: Dict) -> str:
        # Construct ref
        ref = self.root.collection(u"events").document(event["sha256"])
        log.debug(f"Created reference: {ref}")

        # Remove sha256
        event.pop("sha256")

        # Add created timestamp
        event[u"created_datetime"] = firestore.SERVER_TIMESTAMP

        # Attempt set
        return ref.set(event)

    def get_indexed_words(self) -> Dict[str, Dict]:
        """
        Get all preprocessed words.
        """

        return {}

    def upload_indexed_words(self, words: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Provided a dictionary of dictionaries with {word: {indexing results}} update or add index results for each one.
        """

        return {}

    def get_transcript(self, transcript_id: str) -> str:
        """
        Get a transcript from the transcript id.
        """

        return ""

    def upload_transcript(self, transcript: str) -> str:
        """
        Upload a transcript and return the transcript id.
        """

        return ""

    def __str__(self):
        return f"<FirebaseDatabase [{self.credentials_path}]>"

    def __repr__(self):
        return str(self)
