#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from pathlib import Path

import pytest

from cdptools.indexers import Indexer


@pytest.fixture
def example_transcript_raw(data_dir) -> Path:
    return data_dir / "example_transcript_raw.json"


@pytest.fixture
def example_transcript_words(data_dir) -> Path:
    return data_dir / "example_transcript_words.json"


@pytest.fixture
def example_transcript_sentences(data_dir) -> Path:
    return data_dir / "example_transcript_sentences.json"


@pytest.fixture
def example_audio(data_dir) -> Path:
    return data_dir / "example_audio.wav"


@pytest.fixture
def example_event_pipeline_config(data_dir) -> Path:
    return data_dir / "example_event_pipeline_config.json"


def test_get_raw_transcript_formats(
    example_transcript_raw,
    example_transcript_words,
    example_transcript_sentences,
    example_audio,
    example_event_pipeline_config,
):
    # Get raw for format testing
    with open(example_transcript_raw, "r") as read_in:
        raw_transcript = json.load(read_in)
        raw_transcript = raw_transcript["data"][0]["text"]

    result = Indexer.get_raw_transcript(example_transcript_raw)
    assert isinstance(result, str)
    assert result == raw_transcript

    result = Indexer.get_raw_transcript(example_transcript_words)
    assert isinstance(result, str)
    assert result == raw_transcript

    result = Indexer.get_raw_transcript(example_transcript_sentences)
    assert isinstance(result, str)
    assert result == raw_transcript

    # Check formats that should fail
    with pytest.raises(TypeError):
        Indexer.get_raw_transcript(example_audio)

    with pytest.raises(TypeError):
        Indexer.get_raw_transcript(example_event_pipeline_config)


@pytest.mark.parametrize("text, expected", [
    ("hello world", "hello world"),
    ("hello ", "hello"),
    ("the quick brown fox jumps over the running ant", "quick brown fox jump run ant"),
    ("The quick brown fox jumps over the running ant", "quick brown fox jump run ant"),
    ("thE quICk BROwn Fox JuMps OVER the RUNning ANt", "quick brown fox jump run ant"),
    ("1 billion", "1 billion"),
    ("98%", "98 percent"),
    ("1.4 Million", "1 point 4 million"),
    ("Will this remove punctuation?!%'", "remov punctuat"),
    ("$10 10.5% $5.5 2%", "10 dollar 10 point 5 percent 5 point 5 dollar 2 percent"),
    # Unsure how to handle this to the best case, but works okay for now
    # Best case: "study report cost 14 point 8 thousand dollar"
    # Best case: dollar is placed after thousand
    ("The study will reportedly cost $14.8 thousand", "studi reportedli cost 14 point 8 dollar thousand")
])
def test_clean_text_for_indexing(text, expected):
    result = Indexer.clean_text_for_indexing(text)
    assert result == expected
