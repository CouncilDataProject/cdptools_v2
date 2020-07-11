#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from typing import Dict, List, Union

import pandas as pd
from prefect import Flow, task, unmapped
from prefect.engine.executors import DaskExecutor

from ..cdp_instance import CDPInstance
from ..configs import SEATTLE
from ..databases import Database, OrderOperators

###############################################################################
# logger

log = logging.getLogger(__name__)

###############################################################################
# workflow tasks


@task
def get_events(db: Database) -> pd.DataFrame:
    # Get transcript dataset
    return pd.DataFrame(
        db.select_rows_as_list(
            "event", limit=int(1e6), order_by=("event_datetime", OrderOperators.desc)
        )
    )


@task
def get_event_ids(events: pd.DataFrame) -> List[str]:
    return list(events.event_id)


@task
def get_bodies(db: Database) -> List[Dict]:
    return db.select_rows_as_list("body")


@task
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
    return pd.DataFrame(
        [
            transcript_details
            for transcript_details in transcripts
            if transcript_details is not None
        ]
    )


@task
def get_file_ids(transcripts: pd.DataFrame) -> List[str]:
    return list(transcripts.file_id)


@task
def get_file_details(file_id: str, db: Database) -> Dict:
    return db.select_row_by_id("file", file_id)


@task
def merge_event_and_body_details(
    events: pd.DataFrame, bodies: List[Dict]
) -> pd.DataFrame:
    # Create bodies dataframe
    bodies = pd.DataFrame(bodies)

    return events.merge(bodies, on="body_id", suffixes=("_event", "_body"),)


@task
def merge_transcript_and_file_details(
    transcripts: pd.DataFrame, files: List[Dict]
) -> pd.DataFrame:
    # Create files dataframe
    files = pd.DataFrame(files)

    return transcripts.merge(files, on="file_id", suffixes=("_transcript", "_file"),)


@task
def merge_event_and_transcript_details(
    events: pd.DataFrame, transcripts: pd.DataFrame,
) -> pd.DataFrame:
    # Merge dataframes
    merged = transcripts.merge(
        events, on="event_id", suffixes=("_event", "_transcript")
    )

    return merged


@task
def get_event_minutes_items(event_id: str, db: Database) -> List[Dict]:
    return db.select_rows_as_list(
        "event_minutes_item", filters=[("event_id", event_id)]
    )


@task
def expand_and_sort_event_minutes_items(emis: List[Dict], db: Database) -> pd.DataFrame:
    # Fast return None
    if len(emis) == 0:
        return None

    # For each emi in all minutes items for this event
    # Get the minutes item details
    cleaned = []
    for emi in emis:
        mi = db.select_row_by_id("minutes_item", emi["minutes_item_id"])

        # Negate the 1 indexing
        cleaned.append(
            {
                "event_minutes_item_id": emi["event_minutes_item_id"],
                "minutes_item_id": emi["minutes_item_id"],
                "name": mi["name"],
                "matter": mi["matter"],
                "index": emi["index"],
                "decision": emi["decision"],
            }
        )

    # Sort list by index
    cleaned = sorted(cleaned, key=lambda item: item["index"])

    # Convert to dataframe
    emis = pd.DataFrame(
        {
            # Wrapping in lists to enforce a single row
            "event_id": [emi["event_id"]],
            "event_minutes_items": [cleaned],
        }
    )

    # Return as single row dataframe
    return emis


@task
def merge_events_and_emi_details(
    events: pd.DataFrame, all_emis: List[pd.DataFrame]
) -> pd.DataFrame:
    # Clean out Nones
    all_emis = [emis for emis in all_emis if emis is not None]

    # Concat emis
    all_emis = pd.concat(all_emis)

    return events.merge(all_emis, on="event_id", suffixes=("_event", "_emis"))


@task
def finalize_dataset(dataset: pd.DataFrame) -> pd.DataFrame:
    dataset = dataset.rename(
        columns={
            "confidence": "transcript_confidence",
            "uri": "remote_transcript_uri",
            "video_uri": "remote_video_uri",
            "name": "body_name",
            "filename": "transcript_filename",
        }
    )

    return dataset[
        [
            "event_id",
            "event_datetime",
            "body_id",
            "body_name",
            "remote_video_uri",
            "transcript_id",
            "transcript_filename",
            "remote_transcript_uri",
            "transcript_confidence",
            "event_minutes_items",
        ]
    ]


###############################################################################
# workflow run function


def generate_dataset(instance: CDPInstance = CDPInstance(SEATTLE)) -> pd.DataFrame:
    """
    Generate
    """

    # Construct workflow
    with Flow("Download CDP Dataset") as flow:
        # Get events and body information
        events = get_events(instance.database)
        event_ids = get_event_ids(events)
        bodies = get_bodies(instance.database)

        # Get each event's transcript information
        transcripts = get_transcript_details.map(
            event_ids, db=unmapped(instance.database),
        )
        transcripts = construct_transcript_df(transcripts)
        file_ids = get_file_ids(transcripts)
        files = get_file_details.map(file_ids, db=unmapped(instance.database))

        # Get each event's minutes items
        all_emis = get_event_minutes_items.map(
            event_ids, db=unmapped(instance.database)
        )
        all_emis = expand_and_sort_event_minutes_items.map(
            all_emis, db=unmapped(instance.database)
        )

        # Merge dataframes
        events = merge_event_and_body_details(events, bodies)
        transcripts = merge_transcript_and_file_details(transcripts, files)
        transcript_manifest = merge_event_and_transcript_details(events, transcripts)
        complete_manifest = merge_events_and_emi_details(transcript_manifest, all_emis)
        finalize_dataset(complete_manifest)

    # Run
    state = flow.run(executor=DaskExecutor())

    # Return the actual dataframe
    return state.result[flow.get_tasks(name="finalize_dataset")[0]].result
