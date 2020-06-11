#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from pathlib import Path

import pytest
from cdptools.indexers import Indexer, exceptions


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
def example_timestamped_speaker_turns(data_dir) -> Path:
    return data_dir / "example_transcript_speaker_turns.json"


@pytest.fixture
def example_transcript_speaker_turns_raw(data_dir) -> Path:
    return data_dir / "example_transcript_speaker_turns_raw.json"


@pytest.fixture
def example_audio(data_dir) -> Path:
    return data_dir / "example_audio.wav"


@pytest.fixture
def example_event_pipeline_config(data_dir) -> Path:
    return data_dir / "example_event_pipeline_config.json"


@pytest.fixture
def example_invalid_transcript_format(data_dir) -> Path:
    return data_dir / "example_invalid_transcript_format.json"


@pytest.fixture
def indexed_results():
    return {
        "hello": {"event_0": 0.0, "event_1": 0.0},
        "world": {"event_0": 0.0, "event_1": 0.0},
        "name": {"event_0": 0.6931471805599453},
        "jackson": {"event_0": 0.6931471805599453},
        "internet": {"event_1": 0.6931471805599453},
        "gener": {"event_1": 0.6931471805599453},
        "go": {"event_1": 0.6931471805599453},
        "maxfield": {"event_1": 0.6931471805599453},
    }


DROPPED_ZEROS_INDEX = {
    "name": {"event_0": 0.6931471805599453},
    "jackson": {"event_0": 0.6931471805599453},
    "internet": {"event_1": 0.6931471805599453},
    "gener": {"event_1": 0.6931471805599453},
    "go": {"event_1": 0.6931471805599453},
    "maxfield": {"event_1": 0.6931471805599453},
}


def test_get_raw_transcript_formats(
    example_transcript_raw,
    example_transcript_words,
    example_transcript_sentences,
    example_timestamped_speaker_turns,
    example_transcript_speaker_turns_raw,
    example_audio,
    example_event_pipeline_config,
    example_invalid_transcript_format,
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

    # Get raw for speaker turns testing
    with open(example_transcript_speaker_turns_raw, "r") as read_in:
        speaker_turns_raw = json.load(read_in)
        speaker_turns_raw = speaker_turns_raw["data"][0]["text"]

    result = Indexer.get_raw_transcript(example_timestamped_speaker_turns)
    assert isinstance(result, str)
    assert result == speaker_turns_raw

    # Check formats that should fail
    with pytest.raises(exceptions.UnrecognizedTranscriptFormatError):
        Indexer.get_raw_transcript(example_audio)

    with pytest.raises(exceptions.UnrecognizedTranscriptFormatError):
        Indexer.get_raw_transcript(example_event_pipeline_config)

    with pytest.raises(exceptions.UnrecognizedTranscriptFormatError):
        Indexer.get_raw_transcript(example_invalid_transcript_format)


@pytest.mark.parametrize(
    "term, expected",
    [
        ("hello", False),
        ("Thanks.", True),
        ("didn't", False),
        ("No!", True),
        ("Is that a question?", True),
        pytest.param(1, None, marks=pytest.mark.raises(exception=TypeError)),
    ],
)
def test_term_is_end_of_sentence(term, expected):
    assert Indexer.term_is_end_of_sentence(term) == expected


@pytest.mark.parametrize(
    "terms, index, expected",
    [
        (["Hello", "and", "good", "morning."], 0, "Hello and good morning."),
        (
            [
                "But",
                "I",
                "don't",
                "think",
                "the",
                "barrier",
                "is",
                "so",
                "high",
                "to",
                "allow",
                "individuals",
                "to",
                "use",
                "the",
                "service.",
            ],
            0,
            "But I don't think the barrier is so high to ...",
        ),
        (
            [
                "But",
                "I",
                "don't",
                "think",
                "the",
                "barrier",
                "is",
                "so",
                "high",
                "to",
                "allow",
                "individuals",
                "to",
                "use",
                "the",
                "service.",
            ],
            6,
            "... I don't think the barrier is so high to allow ...",
        ),
        (
            [
                "But",
                "I",
                "don't",
                "think",
                "the",
                "barrier",
                "is",
                "so",
                "high",
                "to",
                "allow",
                "individuals",
                "to",
                "use",
                "the",
                "service.",
            ],
            15,
            "... is so high to allow individuals to use the service.",
        ),
        (
            [
                "This",
                "is",
                "a",
                "sentence",
                "with",
                "no",
                "end",
                "of",
                "sentence",
                "punctuation",
                "but",
                "really",
                "why",
                "would",
                "someone",
                "do",
                "this",
            ],
            0,
            "This is a sentence with no end of sentence punctuation ...",
        ),
        (
            [
                "This",
                "is",
                "a",
                "sentence",
                "with",
                "no",
                "end",
                "of",
                "sentence",
                "punctuation",
                "but",
                "really",
                "why",
                "would",
                "someone",
                "do",
                "this",
            ],
            7,
            "... a sentence with no end of sentence punctuation but really ...",
        ),
        (
            [
                "This",
                "is",
                "a",
                "sentence",
                "with",
                "no",
                "end",
                "of",
                "sentence",
                "punctuation",
                "but",
                "really",
                "why",
                "would",
                "someone",
                "do",
                "this",
            ],
            15,
            "... of sentence punctuation but really why would someone do this",
        ),
        (["four", "words", "no", "punctuation"], 0, "four words no punctuation"),
        (["four", "words", "no", "punctuation"], 2, "four words no punctuation"),
        (["four", "words", "no", "punctuation"], 3, "four words no punctuation"),
        (["four", "words.", "yes", "punctuation"], 1, "four words."),
        (["four", "words.", "yes", "punctuation"], 3, "yes punctuation"),
        pytest.param(
            [
                "But",
                "I",
                "don't",
                "think",
                "the",
                "barrier",
                "is",
                "so",
                "high",
                "to",
                "allow",
                "individuals",
                "to",
                "use",
                "the",
                "service.",
            ],
            -1,
            None,
            marks=pytest.mark.raises(exceptions=IndexError),
        ),
        pytest.param(
            [
                "But",
                "I",
                "don't",
                "think",
                "the",
                "barrier",
                "is",
                "so",
                "high",
                "to",
                "allow",
                "individuals",
                "to",
                "use",
                "the",
                "service.",
            ],
            16,
            None,
            marks=pytest.mark.raises(exceptions=IndexError),
        ),
    ],
)
def test_get_context_span_for_index(terms, index, expected):
    assert Indexer.get_context_span_for_index(terms, index) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("hello world", "hello world"),
        ("hello ", "hello"),
        (
            "the quick brown fox jumps over the running ant",
            "quick brown fox jump run ant",
        ),
        (
            "The quick brown fox jumps over the running ant",
            "quick brown fox jump run ant",
        ),
        (
            "thE quICk BROwn Fox JuMps OVER the RUNning ANt",
            "quick brown fox jump run ant",
        ),
        ("1 billion", "1 billion"),
        ("98%", "98"),
        ("\n\n\n\nMEMORANDUM\n\nHello\n\tSPR", "memorandum hello spr"),
        # Would love to learn better methods for handling cases like this but I don't
        # think it matters too much
        ("1.4 Million", "14 million"),
        ("Will this remove punctuation?!%'", "remov punctuat"),
        ("$10 10.5% $5.5 2%", "10 105 55 2"),
        (
            "The study will reportedly cost $14.8 thousand",
            "studi reportedli cost 148 thousand",
        ),
    ],
)
def test_clean_text_for_indexing(text, expected):
    result = Indexer.clean_text_for_indexing(text)
    assert result == expected


@pytest.mark.parametrize("min_value, expected", [(0.0, DROPPED_ZEROS_INDEX), (1.0, {})])
def test_drop_terms_from_index_below_value(indexed_results, min_value, expected):
    result = Indexer.drop_terms_from_index_below_value(indexed_results, min_value)
    assert result == expected
