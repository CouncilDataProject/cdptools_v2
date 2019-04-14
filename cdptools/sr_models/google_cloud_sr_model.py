#!/usr/bin/env python
# -*- coding: utf-8 -*-

from concurrent.futures import ThreadPoolExecutor
import logging
import operator
import os
from pathlib import Path
from typing import NamedTuple, Union

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

from .sr_model import SRModel

###############################################################################

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)4s: %(module)s:%(lineno)4s %(asctime)s] %(message)s'
)
log = logging.getLogger(__file__)

###############################################################################

MAX_CHUNK_SIZE = 64000

###############################################################################


class AudioChunk(NamedTuple):
    index: int
    content: bytes


class TranscriptChunk(NamedTuple):
    index: int
    content: str

###############################################################################


class GoogleCloudSRModel(SRModel):

    def __init__(self, credentials_path: Union[str, Path]):
        # Resolve credentials
        credentials_path = Path(credentials_path).resolve(strict=True)

        # Store path in env variable
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials_path)

    @staticmethod
    def _read_in_chunks(file_object, chunk_size: int = MAX_CHUNK_SIZE) -> AudioChunk:
        # Use an index to sort the list once all chunks have been processed
        index = 0

        # Read until end
        while True:
            # Update index
            index += 1

            # Read chunk
            chunk = file_object.read(chunk_size)

            # If data is empty, break out
            if not chunk:
                break

            # Yield the data
            yield AudioChunk(index, chunk)

    @staticmethod
    def _transcribe_chunk(audio_chunk: AudioChunk) -> str:
        # Create cloud client
        client = speech.SpeechClient()
        config = types.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US"
        )

        # Process content_chunk
        audio = types.RecognitionAudio(content=audio_chunk.content)
        response = client.recognize(config, audio)

        # Select highest confidence transcripts
        transcripts = [result.alternatives[0].transcript for result in response.results]

        # Make and return a new content chunk with the results
        return TranscriptChunk(audio_chunk.index, " ".join(transcripts))

    def transcribe(self, audio_read_path: Union[str, Path], transcript_save_path: Union[str, Path]) -> Path:
        # Check path
        audio_read_path = Path(audio_read_path).resolve(strict=True)
        transcript_save_path = Path(transcript_save_path).resolve()
        if transcript_save_path.is_file():
            return transcript_save_path

        # Read audio data and create chunks due to google size limits
        log.debug(f"Beginning transcription for: {audio_read_path}")
        with open(audio_read_path, "rb") as audio_file:
            with ThreadPoolExecutor() as exe:
                transcript_chunks = list(exe.map(self._transcribe_chunk, self._read_in_chunks(audio_file)))
        log.debug(f"Completed transcription for: {audio_read_path}")

        # Sort transcript chunks
        transcript_chunks.sort(key=operator.attrgetter("index"), reverse=True)
        full_transcript = " ".join([t.content for t in transcript_chunks])

        # Store transcript
        with open(transcript_save_path, "w") as write_out:
            write_out.write(full_transcript)
        log.debug(f"Stored transcript at: {transcript_save_path}")

        # Return the save path
        return transcript_save_path
