#!/usr/bin/env python
# -*- coding: utf-8 -*-

from unittest import mock

import pytest
from firebase_admin import firestore
from google.cloud import storage

from cdptools.databases.cloud_firestore_database import CloudFirestoreDatabase
from cdptools.file_stores.gcs_file_store import GCSFileStore
from cdptools.indexers.tfidf_indexer import TFIDFIndexer
from cdptools.pipelines import EventIndexPipeline

from ..databases.test_cloud_firestore_database import MockedCollection
from ..file_stores.test_gcs_file_store import MockedBlob, MockedBucket


@pytest.fixture
def empty_creds_db() -> CloudFirestoreDatabase:
    with mock.patch(
        "cdptools.databases.cloud_firestore_database.CloudFirestoreDatabase._initialize_creds_db"
    ):
        db = CloudFirestoreDatabase("/fake/path/to/creds.json")
        db._credentials_path = "/fake/path/to/creds.json"
        db._root = mock.Mock(firestore.Client)
        db._root.collection.return_value = MockedCollection([])

        return db


@pytest.fixture
def empty_creds_fs() -> GCSFileStore:
    with mock.patch(
        "cdptools.file_stores.gcs_file_store.GCSFileStore._initialize_creds_fs"
    ):
        fs = GCSFileStore("/fake/path/to/creds.json")
        fs._credentials_path = "/fake/path/to/creds.json"
        fs._client = mock.Mock(storage.Client)
        fs._bucket = MockedBucket(
            "fake_bucket", [MockedBlob("example.mp4", exists=False)]
        )

        return fs


@pytest.fixture
def example_config(data_dir):
    return data_dir / "example_index_pipeline_config.json"


@pytest.fixture
def example_transcript_sentences_0(data_dir):
    return data_dir / "example_transcript_sentences.json"


@pytest.fixture
def example_transcript_sentences_1(data_dir):
    return data_dir / "example_transcript_sentences_1.json"


def test_event_index_pipeline(
    empty_creds_db,
    empty_creds_fs,
    example_config,
    example_transcript_sentences_0,
    example_transcript_sentences_1,
):
    # Configure all mocks
    with mock.patch(
        "cdptools.dev_utils.load_custom_object.load_custom_object"
    ) as mock_loader:
        mock_loader.side_effect = [empty_creds_db, empty_creds_fs, TFIDFIndexer()]

        # Initialize pipeline
        pipeline = EventIndexPipeline(example_config)

        # Mock the transcript manifest get
        with mock.patch(
            "cdptools.research_utils.transcripts.download_transcripts"
        ) as mock_transcript_get:
            mock_transcript_get.return_value = {
                "event_0": example_transcript_sentences_0,
                "event_1": example_transcript_sentences_1,
            }

            pipeline.run()
