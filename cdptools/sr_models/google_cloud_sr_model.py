#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
from pathlib import Path
from typing import Tuple, Union

from google.cloud import speech_v1p1beta1 as speech

from .sr_model import SRModel

###############################################################################

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)4s: %(module)s:%(lineno)4s %(asctime)s] %(message)s'
)
log = logging.getLogger(__file__)

###############################################################################


class GoogleCloudSRModel(SRModel):

    def __init__(self, credentials_path: Union[str, Path], **kwargs):
        # Resolve credentials
        self.credentials_path = Path(credentials_path).resolve(strict=True)

    def transcribe(self, audio_uri: str, transcript_save_path: Union[str, Path]) -> Tuple[Path, float]:
        # Check path
        transcript_save_path = Path(transcript_save_path).resolve()
        if transcript_save_path.is_file():
            return transcript_save_path

        # Create client
        client = speech.SpeechClient.from_service_account_json(self.credentials_path)

        # Prepare for transcription
        config = speech.types.RecognitionConfig(
            encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True
        )
        audio = speech.types.RecognitionAudio(uri=audio_uri)

        # Begin transcription
        log.debug(f"Beginning transcription for: {audio_uri}")
        operation = client.long_running_recognize(config, audio)

        # Wait for complete
        response = operation.result(timeout=4000)

        # Select highest confidence transcripts
        full_transcript = None
        confidence_sum = 0
        segments = 0
        timestamped_transcript = {}
        for result in response.results:
            # Some portions of audio may not have text
            if len(result.alternatives) > 0:
                # Check length of transcript result
                transcript_result = result.alternatives[0].transcript
                word_details = result.alternatives[0].words
                if len(word_details) > 0:
                    start_time = word_details[0].start_time.seconds + word_details[0].start_time.nanos * 1e-9
                    timestamped_transcript[start_time] = " ".join([wd.word for wd in word_details])
                if len(transcript_result) > 0:
                    # Initial start
                    if full_transcript:
                        full_transcript = f"{full_transcript} {transcript_result}"
                    else:
                        full_transcript = transcript_result

                    # Update confidence stats
                    confidence_sum += result.alternatives[0].confidence
                    segments += 1

        with open("timestamped_transcript.json", "w") as write_out:
            json.dump(timestamped_transcript, write_out)

        # Compute mean confidence
        confidence = confidence_sum / segments
        log.info(f"Completed transcription for: {audio_uri}")

        # Store transcript
        with open(transcript_save_path, "w") as write_out:
            write_out.write(full_transcript)
        log.debug(f"Stored transcript at: {transcript_save_path}")

        # Return the save path
        return transcript_save_path, confidence
