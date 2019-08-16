import copy
import csv
import json
import logging
import tempfile
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial
from pathlib import Path
from typing import Any, Dict, Union
from uuid import uuid4

from .. import get_module_version
from ..databases import Database
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

    def _upload_entity(self, database: Database, entity: Dict[str, Any]) -> Dict[str, Any]:
        return database.get_or_upload_event_entity(
            event_id=entity["event_id"],
            label=entity["label"],
            value=entity["value"]
        )

    def task_extract_and_upload_entities(self, event: Dict[str, Any]):
        # Load database
        config = copy.deepcopy(self.config)
        config["database"]["object_kwargs"]["name"] = str(uuid4())
        database = load_custom_object.load_custom_object_from_config("database", config)
        with RunManager(
            database,
            load_custom_object.load_custom_object_from_config("file_store", self.config),
            "EventNLAnalyzePipeline.task_extract_and_upload_entities",
            get_module_version(),
            inputs=[("event_id", event["metadata"]["event_id"])],
            remove_files=True
        ):
            # Load entity analyzer in process
            entity_analyzer = load_custom_object.load_custom_object_from_config("entity_analyzer", self.config)

            # Load model input
            analyzer_input = entity_analyzer.load(event["transcript"], event["metadata"])

            # Analyze text for entities
            entities = entity_analyzer.analyze(analyzer_input)
            flatten = []
            for e_list in entities:
                for entity in e_list:
                    flatten.append({
                        "event_id": event["metadata"]["event_id"],
                        "label": entity["label"],
                        "value": entity["value"]
                    })

        # Create partial for uploader
        # uploader = partial(self._upload_entity, database=database)

            # Multithreaded upload
            for e in flatten:
                self._upload_entity(database, e)
        # with ThreadPoolExecutor() as exe:
        #     list(exe.map(uploader, entities))

    def process_event(self, event: Dict) -> str:
        print("processing event", event["metadata"]["event_id"])
        # Other tasks will go here
        self.task_extract_and_upload_entities(event)

        print("completed event", event["metadata"]["event_id"])

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
                    transcript_path = event_corpus_map[metadata["metadata"]["event_id"]]
                    transcript = transcript_tools.load_transcript(transcript_path, join_text=True, sep=" ")

                    event = {**metadata, "transcript": transcript}
                    events.append(event)

            # Multiprocess each event found
            # Since NLAnalyzer tasks are likely CPU intensive, use ProcessPoolExecutor
            # which can only accept pickleable arguments
            for e in events:
                self.process_event(e)
            # with ProcessPoolExecutor(self.n_workers) as exe:
            #     list(exe.map(self.process_event, events))

        log.info("Completed event processing.")
        log.info("=" * 80)
