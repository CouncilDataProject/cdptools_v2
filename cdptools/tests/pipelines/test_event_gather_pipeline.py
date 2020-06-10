#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from pathlib import Path
from typing import List, Union
from unittest import mock

import pytest
from firebase_admin import firestore
from google.cloud import storage
from requests import RequestException

from cdptools.audio_splitters.ffmpeg_audio_splitter import FFmpegAudioSplitter
from cdptools.databases.cloud_firestore_database import CloudFirestoreDatabase
from cdptools.event_scrapers.seattle_event_scraper import SeattleEventScraper
from cdptools.file_stores.gcs_file_store import GCSFileStore
from cdptools.pipelines import EventGatherPipeline
from cdptools.sr_models.google_cloud_sr_model import GoogleCloudSRModel, SRModelOutputs
from cdptools.sr_models.webvtt_sr_model import WebVTTSRModel

from ..databases.test_cloud_firestore_database import MockedCollection
from ..file_stores.test_gcs_file_store import MockedBlob, MockedBucket


@pytest.fixture
def legistar_data_dir(data_dir) -> Path:
    return data_dir / "legistar"


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
def example_config_with_mixture_sr_model(data_dir) -> Path:
    return data_dir / "example_event_pipeline_config_with_mixture_sr_model.json"


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
def example_transcript_speaker_turns(data_dir) -> Path:
    return data_dir / "example_transcript_speaker_turns.json"


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
def mocked_splitter(example_audio) -> FFmpegAudioSplitter:
    mocked_splitter = mock.Mock(FFmpegAudioSplitter())
    mocked_splitter.split.return_value = example_audio
    return mocked_splitter


@pytest.fixture
def mocked_sr_model(
    example_transcript_raw, example_transcript_words, example_transcript_sentences
) -> GoogleCloudSRModel:
    # Create basic sr model
    # It doesn't matter what file is put in the init as long as it's a file
    # The speech client is configured during the transcribe function
    mocked_model = mock.Mock(GoogleCloudSRModel(example_transcript_raw))
    mocked_model.transcribe.return_value = SRModelOutputs(
        example_transcript_raw,
        99.0,
        example_transcript_words,
        example_transcript_sentences,
    )

    return mocked_model


@pytest.fixture
def mocked_caption_sr_model(
    example_transcript_raw,
    example_transcript_sentences,
    example_transcript_speaker_turns,
) -> WebVTTSRModel:
    mocked_model = mock.Mock(WebVTTSRModel("any-new-turn-pattern"))
    mocked_model.transcribe.return_value = SRModelOutputs(
        raw_path=example_transcript_raw,
        confidence=1,
        timestamped_sentences_path=example_transcript_sentences,
        timestamped_speaker_turns_path=example_transcript_speaker_turns,
    )

    return mocked_model


@pytest.fixture
def mocked_webvtt_sr_model_with_request_exception() -> WebVTTSRModel:
    mocked_model = mock.Mock(WebVTTSRModel("any-new-turn-pattern"))
    # Mock RequestException for transcribe with invalid-caption-uri
    mocked_model.transcribe.side_effect = RequestException("invalid-caption-uri")
    return mocked_model


@pytest.fixture
def example_seattle_routes(data_dir):
    return data_dir / "example_seattle_routes.html"


@pytest.fixture
def example_seattle_route(data_dir):
    return data_dir / "example_seattle_route.html"


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


@pytest.fixture
def loaded_legistar_requests(legistar_data_dir) -> List[RequestReturn]:
    mocked_responses = []
    for i in range(len(list(legistar_data_dir.glob("request_*")))):
        mocked_responses.append(
            RequestReturn(list(legistar_data_dir.glob(f"request_{i}_*"))[0])
        )

    return mocked_responses


def test_event_pipeline_single_sr_model_initialization(
    empty_creds_db, empty_creds_fs, mocked_sr_model, example_config
):
    # Configure all mocks
    with mock.patch(
        "cdptools.dev_utils.load_custom_object.load_custom_object"
    ) as mock_loader:
        mock_loader.side_effect = [
            SeattleEventScraper(),
            empty_creds_db,
            empty_creds_fs,
            FFmpegAudioSplitter(),
            mocked_sr_model,
        ]

        # Initialize pipeline
        pipeline = mock.Mock(EventGatherPipeline(example_config))

        # Test EventGatherPipeline's single sr_model initialization
        assert hasattr(pipeline, "sr_model")
        assert not hasattr(pipeline, "caption_sr_model")


def test_event_pipeline_mixture_sr_model_initialization(
    empty_creds_db,
    empty_creds_fs,
    mocked_sr_model,
    mocked_caption_sr_model,
    example_config_with_mixture_sr_model,
):
    # Configure all mocks
    with mock.patch(
        "cdptools.dev_utils.load_custom_object.load_custom_object"
    ) as mock_loader:
        mock_loader.side_effect = [
            SeattleEventScraper(),
            empty_creds_db,
            empty_creds_fs,
            FFmpegAudioSplitter(),
            mocked_caption_sr_model,
            mocked_sr_model,
        ]

        # Initialize pipeline
        pipeline = mock.Mock(EventGatherPipeline(example_config_with_mixture_sr_model))

        # Test EventGatherPipeline's mixture sr_model initialization
        assert hasattr(pipeline, "sr_model")
        assert hasattr(pipeline, "caption_sr_model")


def test_event_pipeline_no_backfill(
    empty_creds_db,
    empty_creds_fs,
    mocked_sr_model,
    example_config,
    example_seattle_routes,
):
    # Configure all mocks
    with mock.patch(
        "cdptools.dev_utils.load_custom_object.load_custom_object"
    ) as mock_loader:
        mock_loader.side_effect = [
            SeattleEventScraper(),
            empty_creds_db,
            empty_creds_fs,
            FFmpegAudioSplitter(),
            mocked_sr_model,
        ]

        # Initialize pipeline
        pipeline = mock.Mock(EventGatherPipeline(example_config))

        with mock.patch("requests.get") as mock_requests:
            # No backfill means only routes will be gathered because example html file only includes past events.
            mock_requests.side_effect = [RequestReturn(example_seattle_routes)]

            pipeline.run()

            # This should never be ran because example html files only include past events.
            pipeline.process_event.assert_not_called()


def test_event_gather_pipeline_with_backfill(
    empty_creds_db,
    empty_creds_fs,
    mocked_splitter,
    mocked_sr_model,
    example_config,
    example_seattle_routes,
    example_seattle_route,
    example_video,
    loaded_legistar_requests,
):
    # Configure all mocks
    with mock.patch(
        "cdptools.dev_utils.load_custom_object.load_custom_object"
    ) as mock_loader:
        mock_loader.side_effect = [
            SeattleEventScraper(backfill=True),
            empty_creds_db,
            empty_creds_fs,
            mocked_splitter,
            mocked_sr_model,
        ]

        # Initialize pipeline
        pipeline = EventGatherPipeline(example_config)

        with mock.patch("requests.get") as mock_requests:
            # Backfill means we need to mock every request call including all the legistar calls
            mock_requests.side_effect = [
                RequestReturn(example_seattle_routes),
                RequestReturn(example_seattle_route),
                *loaded_legistar_requests,
            ]

            # Mock the video copy
            with mock.patch(
                "cdptools.file_stores.FileStore._external_resource_copy"
            ) as mocked_resource_copy:
                mocked_resource_copy.return_value = example_video

                # Interupt calls to os.remove because it deletes test data otherwise
                with mock.patch("os.remove"):
                    pipeline.run()


def test_event_pipeline_sr_model_failure(
    empty_creds_db,
    empty_creds_fs,
    mocked_splitter,
    mocked_sr_model,
    mocked_webvtt_sr_model_with_request_exception,
    example_config_with_mixture_sr_model,
    example_seattle_routes,
    example_seattle_route,
    example_video,
    loaded_legistar_requests,
):
    # Configure all mocks
    with mock.patch(
        "cdptools.dev_utils.load_custom_object.load_custom_object"
    ) as mock_loader:
        mock_loader.side_effect = [
            SeattleEventScraper(backfill=True),
            empty_creds_db,
            empty_creds_fs,
            mocked_splitter,
            mocked_webvtt_sr_model_with_request_exception,
            mocked_sr_model,
        ]

        # Initialize pipeline
        pipeline = EventGatherPipeline(example_config_with_mixture_sr_model)

        with mock.patch("requests.get") as mock_requests:
            # Backfill means we need to mock every request call including all the legistar calls
            mock_requests.side_effect = [
                RequestReturn(example_seattle_routes),
                RequestReturn(example_seattle_route),
                *loaded_legistar_requests,
            ]

            # Mock the video copy
            with mock.patch(
                "cdptools.file_stores.FileStore._external_resource_copy"
            ) as mocked_resource_copy:
                mocked_resource_copy.return_value = example_video

                # Interupt calls to os.remove because it deletes test data otherwise
                with mock.patch("os.remove"):
                    pipeline.run()
                    # Check if sr_model is called, because caption_sr_model raised RequestException
                    pipeline.sr_model.transcribe.assert_called()


def test_event_pipeline_caption_sr_model_success(
    empty_creds_db,
    empty_creds_fs,
    mocked_splitter,
    mocked_sr_model,
    mocked_caption_sr_model,
    example_config_with_mixture_sr_model,
    example_seattle_routes,
    example_seattle_route,
    example_video,
    loaded_legistar_requests,
):
    # Configure all mocks
    with mock.patch(
        "cdptools.dev_utils.load_custom_object.load_custom_object"
    ) as mock_loader:
        mock_loader.side_effect = [
            SeattleEventScraper(backfill=True),
            empty_creds_db,
            empty_creds_fs,
            mocked_splitter,
            mocked_caption_sr_model,
            mocked_sr_model,
        ]

        # Initialize pipeline
        pipeline = EventGatherPipeline(example_config_with_mixture_sr_model)

        with mock.patch("requests.get") as mock_requests:
            # Backfill means we need to mock every request call including all the legistar calls
            mock_requests.side_effect = [
                RequestReturn(example_seattle_routes),
                RequestReturn(example_seattle_route),
                *loaded_legistar_requests,
            ]

            # Mock the video copy
            with mock.patch(
                "cdptools.file_stores.FileStore._external_resource_copy"
            ) as mocked_resource_copy:
                mocked_resource_copy.return_value = example_video

                # Interupt calls to os.remove because it deletes test data otherwise
                with mock.patch("os.remove"):
                    pipeline.run()
                    # Check if sr_model is not called, because caption_sr_model return valid outputs
                    pipeline.sr_model.transcribe.assert_not_called()
