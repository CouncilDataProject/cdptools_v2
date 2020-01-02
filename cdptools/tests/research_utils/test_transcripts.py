#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tempfile
from datetime import datetime
from pathlib import Path
from shutil import copyfile
from unittest import mock

import pytest

from cdptools.databases.cloud_firestore_database import CloudFirestoreDatabase
from cdptools.file_stores.gcs_file_store import GCSFileStore
from cdptools.research_utils import transcripts as transcript_tools


@pytest.fixture
def example_transcript(data_dir):
    return data_dir / "example_transcript_sentences.json"


@pytest.mark.parametrize("order_by_field", [
    ("confidence"),
    ("created"),
    pytest.param("not-a-valid-field", marks=pytest.mark.raises(exception=ValueError))
])
def test_download_transcripts(example_transcript, order_by_field):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch select rows as list
        with mock.patch.object(
            CloudFirestoreDatabase,
            "select_rows_as_list",
            side_effect=[
                [{
                    "event_id": "1",
                    "legistar_event_id": 4023,
                    "event_datetime": datetime(2019, 7, 15, 9, 30),
                    "agenda_file_uri": "doesnt-matter",
                    "minutes_file_uri": None,
                    "video_uri": "doesnt-matter",
                    "created": datetime(2019, 7, 20, 1, 53, 14, 77790),
                    "body_id": "1",
                    "legistar_event_link": "doesnt-matter",
                    "source_uri": "http://www.seattlechannel.org/CouncilBriefings?videoid=x105823"
                }],
                [{
                    "transcript_id": "1",
                    "confidence": 0.9498944201984921,
                    "event_id": "1",
                    "created": datetime(2019, 7, 20, 1, 53, 18, 611107),
                    "file_id": "1"
                }],
                [{
                    "body_id": "1",
                    "name": "Council Briefing",
                    "created": datetime(2019, 7, 20, 1, 53, 13, 821791),
                    "description": None
                }]
            ]
        ):
            # Patch select row by id
            with mock.patch.object(
                CloudFirestoreDatabase,
                "select_row_by_id",
                return_value={
                    "file_id": "1",
                    "content_type": None,
                    "filename": "example_transcript_sentences.json",  # This doesn't really matter
                    "created": datetime(2019, 7, 20, 1, 53, 10, 726978),
                    "description": None,
                    "uri": "doesnt-matter"
                }
            ):

                # Interrupt and copy file
                with mock.patch("cdptools.file_stores.file_store.FileStore._external_resource_copy") as mocked_copy:
                    save_path = Path(tmpdir) / "example_transcript_sentences.json"
                    copyfile(example_transcript, save_path)
                    mocked_copy.return_value = save_path

                    # Initialize objects
                    db = CloudFirestoreDatabase("fake-cdp-instance")
                    fs = GCSFileStore("fake-cdp-instance.appspot.com")

                    # Get the event corpus map
                    event_corpus_map = transcript_tools.download_transcripts(
                        db=db,
                        fs=fs,
                        order_by_field=order_by_field,
                        save_dir=tmpdir
                    )

                    # Assert structure
                    assert len(event_corpus_map) == 1

                    # It should have one transcript and the manifest CSV
                    assert len(list(Path(tmpdir).iterdir())) == 2
