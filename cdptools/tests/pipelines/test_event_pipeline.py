#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import pytest
from unittest import mock

from firebase_admin import firestore
from google.cloud import storage

from cdptools.audio_splitters.ffmpeg_audio_splitter import FFmpegAudioSplitter
from cdptools.databases.cloud_firestore_database import CloudFirestoreDatabase
from cdptools.event_scrapers.seattle_event_scraper import SeattleEventScraper
from cdptools.file_stores.gcs_file_store import GCSFileStore
from cdptools.pipelines import EventPipeline
from cdptools.sr_models.google_cloud_sr_model import GoogleCloudSRModel, SRModelOutputs

from ..databases.test_cloud_firestore_database import MockedCollection
from ..file_stores.test_gcs_file_store import MockedBlob, MockedBucket


@pytest.fixture
def example_video(data_dir) -> Path:
    return data_dir / "example_video.mp4"


@pytest.fixture
def example_config(data_dir) -> Path:
    return data_dir / "example_event_pipeline_config.json"


@pytest.fixture
def example_transcript_raw(data_dir) -> Path:
    return data_dir / "example_transcript_raw.txt"


@pytest.fixture
def example_transcript_words(data_dir) -> Path:
    return data_dir / "example_transcript_words.json"


@pytest.fixture
def example_transcript_sentences(data_dir) -> Path:
    return data_dir / "example_transcript_sentences.json"


@pytest.fixture
def empty_creds_db() -> CloudFirestoreDatabase:
    with mock.patch("cdptools.databases.cloud_firestore_database.CloudFirestoreDatabase._initialize_creds_db"):
        db = CloudFirestoreDatabase("/fake/path/to/creds.json")
        db._credentials_path = "/fake/path/to/creds.json"
        db._root = mock.Mock(firestore.Client)
        db._root.collection.return_value = MockedCollection([])

        return db


@pytest.fixture
def empty_creds_fs() -> GCSFileStore:
    with mock.patch("cdptools.file_stores.gcs_file_store.GCSFileStore._initialize_creds_fs"):
        fs = GCSFileStore("/fake/path/to/creds.json")
        fs._credentials_path = "/fake/path/to/creds.json"
        fs._client = mock.Mock(storage.Client)
        fs._bucket = MockedBucket("fake_bucket", [MockedBlob("example.mp4", exists=False)])

        return fs


@pytest.fixture
def mocked_sr_model(
    example_transcript_raw,
    example_transcript_words,
    example_transcript_sentences
) -> GoogleCloudSRModel:
    # Create basic sr model
    # It doesn't matter what file is put in the init as long as it's a file
    # The speech client is configured during the transcribe function
    mocked_model = mock.Mock(GoogleCloudSRModel(example_transcript_raw))
    mocked_model.transcribe.return_value = SRModelOutputs(
        example_transcript_raw,
        12.0,
        example_transcript_words,
        example_transcript_sentences
    )


def test_event_pipeline(
    empty_creds_db,
    empty_creds_fs,
    mocked_sr_model,
    example_config,
    example_video
):
    # Configure all mocks
    with mock.patch("cdptools.pipelines.pipeline.Pipeline.load_custom_object") as mock_loader:
        mock_loader.side_effect = [
            SeattleEventScraper(), empty_creds_db, empty_creds_fs, FFmpegAudioSplitter(), mocked_sr_model
        ]

        # Initialize pipeline
        pipeline = EventPipeline(example_config)

        print(pipeline.event_scraper)
        print(pipeline.database)
        print(pipeline.file_store)
        print(pipeline.audio_splitter)
        print(pipeline.sr_model)
