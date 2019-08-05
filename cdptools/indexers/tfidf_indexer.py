#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import math
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Dict, List, NamedTuple, Union

from .indexer import Indexer

###############################################################################

log = logging.getLogger(__name__)

###############################################################################


class DocumentDetails(NamedTuple):
    unique_id: str
    path: Path


class TFIDFIndexer(Indexer):

    def __init__(self, max_synchronous_jobs: int = 8, **kwargs):
        # Set state
        self.n_workers = max_synchronous_jobs

    def _generate_term_counts_for_document(transcript_details: DocumentDetails) -> Dict[str, Dict[str, float]]:
        # Open the transcript and get raw
        raw = Indexer.get_raw_transcript(transcript_details.path)

        # Clean the transcript text
        cleaned = Indexer.clean_text_for_indexing(raw)

        # Count terms
        # Thanks python core modules :^)
        terms = cleaned.split(" ")
        return {"unique_id": transcript_details.unique_id, "term_counts": Counter(terms)}

    @staticmethod
    def _combine_term_counts_for_corpus(
        corpus_results: List[Dict[str, Union[DocumentDetails, Counter]]]
    ) -> Dict[str, Dict[str, int]]:
        # Go through each term count dictionary and combine into single
        combined = {}
        for id_term_counts in corpus_results:
            # For each term count Counter returned get each term and it's count
            for term, count in id_term_counts["term_counts"].items():
                # If the term has been seen before, simply add a new entry for the term count for that unique id
                if term in combined:
                    combined[term][id_term_counts["unique_id"]] = count
                # If the term hasn't been seen, create a new dictionary to store term count by unique id
                else:
                    combined[term] = {id_term_counts["unique_id"]: count}

        return combined

    @staticmethod
    def _calculate_tfidf_for_corpus(term_counts_corpus: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, float]]:
        # N: total number of documents in the corpus
        # Let's use sets to create a list of all unique documents in the term counts corpus
        corpus = set()
        for term in term_counts_corpus:
            # Do set union to continue to add unique items to the corpus map
            documents = set(term_counts_corpus[term].keys())
            corpus = corpus.union(documents)

        # N is just now the length of the corpus
        N = len(corpus)

        # Compute tfidf values for the entire corpus
        tfidf_corpus = {}
        for term in term_counts_corpus:
            for unique_id, tf in term_counts_corpus[term].items():
                # Compute idf
                # d_t: documents containing term
                # The number of documents containing a term is just the length of the available keys for that term
                # in the term counts corpus
                # Ex:
                # "hello": {
                #   "0000...": 3,
                #   "1111...": 7,
                #   "9999...": 2
                # }
                # The term "hello" occurs in 3 documents in the above example
                d_t = len(term_counts_corpus[term])
                idf = math.log(N / d_t)

                # If term already seen, simply add a new entry for the term tfidf value for that unique id
                if term in tfidf_corpus:
                    tfidf_corpus[term][unique_id] = tf * idf
                # If the term hasn't been seen, create a new dictionary to store term tfidf value by unique id
                else:
                    tfidf_corpus[term] = {unique_id: tf * idf}

        return tfidf_corpus

    def generate_index(self, document_corpus_map: Dict[str, Path]) -> Dict[str, Dict[str, float]]:
        # Convert the document corpus map to a list of TranscriptDetails for easier passing to multiprocessing
        document_corpus_map = [DocumentDetails(unique_id, path) for unique_id, path in document_corpus_map.items()]

        # We could use sklearn CountVectorizer/ TfidfVectorizer, but meh 🤷
        # I don't think loading all the files into memory and stuffing them into a single list is that great
        # These transcripts can get long....
        # Memory shouldn't be an issue now, but maybe at like ~4000 documents?
        with ProcessPoolExecutor(max_workers=self.n_workers) as exe:
            results = list(exe.map(TFIDFIndexer._generate_term_counts_for_document, document_corpus_map))

        # Combine the single unique id results
        results = self._combine_term_counts_for_corpus(results)

        # Compute tfidf values for the combined results
        index = self._calculate_tfidf_for_corpus(results)

        return index
