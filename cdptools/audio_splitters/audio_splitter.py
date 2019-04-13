#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

###############################################################################


class AudioSplitter(ABC):

    @abstractmethod
    def split(self, video_read_path: Union[str, Path], audio_save_path: Union[str, Path]) -> Path:
        """
        Split and store the audio from a video file.
        """

        return Path("/root/.local/path/to/file/id.wav")
