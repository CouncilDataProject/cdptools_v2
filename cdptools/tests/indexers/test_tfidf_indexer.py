#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from cdptools.indexers.tfidf_indexer import TFIDFIndexer

indexer = TFIDFIndexer()


@pytest.fixture
def event_corpus_map(data_dir):
    return {
        "event_0": data_dir / "fake_transcript_0.json",
        "event_1": data_dir / "fake_transcript_1.json",
    }


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


def test_generate_index(event_corpus_map, indexed_results):
    # Generate
    index = indexer.generate_index(event_corpus_map)

    # Check results
    assert index == indexed_results
