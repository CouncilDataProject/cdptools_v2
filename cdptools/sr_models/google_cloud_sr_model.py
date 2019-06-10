#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
from pathlib import Path
from typing import List, Optional, Union

from google.cloud import speech_v1p1beta1 as speech

from .sr_model import SRModel, SRModelOutputs

###############################################################################

log = logging.getLogger(__name__)

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
        phrases: Optional[List[str]] = None,
        **kwargs
    ) -> SRModelOutputs:
        # Check paths
        raw_transcript_save_path = Path(raw_transcript_save_path).resolve()
        timestamped_words_save_path = Path(timestamped_words_save_path).resolve()
        timestamped_sentences_save_path = Path(timestamped_sentences_save_path).resolve()

        # Create client
        client = speech.SpeechClient.from_service_account_json(self.credentials_path)

        # Create basic metadata
        metadata = speech.types.RecognitionMetadata()
        metadata.interaction_type = speech.enums.RecognitionMetadata.InteractionType.DISCUSSION

        # Add phrases
        if phrases:
            # Clean and apply usage limits
            cleaned = []
            total_character_count = 0
            for phrase in phrases[:500]:
                if total_character_count < 10000:
                    cleaned_phrase = phrase[:100]
                    cleaned.append(cleaned_phrase[:cleaned_phrase.rfind(" ")])

            # Send to speech context
            speech_context = speech.types.SpeechContext(phrases=cleaned)
        else:
            speech_context = speech.types.SpeechContext()

        # Prepare for transcription
        config = speech.types.RecognitionConfig(
            encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,
            speech_contexts=[speech_context],
            metadata=metadata
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
        timestamped_words = []
        for result in response.results:
            # Some portions of audio may not have text
            if len(result.alternatives) > 0:
                # Check length of transcript result
                word_list = result.alternatives[0].words
                if len(word_list) > 0:
                    for word in word_list:
                        start_time = word.start_time.seconds + word.start_time.nanos * 1e-9
                        end_time = word.end_time.seconds + word.end_time.nanos * 1e-9
                        timestamped_words.append({"word": word.word, "start_time": start_time, "end_time": end_time})

                    # Update confidence stats
                    confidence_sum += result.alternatives[0].confidence
                    segments += 1

        # Create timestamped sentences
        timestamped_sentences = []
        current_sentence = None
        for word_details in timestamped_words:
            # Create new sentence
            if current_sentence is None:
                current_sentence = {"sentence": word_details["word"], "start_time": word_details["start_time"]}
            # Update current sentence
            else:
                current_sentence["sentence"] += " {}".format(word_details["word"])

            # End current sentence and reset
            if word_details["word"][-1] == ".":
                current_sentence["end_time"] = word_details["end_time"]
                timestamped_sentences.append(current_sentence)
                current_sentence = None

        # Create raw transcript
        raw_transcript = " ".join([word_details["word"] for word_details in timestamped_words])

        # Compute mean confidence
        if segments > 0:
            confidence = confidence_sum / segments
        else:
            confidence = 0.0
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
