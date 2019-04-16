#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from pathlib import Path
from typing import Optional, Union

from google.cloud import storage

from .file_store import FileStore

###############################################################################

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)4s: %(module)s:%(lineno)4s %(asctime)s] %(message)s'
)
log = logging.getLogger(__file__)

###############################################################################


class GCSFileStore(FileStore):

    def __init__(self, credentials_path: Union[str, Path], bucket_name: str, **kwargs):
        # Resolve credentials
        self.credentials_path = Path(credentials_path).resolve(strict=True)

        # Initialize client
        self.client = storage.Client.from_service_account_json(self.credentials_path)
        self.bucket = self.client.get_bucket(bucket_name)

    def get_file_uri(self, filename: Union[str, Path], **kwargs) -> str:
        # Resolve path
        filename = Path(filename).resolve().name

        # Create blob
        blob = self.bucket.blob(filename)

        # Check if file exists
        if blob.exists():
            return f"gs://{self.bucket.name}/{filename}"
        else:
            raise FileNotFoundError(filename)

    def upload_file(
        self,
        filepath: Union[str, Path],
        save_name: Optional[str] = None,
        content_type: Optional[str] = None,
        remove: bool = False,
        **kwargs,
    ) -> str:
        # Resolve the path to enforce path complete
        filepath = Path(filepath).resolve(strict=True)

        # Create save name if none provided
        if not save_name:
            save_name = filepath.name

        # Try to get the file first
        try:
            return self.get_file_uri(filename=save_name)
        except FileNotFoundError:
            pass

        # Check if resource is internal
        if not self._path_is_local(filepath):
            raise FileNotFoundError(filepath)

        # Save url is bucket name + save_name
        save_url = f"gs://{self.bucket.name}/{save_name}"

        # Actual copy operation
        log.debug(f"Beginning file copy for: {filepath}")
        blob = self.bucket.blob(save_name)
        blob.upload_from_filename(str(filepath), content_type=content_type)
        log.debug(f"Completed file copy for: {filepath}")
        log.info(f"Stored file: {save_url}")

        # Remove if desired
        if remove:
            os.remove(filepath)

        # Return path after copy
        return save_url

    def download_file(self, filename: str, save_path: Optional[Union[str, Path]] = None, **kwargs) -> Path:
        # Fix name
        filename = Path(filename).resolve()

        # Check for existance
        self.get_file_uri(filename.name)

        # No save path, set it to received filename
        if save_path is None:
            save_path = filename

        # Check save path
        save_path = Path(save_path).resolve()
        if save_path.is_file():
            raise FileExistsError(save_path)

        # Begin download
        log.debug(f"Beginning file download for: {filename}")
        blob = self.bucket.blob(filename.name)
        blob.download_to_filename(str(save_path))
        log.debug(f"Completed file download for: {filename}")

        return save_path
