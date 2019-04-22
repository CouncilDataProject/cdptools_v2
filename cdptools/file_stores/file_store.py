#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
import logging
from pathlib import Path
import shutil
from typing import Optional, Union

import requests

###############################################################################

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)4s: %(module)s:%(lineno)4s %(asctime)s] %(message)s'
)
log = logging.getLogger(__file__)

###############################################################################


class FileStore(ABC):

    @staticmethod
    def _path_is_local(path: Union[str, Path]) -> bool:
        # Convert path
        path = str(path)

        # Start checks
        if path.startswith("http://"):
            return False
        elif path.startswith("https://"):
            return False
        else:
            return True

    @staticmethod
    def _external_resource_copy(url: str, dst: Optional[Union[str, Path]] = None, overwrite: bool = False) -> Path:
        if dst is None:
            dst = url.split("/")[-1]

        # Ensure dst doesn't exist
        dst = Path(dst).resolve()
        if dst.is_file() and not overwrite:
            raise FileExistsError(dst)

        # Open requests connection to url as a stream
        log.debug(f"Beginning external resource copy from: {url}")
        with requests.get(url, stream=True) as streamed_read:
            with open(dst, "wb") as streamed_write:
                shutil.copyfileobj(streamed_read.raw, streamed_write)
        log.debug(f"Completed external resource copy from: {url}")
        log.info(f"Stored external resource copy: {dst}")

        return dst

    @abstractmethod
    def get_file_uri(self, filename: str, **kwargs) -> str:
        """
        Get a file path/ uri.
        """

        return ""

    @abstractmethod
    def upload_file(
        self,
        filepath: Union[str, Path],
        save_name: Optional[str] = None,
        remove: bool = False,
        **kwargs
    ) -> str:
        """
        Store a file.
        """

        return ""

    @abstractmethod
    def download_file(
        self,
        filename: str,
        save_path: Optional[Union[str, Path]] = None,
        overwrite: bool = False,
        **kwargs
    ) -> Path:
        """
        Download the file if neccessary and return the Path.
        """

        return Path("/tmp/file.tmp")
