#!/usr/bin/env python
# -*- coding: utf-8 -*-

# For testing
import random

from concurrent.futures import ThreadPoolExecutor
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
        self.audio_splitter = self.load_custom_object(
            module_path=self.config["audio_splitter"]["module_path"],
            object_name=self.config["audio_splitter"]["object_name"],
            object_kwargs=self.config["audio_splitter"].get("object_kwargs", {})
        )
        self.sr_model = self.load_custom_object(
            module_path=self.config["speech_recognition_model"]["module_path"],
            object_name=self.config["speech_recognition_model"]["object_name"],
            object_kwargs=self.config["speech_recognition_model"].get("object_kwargs", {})
        )

    def task_audio_get_or_copy(self, key: str, video_uri: str) -> str:
        """
        Get or copy and return audio resource uri provied key and video uri.
        """
        with RunManager(
            database=self.database,
            file_store=self.file_store,
            algorithm_name="EventPipeline.task_audio_get_or_copy",
            algorithm_version=get_module_version(),
            inputs=[key, video_uri],
            remove_files=True
        ) as run:
            # Check if audio already exists in file store
            tmp_audio_filepath = f"{key}_audio.wav"
            try:
                audio_uri = self.file_store.get_file_uri(filename=tmp_audio_filepath)
            except FileNotFoundError:
                # Store the video in temporary file
                tmp_video_filepath = f"tmp_{key}_video"
                tmp_video_filepath = self.file_store._external_resource_copy(
                    url=video_uri,
                    dst=tmp_video_filepath
                )

                # Split and store the audio in temporary file prior to upload
                tmp_audio_filepath = self.audio_splitter.split(
                    video_read_path=tmp_video_filepath,
                    audio_save_path=tmp_audio_filepath
                )
                tmp_audio_log_out_filepath = tmp_audio_filepath.with_suffix(".out")
                tmp_audio_log_err_filepath = tmp_audio_filepath.with_suffix(".err")

                # Remove tmp video file
                os.remove(tmp_video_filepath)

                # Store audio and logs
                audio_uri = self.file_store.upload_file(filepath=tmp_audio_filepath)
                audio_log_out_uri = self.file_store.upload_file(filepath=tmp_audio_log_out_filepath)
                audio_log_err_uri = self.file_store.upload_file(filepath=tmp_audio_log_err_filepath)
                # Store database records
                self.database.get_or_upload_file(audio_uri)
                self.database.get_or_upload_file(audio_log_out_uri)
                self.database.get_or_upload_file(audio_log_err_uri)
                # Register audio files with run manager
                run.register_output(tmp_audio_filepath)
                run.register_output(tmp_audio_filepath.with_suffix(".out"))
                run.register_output(tmp_audio_filepath.with_suffix(".err"))

            return audio_uri

    def task_transcript_get_or_create(self, key: str, audio_uri: str):
        """
        Get or create and return transcript resource uri provied key.
        """
        with RunManager(
            database=self.database,
            file_store=self.file_store,
            algorithm_name="EventPipeline.task_audio_get_or_copy",
            algorithm_version=get_module_version(),
            inputs=[key, audio_uri],
            remove_files=True
        ) as run:
            # Check if transcript already exists in file store
            tmp_transcript_filepath = f"{key}_transcript_0.txt"
            try:
                self.file_store.get_file_uri(filename=tmp_transcript_filepath)
            except FileNotFoundError:
                # Transcribe audio
                tmp_transcript_filepath, confidence = self.sr_model.transcribe(
                    audio_uri=audio_uri,
                    transcript_save_path=tmp_transcript_filepath
                )

                # Store and register transcript
                transcript_uri = self.file_store.upload_file(filepath=tmp_transcript_filepath)
                transcript_file_details = self.database.get_or_upload_file(transcript_uri)
                run.register_output(tmp_transcript_filepath)

            return transcript_file_details, confidence

    def process_event(self, event: Dict) -> str:
        # Create a key for the event
        key = hashlib.sha256(event["video_uri"].encode("utf8")).hexdigest()

        # Begin
        with RunManager(
            database=self.database,
            file_store=self.file_store,
            algorithm_name="EventPipeline.process_event",
            algorithm_version=get_module_version(),
            inputs=[event],
            remove_files=True
        ):
            # Check event already exists in database
            found_event = self.database.get_event(event["video_uri"])
            if found_event:
                log.info("Skipping event: {} ({})".format(key, found_event["id"]))
            else:
                log.info("Processing event: {} ({})".format(key, event["video_uri"]))

                # Run audio task
                audio_uri = self.task_audio_get_or_copy(key, event["video_uri"])

                # Run transcript task
                transcript_file_details, confidence = self.task_transcript_get_or_create(key, audio_uri)

                # Store or get body details
                body = event.pop("body")
                body_details = self.database.get_or_upload_body(body)

                # Store event
                event_details = self.database.get_or_upload_event(
                    body_id=body_details["id"],
                    event_datetime=event["event_datetime"],
                    source_uri=event["source_uri"],
                    video_uri=event["video_uri"]
                )

                # Link event to transcript
                self.database.get_or_upload_transcript(
                    event_id=event_details["id"],
                    file_id=transcript_file_details["id"],
                    confidence=confidence
                )

                log.info("Uploaded event details: {} ({})".format(event_details["id"], key))

            # Update progress
            log.info("Completed event: {} ({})".format(key, event["video_uri"]))

    def run(self):
        # Get events
        log.info("Starting event processing.")
        events = self.event_scraper.get_events()

        # For testing
        events = random.sample(events, 3)

        # Multiprocess each event found
        with RunManager(self.database, self.file_store, "EventPipeline.run", get_module_version()):
            with ThreadPoolExecutor(self.n_workers) as exe:
                exe.map(self.process_event, events)

        log.info("Completed event processing.")
        log.info("=" * 80)
