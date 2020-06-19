#!/usr/bin/env python
# -*- coding: utf-8 -*-

import shutil
from pathlib import Path
from unittest import mock

import pytest
from google.cloud import storage

from cdptools.file_stores import exceptions
from cdptools.file_stores.gcs_file_store import GCSFileStore


@pytest.fixture
def example_video(data_dir):
    return data_dir / "example_video.mp4"


class MockedResponse:
    def __init__(self, filepath):
        self.filepath = filepath
        self.opened = open(self.filepath, "rb")

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, tb):
        self.opened.close()

    def raise_for_status(self):
        return True

    @property
    def raw(self):
        return self.opened


@pytest.fixture
def mocked_request(example_video):
    with mock.patch("requests.get") as MockRequest:
        MockRequest.return_value = MockedResponse(example_video)
        yield MockRequest


class MockedBlob:
    def __init__(self, filename, exists=True):
        self.filename = filename
        self._exists = exists

    def exists(self):
        return self._exists

    def upload_from_filename(self, filename, content_type):
        self.filename = filename
        return filename

    def download_to_filename(self, save_path, overwrite=True):
        return save_path


class MockedBucket:
    def __init__(self, name, files):
        self.name = name
        self.files = files

    def blob(self, filename):
        return self.files[0]


@pytest.fixture
def no_creds_fs() -> GCSFileStore:
    return GCSFileStore("fake-cdp-instance.appspot.com")


@pytest.fixture
def creds_fs() -> GCSFileStore:
    with mock.patch(
        "cdptools.file_stores.gcs_file_store.GCSFileStore._initialize_creds_fs"
    ):
        fs = GCSFileStore("/fake/path/to/creds.json")
        fs._credentials_path = "/fake/path/to/creds.json"
        fs._client = mock.Mock(storage.Client)
        fs._bucket = MockedBucket("fake_bucket", [MockedBlob("example.mp4")])

        return fs


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


@pytest.mark.parametrize(
    "bucket_name, credentials_path",
    [
        ("fake-cdp-instance.appspot.com", None),
        pytest.param(
            None,
            "/this/path/doesnt/exist.json",
            marks=pytest.mark.raises(exception=FileNotFoundError),
        ),
    ],
)
def test_gcs_file_store_init(bucket_name, credentials_path):
    GCSFileStore(bucket_name, credentials_path)


def test_get_file_uri(no_creds_fs, creds_fs, mocked_request):
    no_creds_fs.get_file_uri("example.mp4")
    creds_fs.get_file_uri("example.mp4")


@pytest.mark.parametrize(
    "save_name, content_type",
    [
        (None, None),
        ("file.mp4", None),
        (Path("file.mp4"), None),
        (None, None),
        ("file.mp4", None),
        (Path("file.mp4"), None),
        ("file.mp4", "video/ogg"),
    ],
)
def test_upload_file(
    no_creds_fs,
    creds_fs,
    empty_creds_fs,
    tmpdir,
    example_video,
    save_name,
    content_type,
):
    tmp_input_path = shutil.copyfile(example_video, tmpdir / "tmp.mp4")

    # Attempt with missing creds
    with pytest.raises(exceptions.MissingCredentialsError):
        no_creds_fs.upload_file(tmp_input_path, save_name, content_type, False)

    # Attempt with creds
    creds_fs.upload_file(tmp_input_path, save_name, content_type, False)
    empty_creds_fs.upload_file(tmp_input_path, save_name, content_type, True)
    assert not Path(tmp_input_path).exists()


@pytest.mark.parametrize(
    "filename, save_path",
    [("file.mp4", "saved_out.mp4"), ("file.mp4", Path("saved_out.mp4"))],
)
def test_download_file(
    no_creds_fs, creds_fs, tmpdir, mocked_request, example_video, filename, save_path
):
    # Send save out to tmpdir
    save_path = tmpdir / save_path

    # Attempt download
    no_creds_fs.download_file(filename, save_path)

    # No overwrite
    with pytest.raises(FileExistsError):
        creds_fs.download_file(filename, save_path)

    creds_fs.download_file(filename, save_path, overwrite=True)
