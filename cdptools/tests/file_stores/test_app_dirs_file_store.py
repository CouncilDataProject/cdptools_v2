#!/usr/bin/env python
# -*- coding: utf-8 -*-

import shutil
from pathlib import Path
from unittest import mock

import pytest

from cdptools.file_stores.app_dirs_file_store import AppDirsFileStore


@pytest.fixture
def fs(tmpdir):
    with mock.patch("appdirs.user_data_dir") as MockAppDirs:
        MockAppDirs.return_value = tmpdir
        fs = AppDirsFileStore()
        return fs


@pytest.fixture
def example_video(data_dir):
    return Path(data_dir) / "example_video.mp4"


@pytest.fixture
def mock_compute_sha256():
    with mock.patch("cdptools.file_stores.file_store.FileStore.compute_sha256_for_file") as MockSHA:
        MockSHA.return_value = "936a185caaa266bb9cbe981e9e05cb78cd732b0b3280eb944412bb6f8f8f07af"
        yield MockSHA


@pytest.mark.parametrize("filename", [
    ("file.mp3"),
    (Path("file.mp3")),
    ("/path/to/a/file.mp3"),
    (Path("/path/to/a/file.mp3"))
])
def test_locate_file(fs, mock_compute_sha256, filename):
    fs._locate_file(filename)


@pytest.mark.parametrize("save_name, remove", [
    (None, False),
    ("file.mp4", False),
    (Path("file.mp4"), False),
    (None, True),
    ("file.mp4", True),
    (Path("file.mp4"), True)
])
def test_upload_file(fs, mock_compute_sha256, tmpdir, example_video, save_name, remove):
    tmp_input_path = shutil.copyfile(example_video, tmpdir / "tmp.mp4")
    fs.upload_file(tmp_input_path, save_name, remove)
    if remove:
        assert not Path(tmp_input_path).exists()


@pytest.mark.parametrize("filename, save_path", [
    ("file.mp4", "saved_out.mp4"),
    ("file.mp4", Path("saved_out.mp4")),
    pytest.param("does_not_exist.mp4", "not_going_to_exist.mp4", marks=pytest.mark.raises(exception=FileNotFoundError))
])
def test_download_file(fs, mock_compute_sha256, tmpdir, example_video, filename, save_path):
    # Upload file
    tmp_input_path = shutil.copyfile(example_video, tmpdir / "tmp.mp4")
    fs.upload_file(tmp_input_path, "file.mp4")

    # Send save out to tmpdir
    save_path = tmpdir / save_path

    # Attempt download
    fs.download_file(filename, save_path)
