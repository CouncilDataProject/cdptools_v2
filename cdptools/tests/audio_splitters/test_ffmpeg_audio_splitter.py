#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import pytest
from unittest import mock

from cdptools.audio_splitters.ffmpeg_audio_splitter import FFmpegAudioSplitter


@pytest.fixture(scope="module", autouse=True)
def example_video(data_dir) -> Path:
    return data_dir / "example.mp4"

# When this fixture is passed, it will catch requests for ffmpeg.run
@pytest.fixture(scope="module", autouse=True)
def mocked_ffmpeg():
    with mock.patch("ffmpeg") as MockFFmpeg:
        MockFFmpeg.run.return_value = ("hello", "world")
        yield MockFFmpeg


@pytest.fixture(autouse=True)
def test_real_audio_split(tmpdir, example_video):
    # Initialize splitter
    splitter = FFmpegAudioSplitter()

    # Create fake out path
    fake_save_path = tmpdir / "fake.wav"

    # Split
    splitter.split(video_read_path=example_video, audio_save_path=fake_save_path)


@pytest.fixture(autouse=True)
@pytest.mark.parametrize("audio_save_path", [
    ("~/this/is/a/test.wav"),
    (Path("~/this/is/a/test.wav")),
    pytest.param(__file__, marks=pytest.mark.raises(exception=FileExistsError)),
    pytest.param(Path(__file__), marks=pytest.mark.raises(exception=FileExistsError)),
    pytest.param(Path(__file__).parent, marks=pytest.mark.raises(exception=IsADirectoryError))
])
def test_mocked_save_path(example_video, audio_save_path, mocked_ffmpeg):
    # Initialize splitter
    splitter = FFmpegAudioSplitter()

    # Mock split
    splitter.split(video_read_path=example_video, audio_save_path=audio_save_path)
