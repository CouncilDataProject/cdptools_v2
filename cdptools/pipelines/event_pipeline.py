#!/usr/bin/env python
# -*- coding: utf-8 -*-

# For testing
# import random

from concurrent.futures import ProcessPoolExecutor
from functools import partial
import json
import logging
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
        self.event_scraper = super().load_custom_object(
            module_path=self.config["event_scraper"]["module_path"],
            object_name=self.config["event_scraper"]["object_name"],
            object_kwargs=self.config["event_scraper"].get("object_kwargs", {})
        )
        self.database = super().load_custom_object(
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
            # Check event already exists
            if database.get_event(key):
                log.debug(f"Event already exists: {key}")
            else:
                log.info(f"Processing event: {key}")

                # Check for video file
                video_suffix = event["video_url"].split(".")[-1]
                try:
                    local_video_path = file_store.get_file(key, filename=f"video.{video_suffix}")
                except FileNotFoundError:
                    # Create local copy of video
                    local_video_path = file_store.store_file(
                        file=event["video_url"],
                        key=key,
                        save_name=f"video.{video_suffix}"
                    )

                # Check for audio file
                try:
                    local_audio_path = file_store.get_file(key=key, filename="audio.raw")
                except FileNotFoundError:
                    # Create audio file
                    local_audio_path = audio_splitter.split(
                        video_read_path=local_video_path,
                        audio_save_path=local_video_path.parent / "audio.raw"
                    )

                # Check for transcript
                # try:
                #     local_transcript_path = file_store.get_file(key=key, filename="initial_transcript.txt")
                # except FileNotFoundError:
                #     # Transcribe audio to text
                #     transcript = sr_model.transcribe(
                #         audio_read_path=local_audio_path,
                #         transcript_save_path=local_audio_path.parent / f"initial_transcript.txt"
                #     )

                # Store event
                event = database.upload_event(event)
        except Exception as e:
            # Create error
            to_store_error = {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "event": event
            }
            # Upload
            log.info("Something went wrong... Uploading error details.")
            database.upload_error(to_store_error)

        # Update progress
        log.info(f"Completed processing for event: {key}")

    def run(self):
        # Get events
        log.info("Starting event processing.")
        events = self.event_scraper.get_events()

        # For testing
        # events = random.sample(events, 1)

        # Initialize partial
        process_func = partial(self.process_event, config=self.config, module_loader=super().load_custom_object)

        # Multiprocess each event found
        with ProcessPoolExecutor(self.n_workers) as exe:
            exe.map(process_func, events)

        log.info("Completed event processing.")
        log.info("=" * 80)
