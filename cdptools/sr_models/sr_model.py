#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

###############################################################################


class SRModel(ABC):

    @abstractmethod
    def transcribe(self, audio_read_path: Union[str, Path], transcript_save_path: Union[str, Path]) -> Path:
        """
        Transcribe audio from file and store in text file.
        """

        return Path("/root/.local/path/to/file/id.txt")
