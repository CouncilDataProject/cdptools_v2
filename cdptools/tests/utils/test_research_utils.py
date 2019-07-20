#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tempfile
from datetime import datetime
from unittest import mock

import pytest

from cdptools.databases.cloud_firestore_database import CloudFirestoreDatabase
from cdptools.file_stores.gcs_file_store import GCSFileStore
from cdptools.utils import research_utils


@pytest.fixture
def example_transcript(data_dir):
    return data_dir / "example_transcript_sentences.json"


def test_download_most_recent_transcripts(example_transcript):
    with tempfile.TemporaryDirectory() as tmpdir:
        db = CloudFirestoreDatabase("stg-cdp-seattle")
        fs = GCSFileStore("stg-cdp-seattle.appspot.com")

        # Mock interactions
        with mock.patch(
            "cdptools.databases.cloud_firestore_database.CloudFirestoreDatabase.select_rows_as_list"
        ) as mocked_db_select:
            mocked_db_select.side_effect = [
                [{
                    "transcript_id": "9183055d-300d-4204-8741-57cebbb280a9",
                    "confidence": 0.9498944201984921,
                    "event_id": "0a8fcd28-b920-4088-bd73-ceacb304db0f",
                    "created": datetime(2019, 7, 20, 1, 53, 18, 611107),
                    "file_id": "76b7b54d-2f9b-4cad-b0b8-039a51937c15"
                }],
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
                    "body_id": "f0867cf1-7bb0-4f28-83c9-a8cac6152ea4",
                    "name": "Council Briefing",
                    "created": datetime(2019, 7, 20, 1, 53, 13, 821791),
                    "description": None
                }],
                [{
                    "file_id": "76b7b54d-2f9b-4cad-b0b8-039a51937c15",
                    "content_type": None,
                    "filename": "fc52ca9f9febd50ece14f46170014936f76f3d0227688ff96fcf7e369404eee7_ts_sentences_transcript_0.json",  # noqa: E501
                    "created": datetime(2019, 7, 20, 1, 53, 10, 726978),
                    "description": None,
                    "uri": "gs://stg-cdp-seattle.appspot.com/fc52ca9f9febd50ece14f46170014936f76f3d0227688ff96fcf7e369404eee7_ts_sentences_transcript_0.json"  # noqa: E501
                }]
            ]

            with mock.patch("cdptools.file_stores.gcs_file_store.GCSFileStore.download_file") as mocked_download:
                mocked_download.return_value = example_transcript

            # Get the event corpus map
            event_corpus_map = research_utils.download_most_recent_transcripts(db, fs, tmpdir)

            # Assert structure
            assert len(event_corpus_map) == 1
