#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from pathlib import Path
from requests import RequestException

from unittest.mock import Mock

import pytest

from cdptools.sr_models.webvtt_sr_model import WebVttSRModel


@pytest.fixture
def fake_caption(data_dir) -> Path:
    return data_dir / "fake_caption.vtt"


@pytest.fixture
def fake_sentences(data_dir) -> Path:
    return data_dir / "fake_timestamped_sentences.json"


@pytest.fixture
def example_webvtt_sr_model() -> WebVttSRModel:
    webvtt_sr_model = WebVttSRModel("&gt;")
    return webvtt_sr_model


# Check whether WebvttSRModel raise an RequestException if the uri of caption file is invalid
def test_request_caption_content(example_webvtt_sr_model):
    with pytest.raises(RequestException):
        example_webvtt_sr_model._request_caption_content("invalid-source-uri")


# Check whether timestamped sentences of fake_caption equals fake_sentences
def test_get_sentences(example_webvtt_sr_model, fake_caption, fake_sentences):
    with open(fake_caption, "r") as fake_caption_file:
        caption_text = fake_caption_file.read()

    example_webvtt_sr_model._request_caption_content = Mock(return_value=caption_text)

    with open(fake_sentences) as json_file:
        timestamped_sentences = json.load(json_file)

    example_webvtt_sr_model._request_caption_content = Mock(return_value=caption_text)

    assert example_webvtt_sr_model._get_sentences("any-caption-uri") == timestamped_sentences


def test_webvtt_sr_model_transcribe(example_webvtt_sr_model, fake_sentences, tmpdir):
    with open(fake_sentences) as json_file:
        timestamped_sentences = json.load(json_file)

    example_webvtt_sr_model._get_sentences = Mock(return_value=timestamped_sentences)

    example_webvtt_sr_model.transcribe("any-caption-uri", tmpdir / "raw.json", tmpdir / "speaker_turns.json")
