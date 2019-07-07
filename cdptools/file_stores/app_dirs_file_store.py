#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import shutil
from pathlib import Path
from typing import Optional, Union

import appdirs

from .file_store import FileStore

###############################################################################

log = logging.getLogger(__name__)

###############################################################################


class AppDirsFileStore(FileStore):

    def __init__(self, name: str = "cdp_filestore", owner: str = "cdp", **kwargs):
        # Initialize app dir if not already made
        self._root = Path(appdirs.user_data_dir(name, owner))

    def _locate_file(self, filename: Union[str, Path]) -> Path:
        log.debug(f"Locating file: {filename}")
        # Generate key
        key = self.compute_sha256_for_file(filename)

        # Split key into pairs of two characters
        sub_dirs = [key[i:i+2] for i in range(0, len(key), 2)]

        # Construct path parent
        path_parent = self._root
        for sub_dir in sub_dirs:
            path_parent /= sub_dir

        # Return with file name attached
        return path_parent / filename

    def get_file_uri(self, filename: Union[str, Path], **kwargs) -> str:
        # Resolve path
        filename = Path(filename).resolve()

        # Get path
        path = self._locate_file(filename.name)

        # Check exists
        path = path.resolve(strict=True)

        return str(path)

    def upload_file(
        self,
        filepath: Union[str, Path],
        save_name: Optional[str] = None,
        remove: bool = False,
        **kwargs
    ) -> str:
        # Resolve the path to enforce path complete
        filepath = Path(filepath).resolve(strict=True)

        # Create save name if none provided
        if save_name is None:
            save_name = filepath.name

        # Try to get the file first
        try:
            uri = self.get_file_uri(filename=save_name)

            # Check remove before returning
            if remove:
                os.remove(filepath)

            return uri
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
        log.info(f"Completed file copy for: {filepath}")
        log.debug(f"Stored copy at: {save_path}")

        # Remove if desired
        if remove:
            os.remove(filepath)

        # Return path after copy
        return str(save_path)

    def download_file(
        self,
        filename: str,
        save_path: Optional[Union[str, Path]] = None,
        overwrite: bool = False,
        **kwargs
    ) -> Path:
        # Fix name
        filename = Path(filename).resolve().name

        # Get file uri
        stored_uri = self.get_file_uri(filename)

        # No save path just return file
        if save_path is None:
            return stored_uri

        # Check save path
        save_path = Path(save_path).resolve()
        if save_path.is_file() and not overwrite:
            raise FileExistsError(save_path)

        # Copy file to save path
        log.debug(f"Beginning file copy for: {filename}")
        saved_path = Path(shutil.copyfile(stored_uri, save_path))
        log.debug(f"Completed file copy for: {filename}")
        return saved_path

    def __str__(self):
        return f"<AppDirsFileStore [{self._root}]>"

    def __repr__(self):
        return str(self)
