#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import pytest
from unittest import mock

from cdptools.file_stores.file_store import FileStore


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


@pytest.mark.parametrize("uri, expected", [
    ("/this/is/local.mp3", True),
    (Path("/this/is/local.mp3"), True),
    ("http://external.mp3", False),
    ("https://external.mp3", False),
    ("gc://external.mp3", False),
    ("s3://external.mp3", False)
])
def test_path_is_local(uri, expected):
    actual = FileStore._path_is_local(uri)

    assert actual == expected


def test_compute_sha256_for_file(example_video):
    FileStore.compute_sha256_for_file(example_video)


def test_external_resource_copy(tmpdir, mocked_request):
    save_path = tmpdir / "tmpcopy.mp4"
    FileStore._external_resource_copy("https://doesntmatter.com/example.mp4", save_path)
