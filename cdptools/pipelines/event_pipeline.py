#!/usr/bin/env python
# -*- coding: utf-8 -*-

# For testing
import random

from concurrent.futures import ThreadPoolExecutor
from functools import partial
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Union

from .pipeline import Pipeline
from ..utils import RunManager
from .. import get_module_version

###############################################################################

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)4s: %(module)s:%(lineno)4s %(asctime)s] %(message)s'
)
log = logging.getLogger(__file__)

###############################################################################


class EventPipeline(Pipeline):

    def __init__(self, config_path: Union[str, Path]):
        # Resolve config path
        config_path = config_path.resolve(strict=True)

        # Read
        with open(config_path, "r") as read_in:
            self.config = json.load(read_in)

        # Get workers
        self.n_workers = self.config.get("max_synchronous_jobs")

        # Load event scraper
        self.event_scraper = self.load_custom_object(
            module_path=self.config["event_scraper"]["module_path"],
            object_name=self.config["event_scraper"]["object_name"],
            object_kwargs=self.config["event_scraper"].get("object_kwargs", {})
        )
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

    @staticmethod
    def process_event(event: Dict, config: Dict, module_loader: callable) -> str:
        # Create a key for the event
        key = hashlib.sha256(event["video_uri"].encode("utf8")).hexdigest()

        # Initialize all modules
        database = module_loader(
            module_path=config["database"]["module_path"],
            object_name=config["database"]["object_name"],
            object_kwargs={**config["database"].get("object_kwargs", {}), **{"name": f"db_{key}"}}
        )
        file_store = module_loader(
            module_path=config["file_store"]["module_path"],
            object_name=config["file_store"]["object_name"],
            object_kwargs=config["file_store"].get("object_kwargs", {})
        )
        audio_splitter = module_loader(
            module_path=config["audio_splitter"]["module_path"],
            object_name=config["audio_splitter"]["object_name"],
            object_kwargs=config["audio_splitter"].get("object_kwargs", {})
        )
        sr_model = module_loader(
            module_path=config["speech_recognition_model"]["module_path"],
            object_name=config["speech_recognition_model"]["object_name"],
            object_kwargs=config["speech_recognition_model"].get("object_kwargs", {})
        )

        # Begin
        with RunManager(
            database=database,
            file_store=file_store,
            algorithm_name="EventPipeline.process_event",
            algorithm_version=get_module_version(),
            inputs=[event],
            remove_files=True
        ) as run:
            # Get body details
            body = event.pop("body")
            body_details = database.get_or_upload_body(body)

            # Check event already exists in database
            found_event = database.get_event(event["video_uri"])
            if found_event:
                log.debug("Event already exists: {}".format(found_event["id"]))
            else:
                log.info("Processing event: {}".format(event["video_uri"]))

                # Check if audio already exists in file store
                tmp_audio_filepath = f"{key}_audio.wav"
                try:
                    audio_uri = file_store.get_file_uri(filename=tmp_audio_filepath)
                except FileNotFoundError:
                    # Store the video in temporary file
                    tmp_video_filepath = f"tmp_{key}_video"
                    tmp_video_filepath = file_store._external_resource_copy(
                        url=event["video_uri"],
                        dst=tmp_video_filepath
                    )

                    # Split and store the audio in temporary file prior to upload
                    tmp_audio_filepath = audio_splitter.split(
                        video_read_path=tmp_video_filepath,
                        audio_save_path=tmp_audio_filepath
                    )
                    tmp_audio_log_out_filepath = tmp_audio_filepath.with_suffix(".out")
                    tmp_audio_log_err_filepath = tmp_audio_filepath.with_suffix(".err")

                    # Remove tmp video file
                    os.remove(tmp_video_filepath)

                    # Store audio and logs
                    audio_uri = file_store.upload_file(filepath=tmp_audio_filepath)
                    audio_log_out_uri = file_store.upload_file(filepath=tmp_audio_log_out_filepath)
                    audio_log_err_uri = file_store.upload_file(filepath=tmp_audio_log_err_filepath)
                    # Store database records
                    database.get_or_upload_file(audio_uri, tmp_audio_filepath.name)
                    database.get_or_upload_file(audio_log_out_uri, tmp_audio_log_out_filepath.name)
                    database.get_or_upload_file(audio_log_err_uri, tmp_audio_log_err_filepath.name)
                    # Register audio files with run manager
                    run.register_output(tmp_audio_filepath)
                    run.register_output(tmp_audio_filepath.with_suffix(".out"))
                    run.register_output(tmp_audio_filepath.with_suffix(".err"))

                # Check if transcript already exists in file store
                tmp_transcript_filepath = f"{key}_transcript_0.txt"
                try:
                    file_store.get_file_uri(filename=tmp_transcript_filepath)
                except FileNotFoundError:
                    # Transcribe audio
                    tmp_transcript_filepath, confidence = sr_model.transcribe(
                        audio_uri=audio_uri,
                        transcript_save_path=tmp_transcript_filepath
                    )

                    # Store and register transcript
                    transcript_uri = file_store.upload_file(filepath=tmp_transcript_filepath)
                    transcript_file_details = database.get_or_upload_file(transcript_uri, tmp_transcript_filepath.name)
                    run.register_output(tmp_transcript_filepath)

                # Store event
                event_details = database.get_or_upload_event(
                    body_id=body_details["id"],
                    event_datetime=event["event_datetime"],
                    source_uri=event["source_uri"],
                    video_uri=event["video_uri"]
                )

                # Link event to transcript
                database.get_or_upload_transcript(
                    event_id=event_details["id"],
                    file_id=transcript_file_details["id"],
                    confidence=confidence
                )

        # Update progress
        log.info("Completed processing for event: {}".format(event["video_uri"]))

    def run(self):
        # Get events
        log.info("Starting event processing.")
        events = self.event_scraper.get_events()

        # For testing
        events = random.sample(events, 1)

        # Initialize partial
        process_func = partial(self.process_event, config=self.config, module_loader=self.load_custom_object)

        # Multiprocess each event found
        with RunManager(self.database, self.file_store, "EventPipeline.run", get_module_version()):
            # with ThreadPoolExecutor(self.n_workers) as exe:
            #     exe.map(process_func, events)
            for event in events:
                process_func(event)

        log.info("Completed event processing.")
        log.info("=" * 80)
