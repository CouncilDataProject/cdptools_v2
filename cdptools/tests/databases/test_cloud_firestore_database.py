#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from unittest import mock

import pytest
from firebase_admin import firestore

from cdptools.databases import exceptions
from cdptools.databases.cloud_firestore_database import CloudFirestoreDatabase


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


RESPONSE_ITEM = {
    "name": "projects/stg-cdp-seattle/databases/(default)/documents/event/0e3bd59c-3f07-452c-83cf-e9eebeb73af2",
    "fields": {
        "video_uri": {"stringValue": "http://video.seattle.gov:8080/media/council/gen_062717V.mp4"},
        "created": {"timestampValue": "2019-04-21T23:58:04.832481Z"},
        "event_datetime": {"stringValue": "2017-06-27T00:00:00"},
        "body_id": {"stringValue": "6f38a688-2e96-4e33-841c-883738f9f03d"},
        "source_uri": {"stringValue": "http://www.seattlechannel.org/mayor-and-council/city-council/2016/2017-gender-equity-safe-communities-and-new-americans-committee?videoid=x78448"},  # noqa: E501
        "test_boolean_value": {"booleanValue": True},
        "test_null_value": {"nullValue": None},
        "test_float_value": {"doubleValue": "12.12"},
        "test_integer_value": {"integerValue": "12"}
    }
}

EVENT_VALUES = {
    "source_uri": "http://www.seattlechannel.org/mayor-and-council/city-council/2016/2017-gender-equity-safe-communities-and-new-americans-committee?videoid=x78448",  # noqa: E501
    "created": datetime.utcnow(),
    "video_uri": "http://video.seattle.gov:8080/media/council/gen_062717V.mp4",
    "event_datetime": "2017-06-27T00:00:00",
    "body_id": "6f38a688-2e96-4e33-841c-883738f9f03d"
}


@pytest.fixture
def mock_response_item():
    with mock.patch("requests.get") as MockRequest:
        MockRequest.return_value = MockedResponse(RESPONSE_ITEM)
        yield MockRequest


@pytest.fixture
def mock_response_items():
    with mock.patch("requests.get") as MockRequest:
        MockRequest.return_value = MockedResponse({"documents": [RESPONSE_ITEM]})
        yield MockRequest


@pytest.fixture
def no_creds_db() -> CloudFirestoreDatabase:
    return CloudFirestoreDatabase("stg-cdp-seattle")


@pytest.fixture
def creds_db() -> CloudFirestoreDatabase:
    with mock.patch("cdptools.databases.cloud_firestore_database.CloudFirestoreDatabase._initialize_creds_db"):
        db = CloudFirestoreDatabase("/fake/path/to/creds.json")
        db._credentials_path = "/fake/path/to/creds.json"
        db._root = mock.Mock(firestore.Client)
        db._root.collection.return_value = MockedCollection([MockedDocument(
            "0e3bd59c-3f07-452c-83cf-e9eebeb73af2",
            EVENT_VALUES
        )])

        return db


@pytest.fixture
def empty_creds_db() -> CloudFirestoreDatabase:
    with mock.patch("cdptools.databases.cloud_firestore_database.CloudFirestoreDatabase._initialize_creds_db"):
        db = CloudFirestoreDatabase("/fake/path/to/creds.json")
        db._credentials_path = "/fake/path/to/creds.json"
        db._root = mock.Mock(firestore.Client)
        db._root.collection.return_value = MockedCollection([])

        return db


@pytest.mark.parametrize("project_id, credentials_path", [
    ("stg-cdp-seattle", None),
    pytest.param(None, "/this/path/doesnt/exist.json", marks=pytest.mark.raises(exception=FileNotFoundError)),
    pytest.param(None, None, marks=pytest.mark.raises(exception=exceptions.MissingParameterError))
])
def test_cloud_firestore_database_init(project_id, credentials_path):
    CloudFirestoreDatabase(project_id, credentials_path)


@pytest.mark.parametrize("pks", [
    ([("video_uri", "does_not_exist")]),
    ([("video_uri", "http://video.seattle.gov:8080/media/council/gen_062717V.mp4")])
])
def test_get_or_upload_row(no_creds_db, creds_db, empty_creds_db, pks):
    with pytest.raises(exceptions.MissingCredentialsError):
        no_creds_db._get_or_upload_row("event", pks, EVENT_VALUES)

    creds_db._get_or_upload_row("event", pks, EVENT_VALUES)
    empty_creds_db._get_or_upload_row("event", pks, EVENT_VALUES)


def test_cloud_firestore_database_select_row(no_creds_db, creds_db, mock_response_item):
    no_creds_db.select_row_by_id("event", "0e3bd59c-3f07-452c-83cf-e9eebeb73af2")
    creds_db.select_row_by_id("event", "0e3bd59c-3f07-452c-83cf-e9eebeb73af2")


@pytest.mark.parametrize("filters, order_by, limit", [
    (None, None, None),
    ([("video_uri", "http://video.seattle.gov:8080/media/council/gen_062717V.mp4")], None, None),
    ([("video_uri", "http://video.seattle.gov:8080/media/council/gen_062717V.mp4")], "video_uri", None),
    ([("video_uri", "http://video.seattle.gov:8080/media/council/gen_062717V.mp4")], None, 10),
    ([("video_uri", "http://video.seattle.gov:8080/media/council/gen_062717V.mp4")], "video_uri", 10),
    (None, "video_uri", None),
    (None, "video_uri", 10),
    (None, None, 10),
    pytest.param(None, 12, None, marks=pytest.mark.raises(exception=TypeError))
])
def test_cloud_firestore_database_select_rows(no_creds_db, creds_db, mock_response_items, filters, order_by, limit):
    no_creds_db.select_rows_as_list("event", filters, order_by, limit)
    creds_db.select_rows_as_list("event", filters, order_by, limit)


@pytest.mark.parametrize("pks, n_expected", [
    ([("video_uri", "http://video.seattle.gov:8080/media/council/gen_062717V.mp4")], 1),
    pytest.param(
        [("video_uri", "http://video.seattle.gov:8080/media/council/gen_062717V.mp4")],
        0,
        marks=pytest.mark.raises(exception=exceptions.UniquenessError)
    )
])
def test_cloud_firestore_database_max_expectation(no_creds_db, creds_db, pks, n_expected):
    creds_db._select_rows_with_max_results_expectation("event", pks, n_expected)
