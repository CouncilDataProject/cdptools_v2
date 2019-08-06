#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Union

import requests
from tika import parser

from .. import get_module_version
from ..dev_utils import RunManager
from .pipeline import Pipeline, ValuesForTerm

###############################################################################

log = logging.getLogger(__name__)

###############################################################################


class MinutesItemIndexPipeline(Pipeline):

    def __init__(self, config_path: Union[str, Path]):
        # Resolve config path
        config_path = config_path.resolve(strict=True)

        # Read
        with open(config_path, "r") as read_in:
            self.config = json.load(read_in)

        # Get workers
        self.n_workers = self.config.get("max_synchronous_jobs")

        # Load modules
        self.database = self.load_custom_object(
            module_path=self.config["database"]["module_path"],
            object_name=self.config["database"]["object_name"],
            object_kwargs={**self.config["database"].get("object_kwargs", {})}
        )
        self.file_store = self.load_custom_object(
            module_path=self.config["file_store"]["module_path"],
            object_name=self.config["file_store"]["object_name"],
            object_kwargs=self.config["file_store"].get("object_kwargs", {})
        )
        self.indexer = self.load_custom_object(
            module_path=self.config["indexer"]["module_path"],
            object_name=self.config["indexer"]["object_name"],
            object_kwargs=self.config["indexer"].get("object_kwargs", {})
        )

    def task_generate_corpus(self, save_dir: Path) -> Dict[str, Path]:
        """
        Generate the minutes item corpus (decision item corpus) to be indexed.
        """
        with RunManager(
            database=self.database,
            file_store=self.file_store,
            algorithm_name="MinutesItemIndexPipeline.task_generate_corpus",
            algorithm_version=get_module_version()
        ):
            # Get only minutes items that had a decision
            # This will generally reduce the minutes items to just bills, appointments, etc
            # Read this stackoverflow for how we are selecting anything that isn't null
            # https://stackoverflow.com/questions/48479532/firestore-select-where-is-not-null
            decision_items = self.database.select_rows_as_list("event_minutes_item", filters=[("decision", ">", "")])

            # Attach minutes item information to each decision item
            for i, di in enumerate(decision_items):
                decision_items[i] = {**di, **self.database.select_row_by_id("minutes_item", di["minutes_item_id"])}

            # Gather event info and reformat object structure to be a dictionary mapping
            # minutes item to list of events that minutes item was discussed in
            di_to_events = {}
            for di in decision_items:
                if di["minutes_item_id"] in di_to_events:
                    di_to_events[di["minutes_item_id"]].append(self.database.select_row_by_id("event", di["event_id"]))
                else:
                    di_to_events[di["minutes_item_id"]] = [self.database.select_row_by_id("event", di["event_id"])]

            # Add list of most recent transcript filenames
            di_to_transcripts = {}
            for di, events in di_to_events.items():
                for event in events:
                    transcript = self.database.select_rows_as_list(
                        "transcript",
                        filters=[("event_id", event["event_id"])],
                        order_by=("created", "DESCENDING"),
                        limit=1
                    )[0]
                    file_details = self.database.select_row_by_id("file", transcript["file_id"])

                    if di in di_to_transcripts:
                        di_to_transcripts[di].append(file_details["filename"])
                    else:
                        di_to_transcripts[di] = [file_details["filename"]]

            # Download and merge transcripts to single file to act as the decision_item_corpus_map
            di_corpus_map = {}
            for di, files in di_to_transcripts.items():
                # Collect the transcript texts into a fake transcript document
                di_transcript_document = {
                    "format": "timestamped-sentences",
                    "annotations": [],
                    "confidence": None,
                    "data": []
                }

                # Use the provided save directory to download each file, read,
                # and add all data to the decision transcript document
                for filename in files:
                    saved = self.file_store.download_file(filename, save_dir, overwrite=True)
                    with open(saved, "r") as read_in:
                        transcript = json.load(read_in)
                        di_transcript_document["data"] += transcript["data"]

                # Use the provided save directory to download each minutes item file tied to the decision item
                # (usually the bill text, a presentation about the project or bill, or document about the appointment)
                # Parse each file and add each file's contents to the transcript data
                di_files = self.database.select_rows_as_list("minutes_item_file", filters=[("minutes_item_id", di)])
                for di_f in di_files:
                    # In case the file no longer exists 😡
                    try:
                        local_path = self.file_store._external_resource_copy(di_f["uri"], save_dir, overwrite=True)
                        parsed = parser.from_file(str(local_path))
                        # Sometimes the content can't be parsed 🤷
                        if parsed["content"]:
                            di_transcript_document["data"].append({
                                "text": parsed["content"],
                                "start_time": 0.0,
                                "end_time": 1.0
                            })
                    except requests.exceptions.HTTPError:
                        pass

                # Store the join of all transcripts in a single file for the corpus
                document_path = Path(save_dir) / f"document_{di}.json"
                with open(document_path, "w") as write_out:
                    json.dump(di_transcript_document, write_out)

                # Add the document path to the di corpus map
                di_corpus_map[di] = document_path

            return di_corpus_map

    def task_generate_index(self, minutes_item_corpus_map: Dict[str, Path]) -> Dict[str, Dict[str, float]]:
        """
        Generate word minutes item scores dictionary.
        """
        with RunManager(
            database=self.database,
            file_store=self.file_store,
            algorithm_name="MinutesItemIndexPipeline.task_generate_index",
            algorithm_version=get_module_version()
        ):
            return self.indexer.generate_index(minutes_item_corpus_map)

    def task_clean_index(self, index: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        """
        Clean the generated index prior to upload.
        """
        with RunManager(
            database=self.database,
            file_store=self.file_store,
            algorithm_name="MinutesItemIndexPipeline.task_clean_index",
            algorithm_version=get_module_version()
        ):
            return self.indexer.drop_terms_from_index_below_value(index)

    def _upload_indexed_minutes_item_term_minutes_item_values(self, mivft: ValuesForTerm):
        # Loop through each minutes item and value tied to this term and upload to database
        for minutes_item_id, value in mivft.values.items():
            self.database.upload_or_update_indexed_minutes_item_term(
                term=mivft.term,
                minutes_item_id=minutes_item_id,
                value=value
            )

    def task_upload_index(self, index: Dict[str, Dict[str, float]]):
        """
        Upload a word minutes item scores dictionary. This will completely replace a previous index.
        """
        with RunManager(
            database=self.database,
            file_store=self.file_store,
            algorithm_name="MinutesItemIndexPipeline.task_upload_index",
            algorithm_version=get_module_version()
        ):
            # Create upload items
            # This list of objects is just useful for making it easier to multithread the upload
            indexed_minutes_item_term_minutes_item_values = []
            for term, minutes_item_values in index.items():
                indexed_minutes_item_term_minutes_item_values.append(ValuesForTerm(term, minutes_item_values))

            # Multithread the upload/ update of the index
            with ThreadPoolExecutor(self.n_workers) as exe:
                exe.map(
                    self._upload_indexed_minutes_item_term_minutes_item_values,
                    indexed_minutes_item_term_minutes_item_values
                )

    def run(self):
        log.info("Starting index creation.")
        with RunManager(self.database, self.file_store, "MinutesItemIndexPipeline.run", get_module_version()):
            # Store the transcripts locally in a temporary directory
            with tempfile.TemporaryDirectory() as tmpdir:
                # Get the minutes item corpus map and download most recent transcripts to local machine
                log.info("Generating the minutes item corpus (decision item corpus)")
                minutes_item_corpus = self.task_generate_corpus(tmpdir)

                # Compute word minutes item scores
                log.info("Generating index")
                index = self.task_generate_index(minutes_item_corpus)

                # Clean the index
                log.info("Dropping minutes item terms with limited value")
                index = self.task_clean_index(index)

            # Upload word minutes item scores
            log.info("Uploading index")
            self.task_upload_index(index)

        log.info("Completed index creation.")
        log.info("=" * 80)
