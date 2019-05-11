#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from cdptools.pipelines.pipeline import Pipeline


@pytest.mark.parametrize("module_path, object_name, object_kwargs", [
    ("pathlib", "Path", {}),
    ("cdptools.audio_splitters.ffmpeg_audio_splitter", "FFmpegAudioSplitter", {}),
    (["cdptools", "audio_splitters", "ffmpeg_audio_splitter"], "FFmpegAudioSplitter", {}),
    ("datetime", "datetime", {"year": 2019, "month": 5, "day": 11}),
    pytest.param("fake.module.path", "DoesNotExist", {}, marks=pytest.mark.raises(exception=ModuleNotFoundError)),
    pytest.param("datetime", "DoesNotExist", {}, marks=pytest.mark.raises(exception=AttributeError))
])
def test_load_custom_object(module_path, object_name, object_kwargs):
    Pipeline.load_custom_object(module_path, object_name, object_kwargs)
