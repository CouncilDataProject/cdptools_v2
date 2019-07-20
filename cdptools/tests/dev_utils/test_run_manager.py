#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from unittest import mock

import pytest
from firebase_admin import firestore
from google.cloud import storage

from cdptools.databases.cloud_firestore_database import CloudFirestoreDatabase
from cdptools.dev_utils import RunIO, RunManager
from cdptools.file_stores.gcs_file_store import GCSFileStore

from ..databases.test_cloud_firestore_database import MockedCollection
from ..file_stores.test_gcs_file_store import MockedBlob, MockedBucket


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
def example_audio(data_dir) -> Path:
    return data_dir / "example_audio.wav"


@pytest.mark.parametrize("inputs, expected", [
    ([RunIO(str(str), "hello")], [RunIO(str(str), "hello")]),
    ([RunIO(str(int), 1)], [RunIO(str(int), 1)]),
    ([[str, "hello"]], [RunIO(str(str), "hello")]),
    ([[int, 1]], [RunIO(str(int), 1)]),
    ([[1.0]], [RunIO(str(float), 1.0)]),
    pytest.param([["this", "will", "fail"]], None, marks=pytest.mark.raises(exception=ValueError)),
    ([(str, "hello")], [RunIO(str(str), "hello")]),
    ([(int, 1)], [RunIO(str(int), 1)]),
    ([(1.0)], [RunIO(str(float), 1.0)]),
    pytest.param([("this", "will", "fail")], None, marks=pytest.mark.raises(exception=ValueError)),
    ([RunIO(str(str), "hello"), RunIO(str(str), "world")], [RunIO(str(str), "hello"), RunIO(str(str), "world")])
])
def test_run_manager_init(empty_creds_db, empty_creds_fs, inputs, expected):
    with RunManager(
        database=empty_creds_db,
        file_store=empty_creds_fs,
        algorithm_name="fake",
        algorithm_version="1.1.1",
        inputs=inputs
    ) as run:
        assert run._inputs == expected


def test_make_serializable_type(empty_creds_db, empty_creds_fs, data_dir, example_audio):
    # Test with real path
    with RunManager(
        database=empty_creds_db,
        file_store=empty_creds_fs,
        algorithm_name="fake",
        algorithm_version="1.1.1",
        inputs=[example_audio]
    ) as run:
        # Can't use PosixPath because if testing is done on windows then this fails
        for i in run._input_files:
            assert "Path" in i.type
            assert isinstance(i.value, Path)

    # Test with non existent path
    with pytest.raises(FileNotFoundError):
        run = RunManager(
            database=empty_creds_db,
            file_store=empty_creds_fs,
            algorithm_name="fake",
            algorithm_version="1.1.1",
            inputs=[Path("/this/will/fail.mp4")]
        )

    # Test with directory
    with pytest.raises(IsADirectoryError):
        run = RunManager(
            database=empty_creds_db,
            file_store=empty_creds_fs,
            algorithm_name="fake",
            algorithm_version="1.1.1",
            inputs=[data_dir]
        )

    # With any other type
    with RunManager(
        database=empty_creds_db,
        file_store=empty_creds_fs,
        algorithm_name="fake",
        algorithm_version="1.1.1",
        inputs=[((str(tuple), ("this", "will", "be", "cast", "to", "string")))]
    ) as run:
        assert run._inputs == [RunIO(str(tuple), "('this', 'will', 'be', 'cast', 'to', 'string')")]


def test_run_manager_safe_exit(empty_creds_db, empty_creds_fs):
    with RunManager(
        database=empty_creds_db,
        file_store=empty_creds_fs,
        algorithm_name="fake",
        algorithm_version="1.1.1"
    ) as run:
        run.register_output(1)


def test_run_manager_failed_exit(empty_creds_db, empty_creds_fs):
    # Generate exception log
    with pytest.raises(AssertionError):
        with RunManager(
            database=empty_creds_db,
            file_store=empty_creds_fs,
            algorithm_name="fake",
            algorithm_version="1.1.1"
        ):
            assert False

    # Check exception log exists
    logs = list(Path(".").glob("exception_log_*.err"))
    assert len(logs) == 1

    # Clean up exception log
    for log in logs:
        log.unlink()
