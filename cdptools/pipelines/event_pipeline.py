#!/usr/bin/env python
# -*- coding: utf-8 -*-

from concurrent.futures import ThreadPoolExecutor
import json
import logging
from pathlib import Path
from typing import Dict, Union

from .pipeline import Pipeline

###############################################################################

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)4s:%(lineno)4s %(asctime)s] %(message)s'
)
log = logging.getLogger()

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
        # self.sr_model = super().load_custom_object(
        #     module_path=self.config["speech_recognition_model"]["module_path"],
        #     object_name=self.config["speech_recognition_model"]["object_name"],
        #     object_kwargs=self.config["speech_recognition_model"].get("object_kwargs", {})
        # )
        log.info("=" * 80)

    def process_event(self, event: Dict) -> str:
        # Get event key
        key = event["sha256"]
        try:
            # Check event already exists
            if self.database.get_event(key):
                log.info(f"Event already exists: {key}")
            else:
                log.info(f"Processing new event: {key}")

                # Create local copy of video
                log.info(f"Beginning video copy...")
                local_video_path = self.file_store.store_file(
                    file=event["video_url"],
                    key=key,
                    save_name="video.mp4"
                )
                log.info(f"Stored video at: {local_video_path}")

                # Create audio split of video
                # temp_audio_path = self.audio_splitters.split(local_paths["video"])
                #
                # # Store audio split in file store
                # local_paths["audio"] = self.file_store.store("audio", temp_audio_path, remove=True)
                #
                # # Transcribe audio to text
                # transcript = self.sr_model.transcribe(local_paths["audio"])

                # Store event
                log.info("Beginning event details upload...")
                event = self.database.upload_event(event)
        except Exception as e:
            # TODO: push exception log to database
            raise e

    def run(self):
        # TODO: wrap this in a scheduler

        try:
            # Get events
            log.info("Beginning event collection.")
            events = self.event_scraper.get_events()

            # Multithread each event found
            with ThreadPoolExecutor(self.n_workers) as exe:
                exe.map(self.process_event, events)

            log.info(f"Completed event processing.")

        except Exception as e:
            # TODO: push exception log to database
            raise e
