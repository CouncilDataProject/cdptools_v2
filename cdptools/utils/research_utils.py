from pathlib import Path
from typing import Optional, Union

import pandas as pd

from cdptools.databases import Database
from cdptools.file_stores import FileStore


def get_most_recent_transcript_manifest(db: Database) -> pd.DataFrame:
    # Get transcript dataset
    transcripts = pd.DataFrame(db.select_rows_as_list("transcript"))
    events = pd.DataFrame(db.select_rows_as_list("event"))
    bodies = pd.DataFrame(db.select_rows_as_list("body"))
    files = pd.DataFrame(db.select_rows_as_list("file"))
    events = events.merge(bodies, left_on="body_id", right_on="body_id", suffixes=("_event", "_body"))
    transcripts = transcripts.merge(files, left_on="file_id", right_on="file_id", suffixes=("_transcript", "_file"))
    transcripts = transcripts.merge(events, left_on="event_id", right_on="event_id", suffixes=("_transcript", "_event"))

    # Group
    most_recent_transcripts = []
    grouped = transcripts.groupby("event_id")
    for name, group in grouped:
        most_recent = group.loc[group["created_transcript"].idxmax()]
        most_recent_transcripts.append(most_recent)

    most_recent = pd.DataFrame(most_recent_transcripts)

    return most_recent


def download_most_recent_transcripts(db: Database, fs: FileStore, save_dir: Optional[Union[str, Path]] = None) -> Path:
    """
    Download the most recent versions of event transcripts.

    :param db: An already initialized `Database` object to query against.
    :param fs: An alreay initialized `FileStore` object to query against.
    :param save_dir: Path to a directory to save the transcripts and the dataset manifest.
    :return: Fully resolved path where transcripts and dataset manifest were stored.
    """
    # Use current directory is None provided
    if save_dir is None:
        save_dir = "."

    # Resolve save directory
    save_dir = Path(save_dir).resolve()

    # Make the save directory if not already exists
    save_dir.mkdir(parents=True, exist_ok=True)

    # Get most recent transcript data
    most_recent = get_most_recent_transcript_manifest(db)

    # Begin storage
    most_recent.apply(
        lambda r: fs.download_file(r["filename"], save_dir / r["filename"], overwrite=True),
        axis=1
    )

    # Write manifest
    most_recent.to_csv(save_dir / "transcript_manifest.csv", index=False)

    return save_dir
