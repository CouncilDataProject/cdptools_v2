#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from requests import RequestException

from unittest.mock import Mock
from webvtt.structures import Caption

import pytest

from cdptools.sr_models.webvtt_sr_model import WebVTTSRModel


@pytest.fixture
def fake_caption(data_dir) -> Path:
    return data_dir / "fake_caption.vtt"


@pytest.fixture
def example_webvtt_sr_model() -> WebVTTSRModel:
    webvtt_sr_model = WebVTTSRModel("&gt;")
    return webvtt_sr_model


# Check whether WebVTTSRModel raise an RequestException if the uri of caption file is invalid
def test_webvtt_sr_model_request_caption_content(example_webvtt_sr_model):
    with pytest.raises(RequestException):
        example_webvtt_sr_model._request_caption_content("invalid-caption-uri")


@pytest.mark.parametrize("captions, expected", [
    (
        [
            Caption(text="&gt;&gt; Start of Dialog 1."),
            Caption(text="End of Dialog 1."),
            Caption(text="&gt;&gt; [ APPLAUSE ] "),
            Caption(text="&gt;&gt; Dialog 2.")
        ],
        [2, 1, 1]
    ),
    (
        [
            Caption(text="&gt;&gt; Dialog 1."),
            Caption(text="&gt;&gt; [ ROLL BEING CALLED ] "),
            Caption(text="&gt;&gt; Dialog 2."),
        ],
        [1, 1, 1]
    ),
    (
        [
            Caption(text="&gt;&gt; [ LAUGHTER ] Dialog 1."),
            Caption(text="&gt;&gt; [ APPLAUSE ]"),
            Caption(text="&gt;&gt; Dialog 2.")
        ],
        [1, 1, 1]
    ),
    (
        [
            Caption(text="&gt;&gt; Sentence"),
            Caption(text="one."),
            Caption(text="&gt;&gt; Sentence"),
            Caption(text="two!"),
            Caption(text="Sentence"),
            Caption(text="three!"),
            Caption(text="Sentence"),
            Caption(text="four?")
        ],
        [1, 3]
    ),
    (
        [
            Caption(text="&gt;&gt; Sentence"),
            Caption(text="one, no sentence ending punctuation"),
            Caption(text="&gt;&gt; Sentence"),
            Caption(text="two.")
        ],
        [1, 1]
    ),
    (
        [
            Caption(text="Sentence one."),
            Caption(text="ú&gt;&gt; Sentence two.")
        ],
        [1, 1]
    )
])
def test_webvtt_sr_model_create_timestamped_speaker_turns(
    captions,
    expected,
    example_webvtt_sr_model
):
    speaker_turns = example_webvtt_sr_model._get_speaker_turns(captions)
    timestamped_speaker_turns = example_webvtt_sr_model._create_timestamped_speaker_turns(speaker_turns)
    # Check if the number of speaker turns is correct
    assert len(timestamped_speaker_turns) == len(expected)
    # Check if the number of sentences per speaker turn is correct
    for i, number_of_sentences in enumerate(expected):
        assert len(timestamped_speaker_turns[i]["data"]) == number_of_sentences


def test_webvtt_sr_model_transcribe(example_webvtt_sr_model, fake_caption, tmpdir):
    with open(fake_caption, "r") as fake_caption_file:
        caption_text = fake_caption_file.read()

    example_webvtt_sr_model._request_caption_content = Mock(return_value=caption_text)

    example_webvtt_sr_model.transcribe(
        "any-caption-uri",
        tmpdir / "raw.json",
        tmpdir / "timestamped_sentences.json",
        tmpdir / "timestamped_speaker_turns.json",
    )
