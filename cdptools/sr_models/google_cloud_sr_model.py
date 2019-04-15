#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from pathlib import Path
from typing import Union

from google.cloud import speech

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

    def transcribe(self, audio_uri: str, transcript_save_path: Union[str, Path]) -> Path:
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
            language_code="en-US"
        )
        audio = speech.types.RecognitionAudio(uri=audio_uri)

        # Begin transcription
        log.debug(f"Beginning transcription for: {audio_uri}")
        operation = client.long_running_recognize(config, audio)

        # Wait for complete
        response = operation.result(timeout=4000)

        # Select highest confidence transcripts
        full_transcript = " ".join([
            result.alternatives[0].transcript for result in response.results if len(result.alternatives) > 0
        ])
        log.info(f"Completed transcription for: {audio_uri}")

        # Store transcript
        with open(transcript_save_path, "w") as write_out:
            write_out.write(full_transcript)
        log.debug(f"Stored transcript at: {transcript_save_path}")

        # Return the save path
        return transcript_save_path
