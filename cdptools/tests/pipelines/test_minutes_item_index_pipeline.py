#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from unittest import mock

import pytest
from firebase_admin import firestore
from google.cloud import storage

from cdptools.databases.cloud_firestore_database import CloudFirestoreDatabase
from cdptools.file_stores.gcs_file_store import GCSFileStore
from cdptools.indexers.tfidf_indexer import TFIDFIndexer
from cdptools.pipelines import MinutesItemIndexPipeline

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


@pytest.fixture
def example_minutes_item_file_0(data_dir):
    return data_dir / "example_minutes_item_file_0.docx"


@pytest.fixture
def example_minutes_item_file_1(data_dir):
    return data_dir / "example_minutes_item_file_1.docx"


@pytest.fixture
def select_rows_data():
    return [
        # Select decision items
        [
            {
                "event_minutes_item_id": "341f7607-d38a-46fd-bc85-74eb7d93a74d",
                "minutes_item_id": "435de5b9-6df4-4b6e-9d95-f118c7e7c73e",
                "index": 8,
                "event_id": "b848cda1-7144-4899-a3ab-6c33a99ff89d",
                "created": datetime.datetime(2019, 8, 4, 5, 56, 15, 512610),
                "decision": "Pass",
            },
            {
                "event_minutes_item_id": "882a97a5-d481-4073-991c-6f9241cae6e0",
                "minutes_item_id": "604ad8c4-449c-424e-bb75-2bbd3849bf68",
                "index": 10,
                "event_id": "04e6f8ce-7d38-454f-b07b-5a910948a48a",
                "created": datetime.datetime(2019, 8, 4, 5, 46, 0, 519498),
                "decision": "Pass",
            },
        ],
        # Get most recent transcript for b848cda1-7144-4899-a3ab-6c33a99ff89d
        [
            {
                "transcript_id": "6b826b19-1510-4a2a-9a99-f90fc09bca60",
                "confidence": 0.929794622792138,
                "event_id": "b848cda1-7144-4899-a3ab-6c33a99ff89d",
                "file_id": "d6fe106a-868c-4fb9-acb5-d8c7eea618fa",
                "created": datetime.datetime(2019, 8, 4, 5, 56, 22, 614775),
            }
        ],
        # Get most recent transcript for 04e6f8ce-7d38-454f-b07b-5a910948a48a
        [
            {
                "transcript_id": "0913f8ba-5134-4ae6-8aa6-a3ac303c2de4",
                "confidence": 0.9357563015257958,
                "event_id": "04e6f8ce-7d38-454f-b07b-5a910948a48a",
                "file_id": "867c7aa3-b53f-49e4-86cf-3d410908dee7",
                "created": datetime.datetime(2019, 8, 4, 5, 46, 2, 854732),
            }
        ],
        # Get minutes item files for minutes item 435de5b9-6df4-4b6e-9d95-f118c7e7c73e
        [
            {
                "minutes_item_file_id": "19e82346-50b8-4690-a182-754c41ff1b44",
                "minutes_item_id": "435de5b9-6df4-4b6e-9d95-f118c7e7c73e",
                "name": "Summary and Fiscal Note",
                "legistar_matter_attachment_id": 21615,
                "created": datetime.datetime(2019, 8, 4, 5, 56, 14, 994232),
                "uri": "http://legistar2.granicus.com/seattle/attachments/c51bd839-e406-40be-9087-c4ab6a1128ac.docx",  # noqa: E501
            }
        ],
        # Get minutes item files for minutes item 604ad8c4-449c-424e-bb75-2bbd3849bf68
        [
            {
                "minutes_item_file_id": "44604465-0209-4033-aaaf-4ab2f3d163f0",
                "legistar_matter_attachment_id": 21988,
                "created": datetime.datetime(2019, 8, 4, 5, 46, 0, 76622),
                "uri": "http://legistar2.granicus.com/seattle/attachments/414ba24b-c342-45f9-bc2d-eaad6f2c9873.docx",  # noqa: E501
                "minutes_item_id": "604ad8c4-449c-424e-bb75-2bbd3849bf68",
                "name": "Summary Att A \u2013 Map and \u201cExplorer Voyage\u201d Artwork of Christie Park",
            }
        ],
    ]


@pytest.fixture
def select_row_data():
    return [
        # Get additional details for minutes item
        {
            "minutes_item_id": "435de5b9-6df4-4b6e-9d95-f118c7e7c73e",
            "name": "CB 119579",
            "created": datetime.datetime(2019, 8, 4, 5, 56, 14, 753998),
            "matter": "CB 119579",
            "legistar_event_item_id": 65957,
        },
        {
            "minutes_item_id": "604ad8c4-449c-424e-bb75-2bbd3849bf68",
            "name": "CB 119587",
            "created": datetime.datetime(2019, 8, 4, 5, 45, 59, 611139),
            "matter": "CB 119587",
            "legistar_event_item_id": 65840,
        },
        # Get event details for minutes item 435de5b9-6df4-4b6e-9d95-f118c7e7c73e
        {
            "event_id": "b848cda1-7144-4899-a3ab-6c33a99ff89d",
            "source_uri": "http://www.seattlechannel.org/mayor-and-council/city-council/2018/2019-finance-and-neighborhoods?videoid=x106046",  # noqa: E501
            "legistar_event_id": 4051,
            "event_datetime": datetime.datetime(2019, 7, 31, 14, 0),
            "agenda_file_uri": "http://legistar2.granicus.com/seattle/meetings/2019/7/4051_A_Finance_and_Neighborhoods_Committee_19-07-31_Committee_Agenda.pdf",  # noqa: E501
            "minutes_file_uri": None,
            "video_uri": "https://video.seattle.gov/media/council/fin_073119_2551929V.mp4",
            "created": datetime.datetime(2019, 8, 4, 5, 56, 12, 835251),
            "body_id": "1d8dde14-b8e8-4aac-ba10-65165e11b978",
            "legistar_event_link": "https://seattle.legistar.com/MeetingDetail.aspx?LEGID=4051&GID=393&G=FFE3B678-CEF6-4197-84AC-5204EA4CFC0C",  # noqa: E501
        },
        # Get event details for minutes item 604ad8c4-449c-424e-bb75-2bbd3849bf68
        {
            "event_id": "04e6f8ce-7d38-454f-b07b-5a910948a48a",
            "source_uri": "http://www.seattlechannel.org/mayor-and-council/city-council/2018/2019-civic-development-public-assets-and-native-communities-committee?videoid=x106045",  # noqa: E501
            "legistar_event_id": 4035,
            "event_datetime": datetime.datetime(2019, 7, 31, 12, 0),
            "agenda_file_uri": "http://legistar2.granicus.com/seattle/meetings/2019/7/4035_A_Civic_Development%2C_Public_Assets%2C_and_Native_Communities_Committee_19-07-31_Committee_Agenda.pdf",  # noqa: E501
            "minutes_file_uri": None,
            "video_uri": "https://video.seattle.gov/media/council/civdev_073119_2541928V.mp4",
            "created": datetime.datetime(2019, 8, 4, 5, 45, 51, 114947),
            "legistar_event_link": "https://seattle.legistar.com/MeetingDetail.aspx?LEGID=4035&GID=393&G=FFE3B678-CEF6-4197-84AC-5204EA4CFC0C",  # noqa: E501
            "body_id": "1bb00f30-c852-4668-840b-b882e8ed5de2",
        },
        # Get file details for transcript 6b826b19-1510-4a2a-9a99-f90fc09bca60
        {
            "file_id": "d6fe106a-868c-4fb9-acb5-d8c7eea618fa",
            "uri": "gs://fake-cdp-instance.appspot.com/13d3085ac6303361e1ec17c7009dfde502d032bc6af7aa7af2101291d6550aac_ts_sentences_transcript_0.json",  # noqa: E501
            "content_type": None,
            "filename": "13d3085ac6303361e1ec17c7009dfde502d032bc6af7aa7af2101291d6550aac_ts_sentences_transcript_0.json",  # noqa: E501
            "created": datetime.datetime(2019, 8, 4, 5, 56, 9, 838975),
            "description": None,
        },
        # Get file details for transcript 0913f8ba-5134-4ae6-8aa6-a3ac303c2de4
        {
            "file_id": "867c7aa3-b53f-49e4-86cf-3d410908dee7",
            "filename": "99854f8d28e55cfd8408a8d6330bef151fe5d4f31c943e45b3b0642e20fc3048_ts_sentences_transcript_0.json",  # noqa: E501
            "created": datetime.datetime(2019, 8, 4, 5, 45, 47, 442422),
            "description": None,
            "uri": "gs://fake-cdp-instance.appspot.com/99854f8d28e55cfd8408a8d6330bef151fe5d4f31c943e45b3b0642e20fc3048_ts_sentences_transcript_0.json",  # noqa: E501
            "content_type": None,
        },
    ]


def test_minutes_item_index_pipeline(
    empty_creds_db,
    empty_creds_fs,
    example_config,
    example_transcript_sentences_0,
    example_transcript_sentences_1,
    example_minutes_item_file_0,
    example_minutes_item_file_1,
    select_rows_data,
    select_row_data,
):
    # Configure all mocks
    with mock.patch(
        "cdptools.dev_utils.load_custom_object.load_custom_object"
    ) as mock_loader:
        mock_loader.side_effect = [empty_creds_db, empty_creds_fs, TFIDFIndexer()]

        # Initialize pipeline
        pipeline = MinutesItemIndexPipeline(example_config)

        # Mock any time we request rows get
        cfdb = "cdptools.databases.cloud_firestore_database.CloudFirestoreDatabase"
        with mock.patch(f"{cfdb}.select_rows_as_list") as mocked_select_rows:
            mocked_select_rows.side_effect = select_rows_data

            # Mock any time we request single row get
            with mock.patch(f"{cfdb}.select_row_by_id") as mocked_select_row:
                mocked_select_row.side_effect = select_row_data

                # Mock any call to select row with max results expectation
                with mock.patch(
                    f"{cfdb}._select_rows_with_max_results_expectation"
                ) as mocked_select_with_expectation:
                    mocked_select_with_expectation.return_value = None

                    # Mock any file request with creds
                    with mock.patch(
                        "cdptools.file_stores.gcs_file_store.GCSFileStore.download_file"
                    ) as mocked_download_file:
                        mocked_download_file.side_effect = [
                            example_transcript_sentences_0,
                            example_transcript_sentences_1,
                        ]

                        # Mock any external file request
                        with mock.patch(
                            "cdptools.file_stores.gcs_file_store.FileStore._external_resource_copy"
                        ) as mocked_resource_copy:
                            mocked_resource_copy.side_effect = [
                                example_minutes_item_file_0,
                                example_minutes_item_file_1,
                            ]

                            pipeline.run()
