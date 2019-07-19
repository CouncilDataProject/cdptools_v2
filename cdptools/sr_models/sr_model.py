#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Union

from . import constants

###############################################################################


class SRModelOutputs(NamedTuple):
    raw_path: Path
    confidence: float
    timestamped_words_path: Optional[Path] = None
    timestamped_sentences_path: Optional[Path] = None
    extras: Optional[Dict[str, Any]] = None


class SRModel(ABC):

    @staticmethod
    def wrap_and_format_transcript_data(
        data: constants.TranscriptDataJSON,
        transcript_format: str,
        confidence: float,
        annotations: List[Dict[str, Any]] = []
    ) -> Dict[str, Union[str, constants.TranscriptDataJSON]]:
        return {
            "format": transcript_format,
            "annotations": annotations,
            "confidence": confidence,
            "data": data
        }

    @abstractmethod
    def transcribe(
        self,
        audio_uri: Union[str, Path],
        raw_transcript_save_path: Union[str, Path],
        timestamped_words_save_path: Optional[Union[str, Path]] = None,
        timestamped_sentences_save_path: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> SRModelOutputs:
        """
        Transcribe audio from file and store in text file.
        """

        return SRModelOutputs(
            Path(raw_transcript_save_path),
            1.0,
            Path(timestamped_words_save_path),
            Path(timestamped_sentences_save_path)
        )
