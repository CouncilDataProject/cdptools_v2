#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

###############################################################################


class FileStore(ABC):

    @abstractmethod
    def store_file(self, file: Union[str, Path]) -> str:
        """
        Store a file.
        """

        return ""

    @abstractmethod
    def get_file(self, file_id: str) -> Path:
        """
        Get a file by id.
        """
        return Path("/root/.local/path/to/file/id.mp4")
