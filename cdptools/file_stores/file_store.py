#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
import hashlib
import logging
from pathlib import Path
import shutil
from typing import Optional, Union

import requests

###############################################################################

log = logging.getLogger(__name__)

###############################################################################


class FileStore(ABC):

    @staticmethod
    def compute_sha256_for_file(filepath: Union[str, Path], block_size: int = 1024 * 1024) -> Path:
        # Resolve filepath
        filepath = Path(filepath).resolve(strict=True)
        if not filepath.is_file():
            raise IsADirectoryError(filepath)

        # Compute the md5
        func = hashlib.sha256()
        pos = 0

        # Open the file and compute md5 in chunks
        with open(filepath, mode='rb') as f:
            while True:
                f.seek(pos)
                chunk = f.read(block_size)
                if not chunk:
                    break
                func.update(chunk)
                pos += block_size

        return func.hexdigest()

    @staticmethod
    def _path_is_local(path: Union[str, Path]) -> bool:
        # Convert path
        path = str(path)

        # Check for external headers
        external_headers = ["http://", "https://", "gc://", "s3://"]
        return not any(path.startswith(h) for h in external_headers)

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
            streamed_read.raise_for_status()
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
