import csv
import json
import logging
import os
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Dict, Union

from .. import get_module_version
from ..dev_utils import RunManager, load_custom_object
from ..research_utils import transcripts as transcript_tools
from .pipeline import Pipeline

###############################################################################

log = logging.getLogger(__name__)

###############################################################################

_EVENT_METADATA_COLS = [
    'event_id',
    'legistar_event_link',
    'source_uri',
    'legistar_event_id',
    'event_datetime',
    'agenda_file_uri',
    'minutes_file_uri',
    'video_uri',
    'created_event',
    'name',
    'description_event',
    'filename'
]


class EventNLAnalyzePipeline(Pipeline):

    def __init__(self, config_path: Union[str, Path]):
        # Resolve config path
        config_path = config_path.resolve(strict=True)

        # Read
        with open(config_path, "r") as read_in:
            self.config = json.load(read_in)

        # Get workers
        self.n_workers = self.config.get("max_synchronous_jobs")

    def _load_event_metadata(self, manifest_path):
        with open(manifest_path) as f:
            reader = csv.DictReader(f)
            events = [{"metadata": self._extract_event_metadata(row)} for row in reader]
            return events

    @staticmethod
    def _extract_event_metadata(event_row):
        event_metadata = {}
        for col in _EVENT_METADATA_COLS:
            event_metadata[col] = event_row.get(col)
        return event_metadata

    def task_extract_and_upload_entities(self, event: Dict[str, Any]):
        database = load_custom_object.load_custom_object_from_config("database", self.config)
        with RunManager(
            database,
            load_custom_object.load_custom_object_from_config("file_store", self.config),
            "EventNLAnalyzePipeline.task_extract_and_upload_entities",
            get_module_version(),
            remove_files=True
        ):
            entity_analyzer = load_custom_object.load_custom_object_from_config("entity_analyzer", self.config)

            analyzer_input = entity_analyzer.load(event["transcript"], event["metadata"])

            entities = entity_analyzer.analyze(analyzer_input)

            for entity in entities:
                database.get_or_upload_event_entity(
                    event["metadata"]["event_id"],
                    entity["label"],
                    entity["value"]
                )

    def process_event(self, event: Dict) -> str:
        # Other tasks will go here
        self.task_extract_and_upload_entities(event, self.config)

        # Update progress
        log.info("Completed event: {} ({}) ".format(
            event["metadata"]["event_id"],
            event["metadata"]["filename"]
        ))

    def run(self):
        log.info("Starting event processing.")
        database = load_custom_object.load_custom_object_from_config("database", self.config)
        file_store = load_custom_object.load_custom_object_from_config("file_store", self.config)

        with RunManager(
            database,
            file_store,
            "EventNLAnalyzePipeline.run",
            get_module_version(),
            remove_files=True
        ):
            # Store the transcripts and manifest locally in a temporary directory
            with tempfile.TemporaryDirectory() as tmpdir:
                # Get the event corpus map and download most recent transcripts to local machine
                log.info("Downloading most recent transcripts")
                event_corpus_map = transcript_tools.download_most_recent_transcripts(
                    db=database,
                    fs=file_store,
                    save_dir=tmpdir
                )

                manifest_path = Path(tmpdir, transcript_tools.MANIFEST_FILENAME)
                event_metadata_list = self._load_event_metadata(manifest_path)

                events = []
                for metadata in event_metadata_list:
                    transcript_path = event_corpus_map[metadata["event_id"]]
                    transcript = transcript_tools.load_transcript(transcript_path, join_text=True, sep=" ")

                    events.append({"metadata": metadata, "transcript": transcript})

            # Multiprocess each event found
            # Since NLAnalyzer tasks are likely CPU intensive, use ProcessPoolExecutor
            # which can only accept pickleable arguments
            with ProcessPoolExecutor(self.n_workers) as exe:
                exe.map(self.process_event, events)

        log.info("Completed event processing.")
        log.info("=" * 80)
