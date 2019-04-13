#!/usr/bin/env python
# -*- coding: utf-8 -*-

from concurrent.futures import ThreadPoolExecutor
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

        # Get cron schedule
        self.cron = self.config.get("cron_schedule")
        self.n_workers = self.config.get("max_synchronous_jobs")

        # Load modules
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
        self.file_store = super().load_custom_object(
            module_path=self.config["file_store"]["module_path"],
            object_name=self.config["file_store"]["object_name"],
            object_kwargs=self.config["file_store"].get("object_kwargs", {})
        )
        self.audio_splitter = super().load_custom_object(
            module_path=self.config["audio_splitter"]["module_path"],
            object_name=self.config["audio_splitter"]["object_name"],
            object_kwargs=self.config["audio_splitter"].get("object_kwargs", {})
        )
        # self.sr_model = super().load_custom_object(
        #     module_path=self.config["speech_recognition_model"]["module_path"],
        #     object_name=self.config["speech_recognition_model"]["object_name"],
        #     object_kwargs=self.config["speech_recognition_model"].get("object_kwargs", {})
        # )
        log.info("=" * 80)

    def process_event(self, event: Dict) -> str:
        # Get event key
        key = event["key"]
        try:
            # Check event already exists
            if self.database.get_event(key):
                log.debug(f"Event already exists: {key}")
            else:
                log.debug(f"Processing event: {key}")

                # Check for video file
                video_suffix = event["video_url"].split(".")[-1]
                try:
                    local_video_path = self.file_store.get_file(key, filename=f"video.{video_suffix}")
                except FileNotFoundError:
                    # Create local copy of video
                    log.debug("Beginning video copy...")
                    local_video_path = self.file_store.store_file(
                        file=event["video_url"],
                        key=key,
                        save_name=f"video.{video_suffix}"
                    )
                    log.debug(f"Stored video at: {local_video_path}")

                # Check for audio file
                try:
                    local_audio_path = self.file_store.get_file(key=key, filename="audio.mp3")
                except FileNotFoundError:
                    # Create audio file
                    log.debug("Beginning audio split...")
                    local_audio_path = self.audio_splitter.split(
                        video_read_path=local_video_path,
                        audio_save_path=local_video_path.parent / "audio.mp3"
                    )
                    log.debug(f"Stored audio at: {local_audio_path}")

                # # Transcribe audio to text
                # transcript = self.sr_model.transcribe(local_paths["audio"])

                # Store event
                event = self.database.upload_event(event)
        except Exception as e:
            # Create error
            to_store_error = {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "event": event
            }
            # Upload
            log.info("Something went wrong... Uploading error details.")
            self.database.upload_error(to_store_error)

        # Finish
        log.info(f"Finished processing event: {key}")

    def run(self):
        # TODO: wrap this in a scheduler

        try:
            # Get events
            log.info("Beginning event collection.")
            events = self.event_scraper.get_events()[:3]

            # Multithread each event found
            with ThreadPoolExecutor(self.n_workers) as exe:
                exe.map(self.process_event, events)

            log.info(f"Completed event processing.")

        except Exception as e:
            # TODO: push exception log to database
            raise e
