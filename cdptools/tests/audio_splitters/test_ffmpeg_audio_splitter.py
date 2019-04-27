#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import pytest
from unittest import mock

from cdptools.audio_splitters.ffmpeg_audio_splitter import FFmpegAudioSplitter


@pytest.fixture
def example_video(data_dir) -> Path:
    return data_dir / "example.mp4"


@pytest.mark.parametrize("audio_save_path", [
    ("test.wav"),
    (Path("test.wav")),
    pytest.param(__file__, marks=pytest.mark.raises(exception=FileExistsError)),
    pytest.param(Path(__file__), marks=pytest.mark.raises(exception=FileExistsError)),
    pytest.param(Path(__file__).parent, marks=pytest.mark.raises(exception=IsADirectoryError))
])
def test_mocked_save_path(tmpdir, example_video, audio_save_path):
    # Append save name to tmpdir
    audio_save_path = Path(tmpdir) / audio_save_path

    # Initialize splitter
    splitter = FFmpegAudioSplitter()

    # Mock split
    with mock.patch("ffmpeg.run") as mocked_ffmpeg:
        mocked_ffmpeg.return_value = (b"OUTPUT", b"ERROR")
        splitter.split(video_read_path=example_video, audio_save_path=audio_save_path)
