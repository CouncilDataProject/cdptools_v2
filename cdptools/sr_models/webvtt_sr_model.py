#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import json
import logging
import re
import requests
import truecase
import webvtt

from pathlib import Path
from typing import List, Dict, Union

from . import constants
from .sr_model import SRModel, SRModelOutputs

###############################################################################

log = logging.getLogger(__name__)

###############################################################################


class WebVttSRModel(SRModel):
    def __init__(self, new_turn_pattern: str, **kwargs):
        # New speaker turn must begin with one or more new_turn_pattern_str
        self.new_turn_pattern = r"^({})+\s*(.+)$".format(new_turn_pattern)
        # Nentence must be ended by period, question mark, or exclamation point.
        self.end_of_sentence_pattern = r"^.+[.?!]\s*$"

    def _true_case(self, text: str) -> str:
        normalized_text = truecase.get_true_case(text)
        # normalized_text = re.sub('[$] ', ' $', normalized_text)
        return normalized_text

    def _request_caption_content(self, source_uri: str) -> str:
        # Get the content of source_uri
        response = requests.get(source_uri)
        response.raise_for_status()
        return response.text

    def _get_sentences(self, source_uri: str) -> List[Dict[str, Union[str, float]]]:
        # Create file-like object of caption file's content
        buffer = io.StringIO(self._request_caption_content(source_uri))
        # Get list of caption block
        captions = webvtt.read_buffer(buffer).captions
        buffer.close()

        # Create timestamped sentences
        sentences = []
        # List of text, representing a sentence
        lines = []
        start_time = 0
        for caption in captions:
            start_time = start_time or caption.start_in_seconds
            lines.append(caption.text)
            end_sentence_search = re.search(self.end_of_sentence_pattern, caption.text)
            # Caption block is a end of sentence block
            if end_sentence_search:
                sentence = {'start_time': start_time,
                            'end_time': caption.end_in_seconds,
                            'text': ' '.join(lines)}
                sentences.append(sentence)
                # Reset lines and start_time, for start of new sentence
                lines = []
                start_time = 0

        # If any leftovers in lines, add a sentence for that.
        if lines:
            sentences.append({'start_time': start_time,
                              'end_time': captions[-1].end_in_seconds,
                              'text': ' '.join(lines)})
        return sentences

    def _get_speaker_turns(self, source_uri: str) -> List[Dict[str, Union[str, List[Dict[str, Union[str, float]]]]]]:
        # Get timestamped sentences
        sentences = self._get_sentences(source_uri)

        # Create timestamped speaker turns
        turns = []
        for sentence in sentences:
            new_turn_search = re.search(self.new_turn_pattern, sentence['text'])
            text = new_turn_search.group(2) if new_turn_search else sentence['text']
            normalized_text = self._true_case(text)
            # Sentence block is start of new speaker turn, or turns is empty
            if new_turn_search or not turns:
                turn = {
                    'speaker': '',
                    'data': [
                        {
                            'start_time': sentence['start_time'],
                            'end_time': sentence['end_time'],
                            'text': normalized_text
                        }
                    ]
                }
                turns.append(turn)
            # Sentence block is part of recent speaker turn
            elif turns:
                turns[-1]['data'].append({
                    'start_time': sentence['start_time'],
                    'end_time': sentence['end_time'],
                    'text': normalized_text
                })

        return turns

    def transcribe(
        self,
        source_uri: Union[str, Path],
        raw_transcript_save_path: Union[str, Path],
        timestamped_speaker_turns_save_path: Union[str, Path],
        **kwargs
    ) -> SRModelOutputs:
        # Check paths
        raw_transcript_save_path = Path(raw_transcript_save_path).resolve()
        timestamped_speaker_turns_save_path = Path(timestamped_speaker_turns_save_path).resolve()

        # Create timestamped speaker turns transcript
        timestamped_speaker_turns = self._get_speaker_turns(source_uri)

        # Create raw transcript
        raw_text = ' '.join([sentence['text'] for turn in timestamped_speaker_turns for sentence in turn['data']])
        raw_transcript = [{'start_time': timestamped_speaker_turns[0]['data'][0]['start_time'],
                           'end_time': timestamped_speaker_turns[-1]['data'][-1]['end_time'],
                           'text': raw_text}]

        # Wrap each transcript in the standard format
        raw_transcript = self.wrap_and_format_transcript_data(
            data=raw_transcript,
            transcript_format=constants.TranscriptFormats.raw,
            confidence=1
        )

        timestamped_speaker_turns = self.wrap_and_format_transcript_data(
            data=timestamped_speaker_turns,
            transcript_format=constants.TranscriptFormats.timestamped_speaker_turns,
            confidence=1
        )

        # Write files
        with open(raw_transcript_save_path, "w") as write_out:
            json.dump(raw_transcript, write_out)

        with open(timestamped_speaker_turns_save_path, "w") as write_out:
            json.dump(timestamped_speaker_turns, write_out)

        # Return the save path
        return SRModelOutputs(
            raw_transcript_save_path,
            1,
            timestamped_speaker_turns_path=timestamped_speaker_turns_save_path
        )
