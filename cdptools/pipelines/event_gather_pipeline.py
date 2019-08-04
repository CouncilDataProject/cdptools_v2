#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .. import get_module_version
from ..dev_utils import RunManager
from .pipeline import Pipeline

###############################################################################

log = logging.getLogger(__name__)

###############################################################################


class EventGatherPipeline(Pipeline):

    def __init__(self, config_path: Union[str, Path]):
        # Resolve config path
        config_path = config_path.resolve(strict=True)

        # Read
        with open(config_path, "r") as read_in:
            self.config = json.load(read_in)

        # Get workers
        self.n_workers = self.config.get("max_synchronous_jobs")

        # Load modules
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
            algorithm_name="EventGatherPipeline.task_audio_get_or_copy",
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
                filename = video_uri.split("/")[-1]
                if "." in filename:
                    suffix = filename.split(".")[-1]
                else:
                    suffix = ""
                tmp_video_filepath = f"tmp_{key}_video.{suffix}"
                tmp_video_filepath = self.file_store._external_resource_copy(
                    uri=video_uri,
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

    def task_transcript_get_or_create(self, key: str, audio_uri: str, phrases: Optional[List[str]] = None):
        """
        Get or create and return transcript resource uri provied key.
        """
        with RunManager(
            database=self.database,
            file_store=self.file_store,
            algorithm_name="EventGatherPipeline.task_transcript_get_or_create",
            algorithm_version=get_module_version(),
            inputs=[key, audio_uri],
            remove_files=True
        ) as run:
            # Setup temporary filenames
            tmp_raw_transcript_filepath = f"{key}_raw_transcript_0.json"
            tmp_ts_words_transcript_filepath = f"{key}_ts_words_transcript_0.json"
            tmp_ts_sentences_transcript_filepath = f"{key}_ts_sentences_transcript_0.json"

            # Check if raw transcript already exists in file store
            try:
                # Try get the best variant of transcript
                # Timestamped sentences first
                try:
                    main_transcript_uri = self.file_store.get_file_uri(filename=tmp_ts_sentences_transcript_filepath)
                except FileNotFoundError:
                    # Timestamped words second
                    try:
                        main_transcript_uri = self.file_store.get_file_uri(filename=tmp_ts_words_transcript_filepath)
                    # Default to raw transcript
                    # If this isn't found, the first try except block will break and entirely new transcripts will be
                    # generated.
                    except FileNotFoundError:
                        main_transcript_uri = self.file_store.get_file_uri(filename=tmp_raw_transcript_filepath)

                main_transcript_details = self.database.get_or_upload_file(main_transcript_uri)
                confidence = self.database.select_rows_as_list(
                    table="transcript",
                    filters=[("file_id", main_transcript_details["file_id"])],
                    limit=1
                )[0]["confidence"]
            except FileNotFoundError:
                # Transcribe audio
                outputs = self.sr_model.transcribe(
                    audio_uri=audio_uri,
                    phrases=phrases,
                    raw_transcript_save_path=tmp_raw_transcript_filepath,
                    timestamped_words_save_path=tmp_ts_words_transcript_filepath,
                    timestamped_sentences_save_path=tmp_ts_sentences_transcript_filepath,
                )

                # Store and register transcript files
                raw_transcript_uri = self.file_store.upload_file(filepath=outputs.raw_path)
                raw_transcript_file_details = self.database.get_or_upload_file(raw_transcript_uri)
                run.register_output(outputs.raw_path)

                # Default to using the raw output as main transcript
                main_transcript_details = raw_transcript_file_details
                confidence = outputs.confidence

                # Timestamped transcripts are optional
                # If available store them but also set as main transcript
                if outputs.timestamped_words_path:
                    ts_words_transcript_uri = self.file_store.upload_file(filepath=outputs.timestamped_words_path)
                    ts_words_transcript_file_details = self.database.get_or_upload_file(ts_words_transcript_uri)
                    run.register_output(outputs.timestamped_words_path)
                    main_transcript_details = ts_words_transcript_file_details

                # Timestamped sentences provide a nicer viewing experience
                # If available store them but also set as main transcript
                if outputs.timestamped_sentences_path:
                    ts_sentences_transcript_uri = self.file_store.upload_file(
                        filepath=outputs.timestamped_sentences_path
                    )
                    ts_sentences_transcript_file_details = self.database.get_or_upload_file(ts_sentences_transcript_uri)
                    run.register_output(outputs.timestamped_sentences_path)
                    main_transcript_details = ts_sentences_transcript_file_details

            return main_transcript_details, confidence

    def task_parse_and_upload_constructed_event(self, event: Dict[str, Any]):
        with RunManager(
            database=self.database,
            file_store=self.file_store,
            algorithm_name="EventGatherPipeline.task_parse_and_upload_constructed_event",
            algorithm_version=get_module_version(),
            inputs=[event["source_uri"]]
        ):
            # Store or get body details
            body_details = self.database.get_or_upload_body(event["body"])

            # Store event
            event_details = self.database.get_or_upload_event(
                body_id=body_details["body_id"],
                event_datetime=event["event_datetime"],
                source_uri=event["source_uri"],
                video_uri=event["video_uri"],
                agenda_file_uri=event["agenda_file_uri"],
                minutes_file_uri=event["minutes_file_uri"],
                legistar_event_id=event["legistar_event_id"],
                legistar_event_link=event["legistar_event_link"]
            )

            # Store or get all minute_items
            for m_item in event["minutes_items"]:
                # Store or get minutes item
                minutes_item_details = self.database.get_or_upload_minutes_item(
                    name=m_item["name"],
                    matter=m_item["matter"],
                    legistar_event_item_id=m_item["legistar_event_item_id"]
                )

                # Store any attachments
                for attachment in m_item["attachments"]:
                    self.database.get_or_upload_minutes_item_file(
                        minutes_item_id=minutes_item_details["minutes_item_id"],
                        uri=attachment["uri"],
                        name=attachment["name"],
                        legistar_matter_attachment_id=attachment["legistar_matter_attachment_id"]
                    )

                # Attach minutes item to event
                event_minutes_item_details = self.database.get_or_upload_event_minutes_item(
                    event_id=event_details["event_id"],
                    minutes_item_id=minutes_item_details["minutes_item_id"],
                    index=m_item["index"],
                    decision=m_item["decision"]
                )

                # Store any votes and persons
                for vote in m_item["votes"]:
                    person_details = self.database.get_or_upload_person(
                        full_name=vote["person"]["full_name"],
                        email=vote["person"]["email"],
                        phone=vote["person"]["phone"],
                        website=vote["person"]["website"],
                        legistar_person_id=vote["person"]["legistar_person_id"]
                    )

                    self.database.get_or_upload_vote(
                        person_id=person_details["person_id"],
                        event_minutes_item_id=event_minutes_item_details["event_minutes_item_id"],
                        decision=vote["decision"],
                        legistar_event_item_vote_id=vote["legistar_event_item_vote_id"]
                    )

            # Link event to transcript
            self.database.get_or_upload_transcript(
                event_id=event_details["event_id"],
                file_id=event["transcript_details"]["transcript_file_details"]["file_id"],
                confidence=event["transcript_details"]["confidence"]
            )

            return event_details

    def process_event(self, event: Dict) -> str:
        # Create a key for the event
        key = hashlib.sha256(event["video_uri"].encode("utf8")).hexdigest()

        # Begin
        with RunManager(
            database=self.database,
            file_store=self.file_store,
            algorithm_name="EventGatherPipeline.process_event",
            algorithm_version=get_module_version(),
            inputs=[event["source_uri"]],
            remove_files=True
        ):
            # Check event already exists in database
            found_event = self.database.get_event(event["video_uri"])
            if found_event:
                log.info("Skipping event: {} ({})".format(key, found_event["event_id"]))
            else:
                log.info("Processing event: {} ({})".format(key, event["video_uri"]))

                # Run audio task
                audio_uri = self.task_audio_get_or_copy(key, event["video_uri"])

                # Create list of phrases to send to sr model
                phrases = [item["name"] for item in event["minutes_items"]]

                # Run transcript task
                transcript_file_details, confidence = self.task_transcript_get_or_create(key, audio_uri, phrases)

                # Attach transcript details to event
                event["transcript_details"] = {
                    "transcript_file_details": transcript_file_details,
                    "confidence": confidence
                }

                # Event details
                event_details = self.task_parse_and_upload_constructed_event(event)
                log.info("Uploaded event details: {} ({})".format(event_details["event_id"], key))

            # Update progress
            log.info("Completed event: {} ({})".format(key, event["video_uri"]))

    def run(self):
        log.info("Starting event processing.")
        with RunManager(
            self.database,
            self.file_store,
            "EventGatherPipeline.run",
            get_module_version(),
            remove_files=True
        ):
            # Get events
            with RunManager(self.database, self.file_store, "EventScraper.get_events", get_module_version()):
                events = self.event_scraper.get_events()

            # Multiprocess each event found
            with ThreadPoolExecutor(self.n_workers) as exe:
                exe.map(self.process_event, events)

        log.info("Completed event processing.")
        log.info("=" * 80)
