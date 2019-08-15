import json

from pathlib import Path
from typing import Dict, Optional, Union

import pandas as pd

from cdptools.databases import Database
from cdptools.file_stores import FileStore


def get_most_recent_transcript_manifest(db: Database) -> pd.DataFrame:
    """
    Get a pandas dataframe that can act as a manifest of the most recent transcript available for each event stored in a
    CDP instance's database.

    Parameters
    ----------
    db: Database
        An already initialized database object connected to a CDP instance's database.

    Returns
    -------
    manifest: pandas.DataFrame
        A dataframe with transcript, event, body, and file details where each row is the most recent transcript for the
        event of that row.
    """
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


def download_most_recent_transcripts(
    db: Database,
    fs: FileStore,
    save_dir: Optional[Union[str, Path]] = None
) -> Dict[str, Path]:
    """
    Download the most recent versions of event transcripts.

    Parameters
    ----------
    db: Database
        An already initialized database object connected to a CDP instance's database.
    fs: FileStore
        An already initialized file store object connected to a CDP instance's file store.
    save_dir: Optional[Union[str, Path]]
        An optional path of where to save the transcripts and manifest CSV. If None provided, uses current directory.
        Always overwrites existing transcripts with the same name if they already exist in the provided directory.

    Returns
    -------
    event_corpus_map: Dict[str, Path]
        A dictionary mapping event id to local Path of the most recent transcript for that event.
    """
    # Use current directory is None provided
    if save_dir is None:
        save_dir = "."

    # Resolve save directory
    save_dir = Path(save_dir).expanduser().resolve()

    # Make the save directory if not already exists
    save_dir.mkdir(parents=True, exist_ok=True)

    # Get most recent transcript data
    most_recent = get_most_recent_transcript_manifest(db)

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


def load_transcript_text(transcript_path: Union[str, Path], join_sentences: bool = False, sep: str = " ") -> dict:
    """
    Attempts to open either a raw or annotated json transcript format and return the raw transcript as a dict.
    If the file format is not supported or if the data contained in the transcript does not follow the specification
    a TypeError is raised.

    Parameters
    ----------
    transcript_path: Union[str, Path]
        Path to the transcript

    join_sentences: bool=False
        If true, join sentences using sep

    sep: str=" "
        Separator to use if join_sentences is True

    Returns
    -------
    transcript: dict
    {
        "format": str,
        "annotations": [],
        "confidence": float,
        "sentences": [{"text": str, "start_time": float, "end_time": float}],
        "full_text": str
    }
    """
    transcript = {}
    # Enforce path
    transcript_path = Path(transcript_path).expanduser().resolve(strict=True)

    # Check that the transcript follows a known format
    if transcript_path.suffix != ".json":
        raise TypeError(
            f"Unsure how to handle transcript file format: {transcript_path}"
            f"Please refer to the `transcript_formats.md` file in the documentation for details."
        )

    try:
        with open(transcript_path, "r") as read_in:
            transcript = json.load(read_in)

        transcript["sentences"] = transcript.pop("data")
        if join_sentences:
            transcript["full_text"] = sep.join([portion["text"] for portion in transcript["sentences"]])

    except KeyError:
        raise TypeError(
            f"Unsure how to handle annotated JSON transcript provided: {transcript_path}"
            f"Please refer to the `transcript_formats.md` file in the documentation for details."
        )

    return transcript
