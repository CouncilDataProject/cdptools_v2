#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from pathlib import Path
from typing import Union
from unittest import mock

import pytest
from firebase_admin import firestore
from google.cloud import storage

from cdptools.audio_splitters.ffmpeg_audio_splitter import FFmpegAudioSplitter
from cdptools.databases.cloud_firestore_database import CloudFirestoreDatabase
from cdptools.event_scrapers.seattle_event_scraper import SeattleEventScraper
from cdptools.file_stores.gcs_file_store import GCSFileStore
from cdptools.pipelines import EventPipeline
from cdptools.sr_models.google_cloud_sr_model import (GoogleCloudSRModel,
                                                      SRModelOutputs)

from ..databases.test_cloud_firestore_database import MockedCollection
from ..file_stores.test_gcs_file_store import MockedBlob, MockedBucket


@pytest.fixture
def example_video(data_dir) -> Path:
    return data_dir / "example_video.mp4"


@pytest.fixture
def example_audio(data_dir) -> Path:
    return data_dir / "example_audio.wav"


@pytest.fixture
def example_config(data_dir) -> Path:
    return data_dir / "example_event_pipeline_config.json"


@pytest.fixture
def example_transcript_raw(data_dir) -> Path:
    return data_dir / "example_transcript_raw.json"


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
def mocked_splitter(example_audio) -> FFmpegAudioSplitter:
    mocked_splitter = mock.Mock(FFmpegAudioSplitter())
    mocked_splitter.split.return_value = example_audio
    return mocked_splitter


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
        99.0,
        example_transcript_words,
        example_transcript_sentences
    )

    return mocked_model


@pytest.fixture
def example_seattle_routes(data_dir):
    return data_dir / "example_seattle_routes.html"


@pytest.fixture
def example_seattle_route(data_dir):
    return data_dir / "example_seattle_route.html"


@pytest.fixture
def example_legistar_tools_events(data_dir):
    return data_dir / "example_legistar_tools_events.json"


@pytest.fixture
def example_legistar_tools_event_items_0(data_dir):
    return data_dir / "example_legistar_tools_event_items_0.json"


@pytest.fixture
def example_legistar_tools_event_items_1(data_dir):
    return data_dir / "example_legistar_tools_event_items_1.json"


@pytest.fixture
def example_legistar_tools_event_item_vote(data_dir):
    return data_dir / "example_legistar_tools_event_item_vote.json"


class RequestReturn:
    def __init__(self, content: Union[str, Path]):
        if isinstance(content, Path):
            with open(content, "r") as read_in:
                if content.suffix == ".json":
                    content = json.load(read_in)
                else:
                    content = read_in.read()

        self.content = content

    def raise_for_status(self):
        pass

    def json(self):
        return self.content


def test_event_pipeline_no_backfill(
    empty_creds_db,
    empty_creds_fs,
    mocked_sr_model,
    example_config,
    example_seattle_routes
):
    # Configure all mocks
    with mock.patch("cdptools.pipelines.pipeline.Pipeline.load_custom_object") as mock_loader:
        mock_loader.side_effect = [
            SeattleEventScraper(), empty_creds_db, empty_creds_fs, FFmpegAudioSplitter(), mocked_sr_model
        ]

        # Initialize pipeline
        pipeline = mock.Mock(EventPipeline(example_config))

        with mock.patch("requests.get") as mock_requests:
            # No backfill means only routes will be gathered because example html file only includes past events.
            mock_requests.side_effect = [RequestReturn(example_seattle_routes)]

            pipeline.run()

            # This should never be ran because example html files only include past events.
            pipeline.process_event.assert_not_called()


def test_event_pipeline_with_backfill(
    empty_creds_db,
    empty_creds_fs,
    mocked_splitter,
    mocked_sr_model,
    example_config,
    example_seattle_routes,
    example_seattle_route,
    example_legistar_tools_events,
    example_legistar_tools_event_items_0,
    example_legistar_tools_event_items_1,
    example_legistar_tools_event_item_vote,
    example_video
):
    # Configure all mocks
    with mock.patch("cdptools.pipelines.pipeline.Pipeline.load_custom_object") as mock_loader:
        mock_loader.side_effect = [
            SeattleEventScraper(backfill=True), empty_creds_db, empty_creds_fs, mocked_splitter, mocked_sr_model
        ]

        # Initialize pipeline
        pipeline = EventPipeline(example_config)

        # Pre read event item returns
        event_items_zero = RequestReturn(example_legistar_tools_event_items_0)
        event_items_one = RequestReturn(example_legistar_tools_event_items_1)

        with mock.patch("requests.get") as mock_requests:
            # Backfill means we need to mock every request call including all the legistar calls
            mock_requests.side_effect = [
                RequestReturn(example_seattle_routes),
                RequestReturn(example_seattle_route),
                RequestReturn(example_legistar_tools_events),
                event_items_zero,
                *([RequestReturn(example_legistar_tools_event_item_vote)] * len(event_items_zero.content)),
                event_items_one,
                *([RequestReturn(example_legistar_tools_event_item_vote)] * len(event_items_one.content))
            ]

            # Mock the video copy
            with mock.patch("cdptools.file_stores.FileStore._external_resource_copy") as mocked_resource_copy:
                mocked_resource_copy.return_value = example_video

                # Interupt calls to os.remove because it deletes test data otherwise
                with mock.patch("os.remove"):
                    pipeline.run()
