#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging

import pandas as pd
from nltk import ngrams
from nltk.stem import SnowballStemmer

import dask.dataframe as dd
from cdptools import CDPInstance, configs
from cdptools.databases.database import OrderOperators
from cdptools.indexers import Indexer
from cdptools.pipelines.event_index_pipeline import flatten

###############################################################################

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)4s: %(module)s:%(lineno)4s %(asctime)s] %(message)s",
)
log = logging.getLogger(__name__)

###############################################################################

class Args(argparse.Namespace):
    def __init__(self):
        self.__parse()

    def __parse(self):
        p = argparse.ArgumentParser(
            prog="process_single_event", description="Process a single event."
        )

        p.add_argument(
            "--query",
            type=str,
            default="bike infrastructure and neighborhood greenways",
            help="Query to search with.",
        )
        p.add_argument(
            "--local-index",
            dest="local_index",
            type=str,
            default="*_tfidf.csv",
            help="The file glob for which files to use for reading a planned index."
        )
        p.add_argument(
            "--debug",
            action="store_true",
            dest="debug",
            help="Show traceback if the script were to fail.",
        )
        p.parse_args(namespace=self)

###############################################################################

def _get_cdp_link(event_id: str) -> str:
    return f"https://councildataproject.github.io/seattle/#/events/{event_id}"

def run_current_search(query: str):
    log.info("Running search against current index...")

    # Use pre-existing search
    seattle = CDPInstance(configs.SEATTLE)
    results = seattle.database.search_events(query)

    # Report results
    log.info("Current index search results (most strictly relevant first):")
    log.info("=" * 80)
    for i, match in enumerate(results[:5]):
        # Get keywords for event
        match_keywords = seattle.database.select_rows_as_list(
            "indexed_event_term",
            filters=[("event_id", match.unique_id)],
            order_by=("value", OrderOperators.desc),
            limit=5
        )
        match_keywords = [kw["term"] for kw in match_keywords]

        # Log results
        log.info(f"Match {i + 1}: {_get_cdp_link(match.unique_id)}")
        log.info(f"Match relevance: {match.relevance}")
        log.info(f"Match contained grams: {[t.term for t in match.terms]}")
        log.info(f"Match keywords: {match_keywords}")
        log.info(f"Match context: None")
        log.info("-" * 80)

    print()
    log.info("=" * 80)
    print()


def run_local_search(query: str, local_index: str):
    log.info("Running search against local index...")

    # Spawn stemmer
    stemmer = SnowballStemmer("english")

    # Create stemmed grams for query
    query = Indexer.clean_doc(query).split()
    stemmed_grams = []
    for n_gram_size in range(1, 3):
        grams = ngrams(query, n_gram_size)
        for gram in grams:
            stemmed_grams.append(" ".join(stemmer.stem(term.lower()) for term in gram))

    # Read index
    index_df = dd.read_csv(local_index, keep_default_na=False).compute()

    # For each stemmed gram find matching_events
    matching_events = index_df[index_df.stemmed_gram.isin(stemmed_grams)]

    # Group by event id, sum by tfidf, and sort
    summed_tfidf = matching_events\
        .groupby("event_id")\
        .agg({"tfidf": sum})\
        .reset_index()

    # Merge results with original
    matching_events = matching_events\
        .merge(summed_tfidf, on="event_id", suffixes=("_stemmed_gram", "_summed"))\
        .sort_values(by="tfidf_summed", ascending=False)

    # Group events and sort
    matching_events = matching_events.groupby("event_id", sort=False)

    # Report results
    log.info("Local index search results (most strictly relevant first):")
    log.info("=" * 80)
    for i, group_details in enumerate(matching_events):
        # Unpack group details
        event_id, group = group_details

        # Get most important context span by contribution to sum
        most_important_context_span = group\
            [group.tfidf_stemmed_gram == group.tfidf_stemmed_gram.max()]\
            .iloc[0]\
            .context_span

        # Get keywords for event
        event_df = index_df\
            [index_df.event_id == event_id]\
            .sort_values("tfidf", ascending=False)
        match_keywords = list(event_df.unstemmed_gram)[:5]

        # Log results
        log.info(f"Match {i + 1}: {_get_cdp_link(event_id)}")
        log.info(f"Match relevance: {group.iloc[0].tfidf_summed}")
        log.info(f"Match contained grams: {list(group.unstemmed_gram)}")
        log.info(f"Match keywords: {match_keywords}")
        log.info(f"Match context: {most_important_context_span}")
        log.info("-" * 80)

        if i == 4:
            break

    print()
    log.info("=" * 80)
    print()

###############################################################################

if __name__ == "__main__":
    args = Args()

    try:
        log.info(f"Running search comparison against query: '{args.query}'")
        run_current_search(args.query)
        run_local_search(args.query, args.local_index)
    except Exception as e:
        log.error("=============================================")
        if args.debug:
            log.error("\n\n" + traceback.format_exc())
            log.error("=============================================")
        log.error("\n\n" + str(e) + "\n")
        log.error("=============================================")
        sys.exit(1)
