#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from typing import Union


class UnrecognizedTranscriptFormatError(Exception):
    def __init__(self, path: Union[str, Path], **kwargs):
        super().__init__(**kwargs)
        self.path = path

    def __str__(self):
        return (
            f"Unsure how to handle annotated JSON transcript provided: {self.path} "
            f"Please refer to the 'Transcript Formats' section of project documentation for details."
        )
