#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tempfile
from datetime import datetime
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
        with mock.patch.object(
            CloudFirestoreDatabase,
            "select_rows_as_list",
            side_effect=[
                [{
                    "event_id": "0a8fcd28-b920-4088-bd73-ceacb304db0f",
                    "legistar_event_id": 4023,
                    "event_datetime": datetime(2019, 7, 15, 9, 30),
                    "agenda_file_uri": "http://legistar2.granicus.com/seattle/meetings/2019/7/4023_A_Council_Briefing_19-07-15_Council_Briefing.pdf",  # noqa: E501
                    "minutes_file_uri": None,
                    "video_uri": "http://video.seattle.gov:8080/media/council/brief_071519_2011955V.mp4",
                    "created": datetime(2019, 7, 20, 1, 53, 14, 77790),
                    "body_id": "f0867cf1-7bb0-4f28-83c9-a8cac6152ea4",
                    "legistar_event_link": "https://seattle.legistar.com/MeetingDetail.aspx?LEGID=4023&GID=393&G=FFE3B678-CEF6-4197-84AC-5204EA4CFC0C",  # noqa: E501
                    "source_uri": "http://www.seattlechannel.org/CouncilBriefings?videoid=x105823"
                }],
                [{
                    "transcript_id": "9183055d-300d-4204-8741-57cebbb280a9",
                    "confidence": 0.9498944201984921,
                    "event_id": "0a8fcd28-b920-4088-bd73-ceacb304db0f",
                    "created": datetime(2019, 7, 20, 1, 53, 18, 611107),
                    "file_id": "76b7b54d-2f9b-4cad-b0b8-039a51937c15"
                }],
                [{
                    "body_id": "f0867cf1-7bb0-4f28-83c9-a8cac6152ea4",
                    "name": "Council Briefing",
                    "created": datetime(2019, 7, 20, 1, 53, 13, 821791),
                    "description": None
                }]
            ]
        ):

            with mock.patch.object(
                CloudFirestoreDatabase,
                "select_row_by_id",
                return_value={
                    "file_id": "76b7b54d-2f9b-4cad-b0b8-039a51937c15",
                    "content_type": None,
                    "filename": "fc52ca9f9febd50ece14f46170014936f76f3d0227688ff96fcf7e369404eee7_ts_sentences_transcript_0.json",  # noqa: E501
                    "created": datetime(2019, 7, 20, 1, 53, 10, 726978),
                    "description": None,
                    "uri": "gs://fake-cdp-instance.appspot.com/fc52ca9f9febd50ece14f46170014936f76f3d0227688ff96fcf7e369404eee7_ts_sentences_transcript_0.json"  # noqa: E501
                }
            ):

                with mock.patch("cdptools.file_stores.gcs_file_store.GCSFileStore.download_file") as mocked_download:
                    mocked_download.return_value = example_transcript

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
