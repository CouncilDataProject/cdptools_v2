#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
from datetime import timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Union

import dask.config
import pandas as pd
from dask import delayed
from dask_cloudprovider import FargateCluster
from dask_ml.feature_extraction.text import HashingVectorizer
from distributed import Client
from prefect import Flow, task, unmapped
from prefect.engine.executors import DaskExecutor
from tika import parser

from ..databases import Database, OrderOperators
from ..dev_utils import load_custom_object
from ..file_stores import FileStore
from ..indexers import Indexer
from .pipeline import Pipeline

###############################################################################

log = logging.getLogger(__name__)

###############################################################################
# Workflow tasks


@task
def get_events(db: Database) -> pd.DataFrame:
    # Get transcript dataset
    return pd.DataFrame(db.select_rows_as_list("event", limit=int(1e6)))


@task
def get_event_ids(events: pd.DataFrame) -> List[str]:
    return list(events.event_id)


@task
def get_bodies(db: Database) -> List[Dict]:
    return db.select_rows_as_list("body")


# Add retries and retry delay as the worker may struggle with so many request opens
@task(max_retries=3, retry_delay=timedelta(seconds=3))
def get_transcript_details(event_id: str, db: Database) -> Dict:
    # Get the highest confidence transcript for the event
    results = db.select_rows_as_list(
        table="transcript",
        filters=[("event_id", event_id)],
        order_by=("confidence", OrderOperators.desc),
        limit=1,
    )

    # Return result if found
    if len(results) == 1:
        return results[0]


@task
def construct_transcript_df(transcripts: List[Union[Dict, None]]) -> pd.DataFrame:
    # Create transcripts dataframe
    return pd.DataFrame([
        transcript_details for transcript_details in transcripts
        if transcript_details is not None
    ])


@task
def get_file_ids(transcripts: pd.DataFrame) -> List[str]:
    return list(transcripts.file_id)


# Add retries and retry delay as the worker may struggle with so many request opens
@task(max_retries=3, retry_delay=timedelta(seconds=3))
def get_file_details(file_id: str, db: Database) -> Dict:
    return db.select_row_by_id("file", file_id)


# Add retries and retry delay as the worker may struggle with so many request opens
@task(max_retries=3, retry_delay=timedelta(seconds=3))
def get_event_minutes_items(event_id: str, db: Database) -> List[Dict]:
    return db.select_rows_as_list(
        "event_minutes_item", filters=[("event_id", event_id)]
    )


@task
def flatten_event_minutes_items(event_minutes_items: List[List[Dict]]) -> List[Dict]:
    # Drop all None values
    # Pull out the key info
    minutes_items = []
    for event_minutes_item in event_minutes_items:
        if event_minutes_item is not None:
            for minutes_item in event_minutes_item:
                minutes_items.append({
                    "event_id": minutes_item["event_id"],
                    "minutes_item_id": minutes_item["minutes_item_id"],
                })

    return minutes_items


# Add retries and retry delay as the worker may struggle with so many request opens
@task(max_retries=3, retry_delay=timedelta(seconds=3))
def get_minutes_item_file_details(
    minutes_item: Dict, db: Database
) -> Union[List[Dict], None]:
    # Get minutes item file
    mifs = db.select_rows_as_list(
        "minutes_item_file",
        filters=[("minutes_item_id", minutes_item["minutes_item_id"])],
    )

    # Return just the URI if mif exists
    if mifs is not None:
        mifs = [{
            "event_id": minutes_item["event_id"],
            "uri": mif["uri"]
        } for mif in mifs]

    return mifs


@task
def construct_minutes_item_files_df(
    minutes_item_files: List[List[Dict]]
) -> pd.DataFrame:
    # Drop all None values
    # Flatten
    flat_mifs = []
    for event_mifs in minutes_item_files:
        if event_mifs is not None:
            flat_mifs += event_mifs

    return pd.DataFrame(flat_mifs)


@task
def merge_event_and_body_details(
    events: pd.DataFrame, bodies: List[Dict]
) -> pd.DataFrame:
    # Create bodies dataframe
    bodies = pd.DataFrame(bodies)

    return events.merge(
        bodies,
        on="body_id",
        suffixes=("_event", "_body"),
    )


@task
def merge_transcript_and_file_details(
    transcripts: pd.DataFrame, files: List[Dict]
) -> pd.DataFrame:
    # Create files dataframe
    files = pd.DataFrame(files)

    return transcripts.merge(
        files,
        on="file_id",
        suffixes=("_transcript", "_file"),
    )


@task
def merge_event_and_transcript_details(
    events: pd.DataFrame, transcripts: pd.DataFrame,
) -> pd.DataFrame:
    # Merge dataframes
    merged = transcripts.merge(
        events, on="event_id", suffixes=("_event", "_transcript")
    )
    merged.to_csv("transcript_manifest.csv", index=False)

    return merged


@task
def construct_expanded_corpus_df(
    transcripts: pd.DataFrame, minutes_item_files: pd.DataFrame
) -> pd.DataFrame:
    # Drop columns from transcripts df
    transcripts = transcripts[["event_id", "uri"]]

    # Append minutes item files df
    merged = pd.concat([transcripts, minutes_item_files], ignore_index=True)
    merged.to_csv("remote_corpus.csv", index=False)

    return merged


@task
def df_to_records(df: pd.DataFrame) -> List[Dict]:
    return df.to_dict("records")


@task(max_retries=3, retry_delay=timedelta(seconds=3))
def construct_delayed_raw_text_read(row: Dict, fs: FileStore) -> Dict:
    # Route to correct delayed downloader
    # Assumes that if the URI does not start with https
    # the file is a transcript from the file store
    if row["uri"].startswith("https://"):
        path = delayed(FileStore._external_resource_copy)(row["uri"], overwrite=True)
        text = Indexer.get_text_from_file(path)

    else:
        # Download file only accepts the filename, not the full URI
        path = delayed(fs.download_file)(row["uri"].split("/")[-1], overwrite=True)
        text = delayed(Indexer.get_raw_transcript)(path)

    return {
        "event_id": row["event_id"],
        "path": path,
        "text": text,
    }

###############################################################################


class EventIndexPipeline(Pipeline):
    def __init__(self, config_path: Union[str, Path]):
        # Resolve config path
        config_path = config_path.resolve(strict=True)

        # Read
        with open(config_path, "r") as read_in:
            self.config = json.load(read_in)

        # Get workers
        self.n_workers = self.config.get("max_synchronous_jobs")

        # Load modules
        self.database = load_custom_object.load_custom_object(
            module_path=self.config["database"]["module_path"],
            object_name=self.config["database"]["object_name"],
            object_kwargs={**self.config["database"].get("object_kwargs", {})},
        )
        self.file_store = load_custom_object.load_custom_object(
            module_path=self.config["file_store"]["module_path"],
            object_name=self.config["file_store"]["object_name"],
            object_kwargs=self.config["file_store"].get("object_kwargs", {}),
        )
        self.indexer = load_custom_object.load_custom_object(
            module_path=self.config["indexer"]["module_path"],
            object_name=self.config["indexer"]["object_name"],
            object_kwargs=self.config["indexer"].get("object_kwargs", {}),
        )

    def run(self):
        # Construct workflow
        with Flow("Event Index Pipeline") as flow:
            # Get events and body information
            events = get_events(self.database)
            event_ids = get_event_ids(events)
            bodies = get_bodies(self.database)

            # Get each event's transcript information
            transcripts = get_transcript_details.map(
                event_ids, db=unmapped(self.database),
            )
            transcripts = construct_transcript_df(transcripts)
            file_ids = get_file_ids(transcripts)
            files = get_file_details.map(
                file_ids, db=unmapped(self.database)
            )

            # Get each event's minutes items
            all_events_emis = get_event_minutes_items.map(
                event_ids, db=unmapped(self.database)
            )
            flattened_emis = flatten_event_minutes_items(all_events_emis)
            all_events_mifs = get_minutes_item_file_details.map(
                flattened_emis, db=unmapped(self.database)
            )
            minutes_item_files = construct_minutes_item_files_df(all_events_mifs)

            # Merge dataframes
            events = merge_event_and_body_details(events, bodies)
            transcripts = merge_transcript_and_file_details(transcripts, files)
            transcripts = merge_event_and_transcript_details(events, transcripts)
            remote_corpus = construct_expanded_corpus_df(
                transcripts, minutes_item_files
            )

            # Construct delayed text get
            rows = df_to_records(remote_corpus)
            read_corpus = construct_delayed_raw_text_read.map(
                rows, fs=unmapped(self.file_store)
            )

        # Configure dask config
        dask.config.set(
            {
                "scheduler.work-stealing": False,
            }
        )

        # Construct FargateCluster
        cluster = FargateCluster(
            image="councildataproject/cdptools-beta",
            worker_cpu=512,
            worker_mem=8192,
        )
        cluster.adapt(2, 100)
        client = Client(cluster)

        log.info(f"Dashboard available at: {client.dashboard_link}")

        # Run
        state = flow.run(executor=DaskExecutor(address=cluster.scheduler_address))

        # Visualize
        flow.visualize(filename="event-index-pipeline", format="png")

        items = state.result[
            flow.get_tasks("construct_delayed_raw_text_read")[0]
        ].result
        print(items[0])
        items[0]["text"] = items[0]["text"].compute()
        print(items[0])
