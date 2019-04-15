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

    def __init__(self, credentials_path: Union[str, Path], bucket_uri: str, **kwargs):
        # Resolve credentials
        self.credentials_path = Path(credentials_path).resolve(strict=True)

        # Initialize client
        self.client = storage.Client.from_service_account_json(self.credentials_path)
        self.bucket = self.client.get_bucket(bucket_uri)

    def store_file(
        self,
        filepath: Union[str, Path],
        save_name: Optional[str] = None,
        content_type: Optional[str] = None,
        remove: bool = False
    ) -> str:
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

    def get_file(self, filename: Union[str, Path]) -> str:
        # Resolve path
        filename = Path(filename).resolve().name

        # Create blob
        blob = self.bucket.blob(filename)

        # Check if file exists
        if blob.exists():
            return blob.path
        else:
            raise FileNotFoundError(filename)
