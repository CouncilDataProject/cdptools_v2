#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import logging
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union

import requests

###############################################################################

log = logging.getLogger(__name__)

###############################################################################


class FileStore(ABC):

    @staticmethod
    def compute_sha256_for_file(filepath: Union[str, Path], block_size: int = 1024 * 1024) -> Path:
        """
        Compute a SHA256 hexdigest for a file. Works for large files.

        Parameters
        ----------
        filepath: Union[str, Path]
            The path to the file to compute a SHA256 hexdigest for.
        block_size: int
            How many bytes to read at a time to add to the hashing algorithm.

        Returns
        -------
        digest: str
            The result of completing the SHA256 hash and taking the hexdigest.
        """
        # Resolve filepath
        filepath = Path(filepath).resolve(strict=True)
        if not filepath.is_file():
            raise IsADirectoryError(filepath)

        # Compute the md5
        func = hashlib.sha256()
        pos = 0

        # Open the file and compute md5 in chunks
        with open(filepath, mode="rb") as f:
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
        """
        Check to make sure that a path provided is on the local machine. Simply checks for common external uri headers.

        Parameters
        ----------
        path: Union[str, Path]
            The filepath to check for local existance.

        Returns
        -------
        is_local: bool
            A boolean value informing whether or not the provided path is a local resource or not.
        """
        # Convert path
        path = str(path)

        # Check for external headers
        external_headers = ["http://", "https://", "gc://", "s3://"]
        return not any(path.startswith(h) for h in external_headers)

    @staticmethod
    def _external_resource_copy(uri: str, dst: Optional[Union[str, Path]] = None, overwrite: bool = False) -> Path:
        """
        Copy an external resource to a local destination on the machine.

        Parameters
        ----------
        uri: str
            The uri for the external resource to copy.
        dst: Optional[Union[str, Path]]
            A specific destination to where the copy should be placed. If None provided stores the resource in the
            current working directory.
        overwrite: bool
            Boolean value indicating whether or not to overwrite a local resource with the same name if it already
            exists.

        Returns
        -------
        saved_path: Path
            The path of where the resource ended up getting copied to.
        """
        if dst is None:
            dst = uri.split("/")[-1]

        # Ensure dst doesn't exist
        dst = Path(dst).resolve()
        if dst.is_dir():
            dst = dst / uri.split("/")[-1]
        if dst.is_file() and not overwrite:
            raise FileExistsError(dst)

        # Open requests connection to uri as a stream
        log.debug(f"Beginning external resource copy from: {uri}")
        with requests.get(uri, stream=True) as streamed_read:
            streamed_read.raise_for_status()
            with open(dst, "wb") as streamed_write:
                shutil.copyfileobj(streamed_read.raw, streamed_write)
        log.debug(f"Completed external resource copy from: {uri}")
        log.info(f"Stored external resource copy: {dst}")

        return dst

    @abstractmethod
    def get_file_uri(self, filename: str, **kwargs) -> str:
        """
        Get a file path/ uri given a filename.

        Parameters
        ----------
        filename: str
            The file you are requesting a file uri for.

        Returns
        -------
        uri: str
            If the file is found, the file uri is returned as a string. If it isn't a FileNotFoundError is raised.
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

        Parameters
        ----------
        filepath: Union[str, Path]
            The filepath to the file you want to store.
        save_name: Optional[str]
            An optional save name to store the file as instead of it's current name.
        remove: bool
            Boolean value indicating whether or not to remove the local file after storage in the file store.

        Returns
        -------
        uri: str
            The uri for the stored file.
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

        Parameters
        ----------
        filename: str
            The name of the file in the file store that you want to download.
        save_path: Optional[Union[str, Path]] = None
            An optional save path / destination to store the file locally.
        overwrite: bool
            Boolean value indicating whether or not to overwrite a file that already exists in the destination.

        Returns
        -------
        save_path: Path
            The local path of the downloaded file.
        """

        return Path("/tmp/file.tmp")
