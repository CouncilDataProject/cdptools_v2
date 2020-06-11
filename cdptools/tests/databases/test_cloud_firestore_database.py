#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from unittest import mock

import pytest
from cdptools.databases import WhereOperators, exceptions
from cdptools.databases.cloud_firestore_database import (
    CloudFirestoreDatabase, CloudFirestoreWhereOperators, NoCredResponseTypes)
from firebase_admin import firestore


class MockedResponse:
    def __init__(self, json_data):
        self.json_data = json_data

    def raise_for_status(self):
        return True

    def json(self):
        return self.json_data


class MockedDocument:
    def __init__(self, id, json_data):
        self.id = id
        self.json_data = json_data

    def get(self):
        return self

    def set(self, values):
        self.json_data = values
        return self

    def to_dict(self):
        return self.json_data


class MockedCollection:
    def __init__(self, items):
        self.items = items

    def document(self, id):
        if len(self.items) == 0:
            return MockedDocument("new_doc", {})

        return self.items[0]

    def where(self, col, op, val):
        return self

    def limit(self, val):
        return self

    def order_by(self, col, direction):
        return self

    def stream(self):
        return self.items


EVENT_ITEM = {
    "name": "projects/fake-cdp-instance/databases/(default)/documents/event/0e3bd59c-3f07-452c-83cf-e9eebeb73af2",  # noqa: E501
    "fields": {
        "video_uri": {
            "stringValue": "http://video.seattle.gov:8080/media/council/gen_062717V.mp4"
        },
        "created": {"timestampValue": "2019-04-21T23:58:04.832481Z"},
        "event_datetime": {"timestampValue": "2017-06-27T00:00:00Z"},
        "body_id": {"stringValue": "6f38a688-2e96-4e33-841c-883738f9f03d"},
        "source_uri": {
            "stringValue": "http://www.seattlechannel.org/mayor-and-council/city-council/2016/2017-gender-equity-safe-communities-and-new-americans-committee?videoid=x78448"  # noqa: E501
        },
        "test_boolean_value": {"booleanValue": True},
        "test_null_value": {"nullValue": None},
        "test_float_value": {"doubleValue": "12.12"},
        "test_integer_value": {"integerValue": "12"},
    },
}


EVENT_ITEMS = [{"document": EVENT_ITEM}]

INDEXED_EVENT_TERM_ITEMS_HELLO = [
    {
        "document": {
            "name": "projects/fake-cdp-instance/databases/(default)/documents/indexed_event_term/000",  # noqa: E501
            "fields": {
                "event_id": {"stringValue": "event_id_123"},
                "updated": {"timestampValue": "2019-04-21T23:58:04.832481Z"},
                "term": {"stringValue": "hello"},
                "value": {"doubleValue": 0.2},
            },
        }
    },
    {
        "document": {
            "name": "projects/fake-cdp-instance/databases/(default)/documents/indexed_event_term/111",  # noqa: E501
            "fields": {
                "event_id": {"stringValue": "event_id_234"},
                "updated": {"timestampValue": "2019-04-21T23:58:04.832481Z"},
                "term": {"stringValue": "hello"},
                "value": {"doubleValue": 0.4},
            },
        }
    },
]

INDEXED_EVENT_TERM_ITEMS_WORLD = [
    {
        "document": {
            "name": "projects/fake-cdp-instance/databases/(default)/documents/indexed_event_term/222",  # noqa: E501
            "fields": {
                "event_id": {"stringValue": "event_id_234"},
                "updated": {"timestampValue": "2019-04-21T23:58:04.832481Z"},
                "term": {"stringValue": "world"},
                "value": {"doubleValue": 0.4},
            },
        }
    }
]

EVENT_VALUES = {
    "source_uri": "http://www.seattlechannel.org/mayor-and-council/city-council/2016/2017-gender-equity-safe-communities-and-new-americans-committee?videoid=x78448",  # noqa: E501
    "created": datetime.utcnow(),
    "video_uri": "http://video.seattle.gov:8080/media/council/gen_062717V.mp4",
    "event_datetime": "2017-06-27T00:00:00",
    "body_id": "6f38a688-2e96-4e33-841c-883738f9f03d",
}


@pytest.fixture
def no_creds_db() -> CloudFirestoreDatabase:
    return CloudFirestoreDatabase("this-is-a-fake-database-hi")


@pytest.fixture
def creds_db() -> CloudFirestoreDatabase:
    with mock.patch(
        "cdptools.databases.cloud_firestore_database.CloudFirestoreDatabase._initialize_creds_db"  # noqa: E501
    ):
        db = CloudFirestoreDatabase("/fake/path/to/creds.json")
        db._credentials_path = "/fake/path/to/creds.json"
        db._root = mock.Mock(firestore.Client)
        db._root.collection.return_value = MockedCollection(
            [MockedDocument("0e3bd59c-3f07-452c-83cf-e9eebeb73af2", EVENT_VALUES)]
        )

        return db


@pytest.fixture
def empty_creds_db() -> CloudFirestoreDatabase:
    with mock.patch(
        "cdptools.databases.cloud_firestore_database.CloudFirestoreDatabase._initialize_creds_db"  # noqa: E501
    ):
        db = CloudFirestoreDatabase("/fake/path/to/creds.json")
        db._credentials_path = "/fake/path/to/creds.json"
        db._root = mock.Mock(firestore.Client)
        db._root.collection.return_value = MockedCollection([])

        return db


@pytest.mark.parametrize(
    "project_id, credentials_path",
    [
        ("fake-cdp-instance", None),
        pytest.param(
            None,
            "/this/path/doesnt/exist.json",
            marks=pytest.mark.raises(exception=FileNotFoundError),
        ),
        pytest.param(
            None,
            None,
            marks=pytest.mark.raises(exception=exceptions.MissingParameterError),
        ),
    ],
)
def test_cloud_firestore_database_init(project_id, credentials_path):
    CloudFirestoreDatabase(project_id, credentials_path)


@pytest.mark.parametrize(
    "pks",
    [
        ([("video_uri", "does_not_exist")]),
        (
            [
                (
                    "video_uri",
                    "http://video.seattle.gov:8080/media/council/gen_062717V.mp4",
                )
            ]
        ),
    ],
)
def test_get_or_upload_row(no_creds_db, creds_db, empty_creds_db, pks):
    with pytest.raises(exceptions.MissingCredentialsError):
        no_creds_db._get_or_upload_row("event", pks, EVENT_VALUES)

    creds_db._get_or_upload_row("event", pks, EVENT_VALUES)
    empty_creds_db._get_or_upload_row("event", pks, EVENT_VALUES)


def test_cloud_firestore_database_select_row(no_creds_db, creds_db):
    # Mock requests
    with mock.patch("requests.get") as mocked_request:
        mocked_request.return_value = MockedResponse(EVENT_ITEM)
        no_creds_db.select_row_by_id("event", "0e3bd59c-3f07-452c-83cf-e9eebeb73af2")

    creds_db.select_row_by_id("event", "0e3bd59c-3f07-452c-83cf-e9eebeb73af2")


@pytest.mark.parametrize(
    "filters, order_by, limit",
    [
        (None, None, None),
        (
            [
                (
                    "video_uri",
                    "http://video.seattle.gov:8080/media/council/gen_062717V.mp4",
                )
            ],
            None,
            None,
        ),
        (
            [
                (
                    "video_uri",
                    "http://video.seattle.gov:8080/media/council/gen_062717V.mp4",
                )
            ],
            "video_uri",
            None,
        ),
        (
            [
                (
                    "video_uri",
                    "http://video.seattle.gov:8080/media/council/gen_062717V.mp4",
                )
            ],
            None,
            10,
        ),
        (
            [
                (
                    "video_uri",
                    "http://video.seattle.gov:8080/media/council/gen_062717V.mp4",
                )
            ],
            "video_uri",
            10,
        ),
        (None, "video_uri", None),
        (None, "video_uri", 10),
        (None, None, 10),
        pytest.param(
            None,
            12,
            None,
            marks=pytest.mark.raises(
                exception=exceptions.UnknownTypeOrderConditionError
            ),
        ),
    ],
)
def test_cloud_firestore_database_select_rows_as_list(
    no_creds_db, creds_db, filters, order_by, limit
):
    # Mock requests
    with mock.patch("requests.post") as mocked_request:
        mocked_request.return_value = MockedResponse(EVENT_ITEMS)
        no_creds_db.select_rows_as_list("event", filters, order_by, limit)

    creds_db.select_rows_as_list("event", filters, order_by, limit)


@pytest.mark.parametrize(
    "op, expected",
    [
        (WhereOperators.eq, CloudFirestoreWhereOperators.eq),
        (WhereOperators.contains, CloudFirestoreWhereOperators.contains),
        (WhereOperators.gt, CloudFirestoreWhereOperators.gt),
        (WhereOperators.lt, CloudFirestoreWhereOperators.lt),
        (WhereOperators.gteq, CloudFirestoreWhereOperators.gteq),
        (WhereOperators.lteq, CloudFirestoreWhereOperators.lteq),
        pytest.param(
            "hello world", None, marks=pytest.mark.raises(exception=ValueError)
        ),
    ],
)
def test_convert_base_where_operator_to_cloud_firestore_where_operator(op, expected):
    assert (
        CloudFirestoreDatabase._convert_base_where_operator_to_cloud_firestore_where_operator(    # noqa: E501
            op
        )
        == expected
    )


@pytest.mark.parametrize(
    "val, expected",
    [
        (True, NoCredResponseTypes.boolean),
        (0.1, NoCredResponseTypes.double),
        (datetime.utcnow(), NoCredResponseTypes.dt),
        (1, NoCredResponseTypes.integer),
        ("hello world", NoCredResponseTypes.string),
        (None, NoCredResponseTypes.null),
        pytest.param(
            ("hello", "world"), None, marks=pytest.mark.raises(exception=ValueError)
        ),
    ],
)
def test_get_cloud_firestore_value_type(val, expected):
    assert CloudFirestoreDatabase._get_cloud_firestore_value_type(val) == expected


@pytest.mark.parametrize(
    "pks, n_expected",
    [
        (
            [
                (
                    "video_uri",
                    "http://video.seattle.gov:8080/media/council/gen_062717V.mp4",
                )
            ],
            1,
        ),
        pytest.param(
            [
                (
                    "video_uri",
                    "http://video.seattle.gov:8080/media/council/gen_062717V.mp4",
                )
            ],
            0,
            marks=pytest.mark.raises(exception=exceptions.UniquenessError),
        ),
    ],
)
def test_cloud_firestore_database_max_expectation(
    no_creds_db, creds_db, pks, n_expected
):
    # Mock requests
    with mock.patch("requests.post") as mocked_request:
        mocked_request.return_value = MockedResponse(EVENT_ITEMS)
        no_creds_db._select_rows_with_max_results_expectation("event", pks, n_expected)

    creds_db._select_rows_with_max_results_expectation("event", pks, n_expected)


def test_search_events(no_creds_db):
    # Mock the complex search query
    with mock.patch("requests.post") as mocked_post:
        mocked_post.side_effect = [
            MockedResponse(INDEXED_EVENT_TERM_ITEMS_HELLO),
            MockedResponse(INDEXED_EVENT_TERM_ITEMS_WORLD),
        ]

        # Mock the minimal event gets that get attached to the `Match.data` attributes
        with mock.patch("requests.get") as mocked_get:
            mocked_get.return_value = MockedResponse({"fields": {}})

            # Generate results
            results = no_creds_db.search_events("hello world")

            # Check results
            # Two events returned
            assert len(results) == 2

            # Check individual event results
            # We know the order they should be returned in is highest match to lowest
            # match order
            # Check to make sure that is the case
            assert results[0].unique_id == "event_id_234"
            assert results[0].relevance == 0.8
            assert results[1].unique_id == "event_id_123"
            assert results[1].relevance == 0.2
