#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from pathlib import Path
from requests import RequestException

from unittest.mock import Mock

import pytest

from cdptools.sr_models.webvtt_sr_model import WebVTTSRModel


@pytest.fixture
def fake_caption(data_dir) -> Path:
    return data_dir / "fake_caption.vtt"


@pytest.fixture
def fake_timestamped_sentences(data_dir) -> Path:
    return data_dir / "fake_timestamped_sentences.json"


@pytest.fixture
def example_webvtt_sr_model() -> WebVTTSRModel:
    webvtt_sr_model = WebVTTSRModel("&gt;")
    return webvtt_sr_model


# Check whether WebVTTSRModel raise an RequestException if the uri of caption file is invalid
def test_webvtt_sr_model_request_caption_content(example_webvtt_sr_model):
    with pytest.raises(RequestException):
        example_webvtt_sr_model._request_caption_content("invalid-caption-uri")


# Check whether timestamped sentences of fake_caption equals fake_timestamped_sentences
def test_webvtt_sr_model_get_sentences(example_webvtt_sr_model, fake_caption, fake_timestamped_sentences):
    with open(fake_caption, "r") as fake_caption_file:
        caption_text = fake_caption_file.read()

    example_webvtt_sr_model._request_caption_content = Mock(return_value=caption_text)

    with open(fake_timestamped_sentences) as json_file:
        timestamped_sentences = json.load(json_file)

    example_webvtt_sr_model._request_caption_content = Mock(return_value=caption_text)

    assert example_webvtt_sr_model._get_sentences("any-caption-uri") == timestamped_sentences


def test_webvtt_sr_model_transcribe(example_webvtt_sr_model, fake_timestamped_sentences, tmpdir):
    with open(fake_timestamped_sentences) as json_file:
        timestamped_sentences = json.load(json_file)

    example_webvtt_sr_model._get_sentences = Mock(return_value=timestamped_sentences)

    example_webvtt_sr_model.transcribe(
        "any-caption-uri",
        tmpdir / "raw.json",
        tmpdir / "timestamped_sentences.json",
        tmpdir / "timestamped_speaker_turns.json",
    )
