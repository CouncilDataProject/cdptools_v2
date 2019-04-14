#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from pathlib import Path
import shutil
from typing import Optional, Union

import appdirs
import requests

from .file_store import FileStore

###############################################################################

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)4s: %(module)s:%(lineno)4s %(asctime)s] %(message)s'
)
log = logging.getLogger(__file__)

###############################################################################


class AppDirsFileStore(FileStore):

    def __init__(self, name: str = "cdp_filestore", owner: str = "cdp"):
        # Initialize app dir if not already made
        self.root = Path(appdirs.user_data_dir(name, owner))

    @staticmethod
    def _path_is_local(path: Union[str, Path]) -> bool:
        # Convert path
        path = str(path)

        # Start checks
        if "http://" in path:
            return False
        elif "https://" in path:
            return False
        elif "s3://" in path:
            return False
        else:
            return True

    @staticmethod
    def _external_resource_copy(url: str, dst: Union[str, Path]) -> Path:
        # Enforce dst does not exist
        dst = Path(dst).resolve()
        if dst.is_file():
            raise FileExistsError(dst)

        # Open requests connection to url as a stream
        with requests.get(url, stream=True) as streamed_read:
            # Open bytes writing file
            with open(dst, "wb") as write_out:
                shutil.copyfileobj(streamed_read.raw, write_out)

        return dst

    @staticmethod
    def _locate_file(root: Path, key: str, file_name: str) -> Path:
        # Split key into pairs of two characters
        sub_dirs = [key[i:i+2] for i in range(0, len(key), 2)]

        # Construct path parent
        path_parent = root
        for sub_dir in sub_dirs:
            path_parent /= sub_dir

        # Return with file name attached
        return path_parent / file_name

    def store_file(
        self,
        file: Union[str, Path],
        key: str,
        save_name: Optional[str] = None,
        remove: bool = False
    ) -> Path:
        # Try to get the file first
        try:
            return self.get_file(key=key, filename=save_name)
        except FileNotFoundError:
            pass

        # Check if resource is internal
        if self._path_is_local(file):
            # It is so resolve the path to enforce path complete.
            file = Path(file).resolve(strict=True)

            # Set the copy function to shutil copy
            copy_function = shutil.copyfile

            # Determine save name if none passed
            if not save_name:
                save_name = file.name
        else:
            # Set the copy function external copy
            copy_function = self._external_resource_copy

            # Ignore any remove because we can't remove an external resource
            remove = False

            # Determine save name if none passed
            if not save_name:
                save_name = file.split("/")[-1]

        # Generate save path
        save_path = self._locate_file(self.root, key, save_name)

        # Check if file already exists
        if save_path.is_file():
            raise FileExistsError(save_path)

        # Create save_dir if not already exists
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Actual copy operation
        log.debug(f"Beginning file copy for: {file}")
        save_path = copy_function(file, save_path)
        log.debug(f"Completed file copy for: {file}")
        log.debug(f"Stored copy at: {save_path}")

        # Remove if desired
        if remove:
            os.remove(file)

        # Return path after copy
        return save_path

    def get_file(self, key: str, filename: str) -> Path:
        # Get path
        path = self._locate_file(self.root, key, filename)

        # Check exists
        path = path.resolve(strict=True)

        return path
