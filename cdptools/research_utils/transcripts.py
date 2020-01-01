#!/usr/bin/env python
# -*- coding: utf-8 -*-

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from typing import Any, Dict, NamedTuple, Optional, Union

import pandas as pd

from cdptools.databases import Database, OrderOperators
from cdptools.file_stores import FileStore

###############################################################################

ALLOWED_ORDER_BY_FIELDS = [
    "created",
    "confidence"
]

###############################################################################


class TrancriptJoin(NamedTuple):
    event_id: str
    transcript_details: Optional[Dict[str, Any]]


def _get_transcript_for_event(event_id: str, db: Database, order_by_field: str) -> Dict[str, Any]:
    # Get the most recent or highest confidence transcript for the event
    results = db.select_rows_as_list(
        table="transcript",
        filters=[
            ("event_id", event_id)
        ],
        order_by=(order_by_field, OrderOperators.desc),
        limit=1
    )

    # Return result if found
    if len(results) == 1:
        return TrancriptJoin(event_id=event_id, transcript_details=results[0])

    # Return none to be filtered out
    return TrancriptJoin(event_id=event_id, transcript_details=None)


def _get_file(file_id: str, db: Database) -> Dict[str, Any]:
    return db.select_row_by_id(table="file", id=file_id)


def get_transcript_manifest(db: Database, order_by_field: str = "confidence") -> pd.DataFrame:
    """
    Get a pandas dataframe that can act as a manifest of a transcript available for each event stored in a CDP
    instance's database.

    Parameters
    ----------
    db: Database
        An already initialized database object connected to a CDP instance's database.
    order_by_field: str
        Which field to order the transcripts by to select the first (highest value) of.
        Default: "confidence"
        Choices: ["created", "confidence"]

    Returns
    -------
    manifest: pandas.DataFrame
        A dataframe where each row has transcript, event, body, and file details for the event at that row.
    """

    # Get transcript dataset
    events = pd.DataFrame(db.select_rows_as_list("event", limit=1e6))

    # Enforce that the provided order by field is valid
    order_by_field = order_by_field.lower()
    if order_by_field not in ALLOWED_ORDER_BY_FIELDS:
        raise ValueError(
            f"Provided `order_by_field` value is not a valid selection for transcript ordering / selection. "
            f"Received: {order_by_field}. Possible choices: {ALLOWED_ORDER_BY_FIELDS}"
        )

    # Create transcript get partial
    transcript_get = partial(_get_transcript_for_event, db=db, order_by_field=order_by_field)

    # Threaded request all transcripts
    with ThreadPoolExecutor() as exe:
        transcript_joins = list(exe.map(transcript_get, list(events.event_id)))

    # Filter down to only valid events
    # (Events that have transcripts)
    events_with_transcripts = [join.event_id for join in transcript_joins if join.transcript_details is not None]
    events = events[events.event_id.isin(events_with_transcripts)]

    # Create a dataframe of the valid transcripts
    transcripts = pd.DataFrame(
        [join.transcript_details for join in transcript_joins if join.transcript_details is not None]
    )

    # Merge transcript data with event data
    events = events.merge(transcripts, on="event_id", suffixes=("_event", "_transcript"))

    # Create file get partial
    file_get = partial(_get_file, db=db)

    # Get all the transcript files
    with ThreadPoolExecutor() as exe:
        transcript_file_details = pd.DataFrame(list(exe.map(file_get, events.file_id)))

    # Merge transcript file data with event transcript data
    events = events.merge(transcript_file_details, on="file_id", suffixes=("_transcript", "_file"))

    # Get body details and merge
    events = events.merge(
        pd.DataFrame(db.select_rows_as_list(table="body", limit=1e4)),
        on="body_id",
        suffixes=("_event", "_body")
    )

    return events


def download_event_transcripts(
    db: Database,
    fs: FileStore,
    order_by_field: str = "confidence",
    save_dir: Optional[Union[str, Path]] = None
) -> Dict[str, Path]:
    """
    Download a transcript for each event found in a CDP instance. Additionally saves the manifest as a CSV.

    Parameters
    ----------
    db: Database
        An already initialized database object connected to a CDP instance's database.
    fs: FileStore
        An already initialized file store object connected to a CDP instance's file store.
    order_by_field: str
        Which field to order the transcripts by to select the first (highest value) of.
        Default: "confidence"
        Choices: ["created", "confidence"]
    save_dir: Optional[Union[str, Path]]
        An optional path of where to save the transcripts and manifest CSV. If None provided, uses current directory.
        Always overwrites existing transcripts with the same name if they already exist in the provided directory.

    Returns
    -------
    event_corpus_map: Dict[str, Path]
        A dictionary mapping event id to a local Path for a transcript for that event.
    """

    # Use current directory is None provided
    if save_dir is None:
        save_dir = "."

    # Resolve save directory
    save_dir = Path(save_dir).expanduser().resolve()

    # Make the save directory if not already exists
    save_dir.mkdir(parents=True, exist_ok=True)

    # Get most recent transcript data
    most_recent = get_transcript_manifest(db=db, order_by_field=order_by_field)

    # Begin storage
    most_recent.apply(
        lambda r: fs.download_file(r["filename"], save_dir, overwrite=True),
        axis=1
    )

    # Write manifest
    most_recent.to_csv(save_dir / "transcript_manifest.csv", index=False)

    # Create event corpus map
    event_corpus_map = {}
    for transcript_details in most_recent.to_dict("records"):
        event_corpus_map[transcript_details["event_id"]] = Path(
            save_dir / transcript_details["filename"]
        ).resolve(strict=False)

    return event_corpus_map
