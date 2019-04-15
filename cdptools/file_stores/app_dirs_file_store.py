#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import logging
import os
from pathlib import Path
import shutil
from typing import Optional, Union

import appdirs
from .file_store import FileStore

###############################################################################

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)4s: %(module)s:%(lineno)4s %(asctime)s] %(message)s'
)
log = logging.getLogger(__file__)

###############################################################################


class AppDirsFileStore(FileStore):

    def __init__(self, name: str = "cdp_filestore", owner: str = "cdp", **kwargs):
        # Initialize app dir if not already made
        self.root = Path(appdirs.user_data_dir(name, owner))

    def _locate_file(self, filename: Union[str, Path]) -> Path:
        log.debug(f"Locating file: {filename}")
        # Generate key
        key = hashlib.sha256(str(filename).encode("utf8")).hexdigest()

        # Split key into pairs of two characters
        sub_dirs = [key[i:i+2] for i in range(0, len(key), 2)]

        # Construct path parent
        path_parent = self.root
        for sub_dir in sub_dirs:
            path_parent /= sub_dir

        # Return with file name attached
        return path_parent / filename

    def store_file(self, filepath: Union[str, Path], save_name: Optional[str] = None, remove: bool = False) -> Path:
        # Resolve the path to enforce path complete
        filepath = Path(filepath).resolve(strict=True)

        # Create save name if none provided
        if not save_name:
            save_name = filepath.name

        # Try to get the file first
        try:
            return self.get_file(filename=save_name)
        except FileNotFoundError:
            pass

        # Check if resource is internal
        if not self._path_is_local(filepath):
            raise FileNotFoundError(filepath)

        # Generate save path
        save_path = self._locate_file(save_name)

        # Create save_dir if not already exists
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Actual copy operation
        log.debug(f"Beginning file copy for: {filepath}")
        save_path = shutil.copyfile(filepath, save_path)
        log.debug(f"Completed file copy for: {filepath}")
        log.debug(f"Stored copy at: {save_path}")

        # Remove if desired
        if remove:
            os.remove(filepath)

        # Return path after copy
        return save_path

    def get_file(self, filename: Union[str, Path]) -> Path:
        # Resolve path
        filename = Path(filename).resolve()

        # Get path
        path = self._locate_file(filename.name)

        # Check exists
        path = path.resolve(strict=True)

        return path
