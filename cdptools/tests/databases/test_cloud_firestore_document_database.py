#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from unittest import mock

import pytest
from cdptools.databases import WhereOperators, exceptions
from cdptools.databases.cloud_firestore_document_database import (
    CloudFirestoreDocumentDatabase,
    CloudFirestoreWhereOperators,
    NoCredResponseTypes,
)
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


VOTE_ITEM = {
    "name": "projects/fake-cdp-instance/databases/(default)/documents/vote/a-vote-item-id",  # noqa: E501
    "fields": {
        "matter": {
            "id": "matter_id",
            "name": "matter_name",
            "title": "matter_title",
            "type": "matter_type",
        },
        "event": {
            "id": "event_id",
            "body_name": "event_body_name",
            "event_datetime": "2017-06-27T00:00:00",
        },
        "event_minutes_item": {"id": "event_minutes_item_id", "decision": "passed"},
        "person": {"id": "person_id", "name": "person_name"},
        "vote_decision": {"stringValue": "passed"},
        "is_majority": {"booleanValue": True},
        "created": {"timestampValue": "2019-04-21T23:58:04.832481Z"},
        "test_boolean_value": {"booleanValue": True},
        "test_null_value": {"nullValue": None},
        "test_float_value": {"doubleValue": "12.12"},
        "test_integer_value": {"integerValue": "12"},
    },
}

VOTE_ITEMS = [{"document": VOTE_ITEM}]

VOTE_VALUES = {
    "matter": {
        "id": "matter_id",
        "name": "matter_name",
        "title": "matter_title",
        "type": "matter_type",
    },
    "event": {
        "id": "event_id",
        "body_name": "event_body_name",
        "event_datetime": "2017-06-27T00:00:00",
    },
    "event_minutes_item": {"id": "event_minutes_item_id", "decision": "passed"},
    "person": {"id": "person_id", "name": "person_name"},
    "vote_decision": "passed",
    "is_majority": True,
    "created": datetime.utcnow(),
}


@pytest.fixture
def no_creds_db() -> CloudFirestoreDocumentDatabase:
    return CloudFirestoreDocumentDatabase("this-is-a-fake-database-hi")


@pytest.fixture
def creds_db() -> CloudFirestoreDocumentDatabase:
    with mock.patch(
        "cdptools.databases.cloud_firestore_document_database.CloudFirestoreDocumentDatabase._initialize_creds_db"  # noqa: E501
    ):
        db = CloudFirestoreDocumentDatabase("/fake/path/to/creds.json")
        db._credentials_path = "/fake/path/to/creds.json"
        db._root = mock.Mock(firestore.Client)
        db._root.collection.return_value = MockedCollection(
            [MockedDocument("a-vote-item-id", VOTE_VALUES)]
        )

        return db


@pytest.fixture
def empty_creds_db() -> CloudFirestoreDocumentDatabase:
    with mock.patch(
        "cdptools.databases.cloud_firestore_document_database.CloudFirestoreDocumentDatabase._initialize_creds_db"  # noqa: E501
    ):
        db = CloudFirestoreDocumentDatabase("/fake/path/to/creds.json")
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
def test_cloud_firestore_document_database_init(project_id, credentials_path):
    CloudFirestoreDocumentDatabase(project_id, credentials_path)


@pytest.mark.parametrize(
    "pks",
    [
        ([("person.id", "event_minutes_item.id")]),
        (
            [
                ("person.id", "person_id",),
                ("event_minutes_item.id", "event_minutes_item_id"),
            ]
        ),
    ],
)
def test_get_or_upload_document(no_creds_db, creds_db, empty_creds_db, pks):
    with pytest.raises(exceptions.MissingCredentialsError):
        no_creds_db._get_or_upload_document("vote", pks, VOTE_VALUES)

    creds_db._get_or_upload_document("vote", pks, VOTE_VALUES)
    empty_creds_db._get_or_upload_document("vote", pks, VOTE_VALUES)


def test_cloud_firestore_document_database_select_document(no_creds_db, creds_db):
    # Mock requests
    with mock.patch("requests.get") as mocked_request:
        mocked_request.return_value = MockedResponse(VOTE_ITEM)
        no_creds_db.select_document_by_id("vote", "a-vote-item-id")

    creds_db.select_document_by_id("vote", "a-vote-item-id")


@pytest.mark.parametrize(
    "filters, order_by, limit",
    [
        (None, None, None),
        (
            [
                ("person.id", "person_id",),
                ("event_minutes_item.id", "event_minutes_item_id"),
            ],
            None,
            None,
        ),
        (
            [
                ("person.id", "person_id",),
                ("event_minutes_item.id", "event_minutes_item_id"),
            ],
            "person.id",
            None,
        ),
        (
            [
                ("person.id", "person_id",),
                ("event_minutes_item.id", "event_minutes_item_id"),
            ],
            None,
            10,
        ),
        (None, "event_minutes_item.id", None),
        (None, "person.id", 10),
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
def test_cloud_firestore_document_database_select_documents_as_list(
    no_creds_db, creds_db, filters, order_by, limit
):
    # Mock requests
    with mock.patch("requests.post") as mocked_request:
        mocked_request.return_value = MockedResponse(VOTE_ITEMS)
        no_creds_db.select_documents_as_list("vote", filters, order_by, limit)

    creds_db.select_documents_as_list("vote", filters, order_by, limit)


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
        CloudFirestoreDocumentDatabase._convert_base_where_operator_to_cloud_firestore_where_operator(  # noqa: E501
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
    assert (
        CloudFirestoreDocumentDatabase._get_cloud_firestore_value_type(val) == expected
    )  # noqa: E501


@pytest.mark.parametrize(
    "pks, n_expected",
    [
        (
            [
                ("person.id", "person_id",),
                ("event_minutes_item.id", "event_minutes_item_id"),
            ],
            1,
        ),
        pytest.param(
            [
                ("person.id", "person_id",),
                ("event_minutes_item.id", "event_minutes_item_id"),
            ],
            0,
            marks=pytest.mark.raises(exception=exceptions.UniquenessError),
        ),
    ],
)
def test_cloud_firestore_document_database_max_expectation(
    no_creds_db, creds_db, pks, n_expected
):
    # Mock requests
    with mock.patch("requests.post") as mocked_request:
        mocked_request.return_value = MockedResponse(VOTE_ITEMS)
        no_creds_db._select_documents_with_max_results_expectation(
            "vote", pks, n_expected
        )  # noqa: E501

    creds_db._select_documents_with_max_results_expectation("vote", pks, n_expected)
