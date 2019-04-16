#!/usr/bin/env python
# -*- coding: utf-8 -*-

# For testing
import random

from concurrent.futures import ProcessPoolExecutor
from functools import partial
import json
import logging
import os
from pathlib import Path
import traceback
from typing import Dict, Union

from .pipeline import Pipeline

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
            object_kwargs=self.config["database"].get("object_kwargs", {})
        )

    @staticmethod
    def process_event(event: Dict, config: Dict, module_loader: callable) -> str:
        # Get event key
        key = event["key"]

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
        try:
            # Check event already exists in database
            if database.get_event(key):
                log.debug(f"Event already exists: {key}")
            else:
                log.info(f"Processing event: {key}")

                # Check if audio already exists in file store
                tmp_audio_filepath = f"{key}_audio.wav"
                try:
                    audio_uri = file_store.get_file_uri(filename=tmp_audio_filepath)
                except FileNotFoundError:
                    # Store the video in temporary file
                    tmp_video_filepath = f"tmp_{key}_video"
                    tmp_video_filepath = file_store._external_resource_copy(
                        url=event["video_url"],
                        dst=tmp_video_filepath
                    )

                    # Split and store the audio in temporary file prior to upload
                    tmp_audio_filepath = audio_splitter.split(
                        video_read_path=tmp_video_filepath,
                        audio_save_path=tmp_audio_filepath
                    )

                    # Remove tmp video file
                    os.remove(tmp_video_filepath)

                    # Store audio and logs
                    audio_uri = file_store.upload_file(
                        filepath=tmp_audio_filepath,
                        content_type="audio/wav",
                        remove=True
                    )
                    file_store.upload_file(
                        filepath=f"{key}_audio_log.out",
                        content_type="text/plain",
                        remove=True
                    )
                    file_store.upload_file(
                        filepath=f"{key}_audio_log.err",
                        content_type="text/plain",
                        remove=True
                    )

                # Check if transcript already exists in file store
                tmp_transcript_filepath = f"{key}_transcript_0.txt"
                try:
                    transcript_uri = file_store.get_file_uri(filename=tmp_transcript_filepath)
                except FileNotFoundError:
                    # Transcribe audio
                    tmp_transcript_filepath = sr_model.transcribe(
                        audio_uri=audio_uri,
                        transcript_save_path=tmp_transcript_filepath
                    )

                    # Upload transcript
                    transcript_uri = file_store.upload_file(
                        filepath=tmp_transcript_filepath,
                        content_type="text/plain",
                        remove=True
                    )

                # Upload transcript details
                transcript_id = f"{key}_0"
                database.upload_transcript({
                    "key": transcript_id,
                    "event_id": key,
                    "uri": transcript_uri
                })

                # Update event
                event["transcript_ids"] = [transcript_id]

                # Store event
                database.upload_event(event)
        except Exception as e:
            # Upload error
            log.info("Something went wrong... Uploading error details.")
            database.upload_error({
                "error": str(e),
                "traceback": traceback.format_exc(),
                "event": event
            })

        # Update progress
        log.info(f"Completed processing for event: {key}")

    def run(self):
        # Get events
        log.info("Starting event processing.")
        events = self.event_scraper.get_events()

        # For testing
        events = random.sample(events, 1)

        # Initialize partial
        process_func = partial(self.process_event, config=self.config, module_loader=self.load_custom_object)

        # Multiprocess each event found
        with ProcessPoolExecutor(self.n_workers) as exe:
            exe.map(process_func, events)

        log.info("Completed event processing.")
        log.info("=" * 80)
