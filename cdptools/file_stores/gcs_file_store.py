#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from pathlib import Path
from typing import List, Optional, Union

import requests
from google.cloud import storage
from google.api_core.page_iterator import Page

from concurrent.futures import ThreadPoolExecutor

from . import exceptions
from .file_store import FileStore

###############################################################################

log = logging.getLogger(__name__)

GCS_URI = "https://storage.googleapis.com/{bucket}/{filename}"

SUFFIX_CONTENT_TYPE_MAP = {
    ".wav": "audio/wav",
    ".txt": "text/plain",
    ".err": "text/plain",
    ".out": "text/plain",
    ".mp4": "video/mp4",
}

###############################################################################


class GCSFileStore(FileStore):
    def _initialize_creds_fs(
        self, bucket_name: str, credentials_path: Union[str, Path]
    ):
        # Resolve credentials
        self._credentials_path = Path(credentials_path).resolve(strict=True)

        # Initialize client
        self._client = storage.Client.from_service_account_json(self._credentials_path)
        self._bucket = self._client.get_bucket(bucket_name)

    def __init__(
        self,
        bucket_name: str,
        credentials_path: Optional[Union[str, Path]] = None,
        **kwargs,
    ):
        # With credentials:
        if credentials_path:
            self._initialize_creds_fs(bucket_name, credentials_path)
        else:
            self._credentials_path = None
            self._bucket = bucket_name

    def _get_file_uri_with_creds(self, filename: Union[str, Path]) -> str:
        # Resolve path
        filename = Path(filename).resolve().name

        # Create blob
        blob = self._bucket.blob(filename)

        # Check if file exists
        if blob.exists():
            return f"gs://{self._bucket.name}/{filename}"
        else:
            raise FileNotFoundError(filename)

    def _get_file_uri_no_creds(self, filename: Union[str, Path]) -> str:
        # Resolve path
        filename = Path(filename).resolve().name

        # Open request
        uri = GCS_URI.format(bucket=self._bucket, filename=filename)
        with requests.get(uri, stream=True) as response:
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                raise FileNotFoundError(filename)

            # Existed
            return uri

    def get_file_uri(self, filename: Union[str, Path], **kwargs) -> str:
        # With credentials
        if self._credentials_path:
            return self._get_file_uri_with_creds(filename)

        return self._get_file_uri_no_creds(filename)

    def upload_file(
        self,
        filepath: Union[str, Path],
        save_name: Optional[str] = None,
        content_type: Optional[str] = None,
        remove: bool = False,
        **kwargs,
    ) -> str:
        # Reject any upload without credentials
        if self._credentials_path is None:
            raise exceptions.MissingCredentialsError()

        # Resolve the path to enforce path complete
        filepath = Path(filepath).resolve(strict=True)

        # Create save name if none provided
        if not save_name:
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

        # Save url is bucket name + save_name
        save_url = f"gs://{self._bucket.name}/{save_name}"

        # Match content type
        if content_type is None:
            if filepath.suffix in SUFFIX_CONTENT_TYPE_MAP:
                content_type = SUFFIX_CONTENT_TYPE_MAP[filepath.suffix]

        # Actual copy operation
        log.debug(f"Beginning file copy for: {filepath}")
        blob = self._bucket.blob(save_name)
        blob.upload_from_filename(str(filepath), content_type=content_type)
        log.debug(f"Completed file copy for: {filepath}")
        log.info(f"Stored file: {save_url}")

        # Remove if desired
        if remove:
            os.remove(filepath)

        # Return path after copy
        return save_url

    def _download_file_with_creds(
        self,
        filename: str,
        save_path: Optional[Union[str, Path]] = None,
        overwrite: bool = False,
    ) -> Path:
        # Check for existance
        self.get_file_uri(filename)

        # No save path, set it to received filename
        if save_path is None:
            save_path = filename

        # Resolve save path
        save_path = Path(save_path).expanduser().resolve()

        # If the save path is a directory, attach the filename to the path
        if save_path.is_dir():
            save_path = save_path / filename

        # Check save path
        if save_path.is_file() and not overwrite:
            raise FileExistsError(save_path)

        # Begin download
        log.debug(f"Beginning file download for: {filename}")
        blob = self._bucket.blob(filename)
        blob.download_to_filename(str(save_path))
        log.debug(f"Completed file download for: {filename}")

        return save_path

    def _download_file_no_creds(
        self,
        filename: str,
        save_path: Optional[Union[str, Path]] = None,
        overwrite: bool = False,
    ) -> Path:
        # Resolve path
        filename = Path(filename).resolve().name

        # Format request
        uri = GCS_URI.format(bucket=self._bucket, filename=filename)
        return self._external_resource_copy(uri, save_path, overwrite)

    def download_file(
        self,
        filename: str,
        save_path: Optional[Union[str, Path]] = None,
        overwrite: bool = False,
        **kwargs,
    ) -> Path:
        # With credentials
        if self._credentials_path:
            return self._download_file_with_creds(filename, save_path, overwrite)

        return self._download_file_no_creds(filename, save_path, overwrite)

    def delete_file(self, filename: str) -> str:
        self._bucket.delete_blob(filename)
        return f"Deleted file: {filename}"

    def delete_page(self, page: Page) -> str:
        for blob in page:
            self.delete_file(blob.name)
        return f"Deleted page in bucket: {self._bucket.name}"

    def clear_bucket(self) -> str:
        # Gather the files by pages so we can delete in parallel
        pages = self._client.list_blobs(self._bucket).pages

        with ThreadPoolExecutor() as exe:
            exe.map(self.delete_page, pages)

        log.info(f"Cleared bucket: {self._bucket.name}")
        return f"Cleared bucket: {self._bucket.name}"

    def list_page(self, page: Page) -> List[str]:
        file_list = []
        for blob in page:
            file_list.append(blob.name)

        return file_list

    def list_all_files(self) -> List[str]:
        # Gather the files by pages
        pages = self._client.list_blobs(self._bucket).pages

        full_list = []
        with ThreadPoolExecutor() as exe:
            # Add list of file from each page to full list
            for page in pages:
                future = exe.submit(self.list_page, page)
                sub_list = future.result()
                full_list += sub_list

        return full_list

    def __str__(self):
        # With credentials
        if self._credentials_path:
            return f"<GCSFileStore [{self._bucket.name}]>"

        return f"<GCSFileStore [{self._bucket}]>"

    def __repr__(self):
        return str(self)
