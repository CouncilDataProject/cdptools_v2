#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
from pathlib import Path
from typing import Union

from google.cloud import speech_v1p1beta1 as speech

from .sr_model import SRModel, SRModelOutputs

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

    def transcribe(
        self,
        audio_uri: Union[str, Path],
        raw_transcript_save_path: Union[str, Path],
        timestamped_words_save_path: Union[str, Path],
        timestamped_sentences_save_path: Union[str, Path],
        **kwargs
    ) -> SRModelOutputs:
        # Check paths
        raw_transcript_save_path = Path(raw_transcript_save_path).resolve()
        timestamped_words_save_path = Path(timestamped_words_save_path).resolve()
        timestamped_sentences_save_path = Path(timestamped_sentences_save_path).resolve()

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
        confidence_sum = 0
        segments = 0
        timestamped_words = {}
        for result in response.results:
            # Some portions of audio may not have text
            if len(result.alternatives) > 0:
                # Check length of transcript result
                word_list = result.alternatives[0].words
                if len(word_list) > 0:
                    for word in word_list:
                        start_time = word.start_time.seconds + word.start_time.nanos * 1e-9
                        timestamped_words[start_time] = word.word

                    # Update confidence stats
                    confidence_sum += result.alternatives[0].confidence
                    segments += 1

        # Create timestamped sentences
        timestamped_sentences = {}
        current_start_time = None
        for start_time, word in timestamped_words.items():
            # Update current start time
            if current_start_time is None:
                current_start_time = start_time

            # Create or update sentence
            if current_start_time in timestamped_sentences:
                timestamped_sentences[current_start_time] += f" {word}"
            else:
                timestamped_sentences[current_start_time] = word

            # Reset current start time if sentence end
            if word[-1] == ".":
                current_start_time = None

        # Create raw transcript
        raw_transcript = " ".join(timestamped_words.values())

        # Compute mean confidence
        confidence = confidence_sum / segments
        log.info(f"Completed transcription for: {audio_uri}. Confidence: {confidence}")

        # Write files
        with open(timestamped_words_save_path, "w") as write_out:
            json.dump(timestamped_words, write_out)

        with open(timestamped_sentences_save_path, "w") as write_out:
            json.dump(timestamped_sentences, write_out)

        with open(raw_transcript_save_path, "w") as write_out:
            write_out.write(raw_transcript)

        # Return the save path
        return SRModelOutputs(
            raw_transcript_save_path,
            confidence,
            timestamped_words_save_path,
            timestamped_sentences_save_path
        )
