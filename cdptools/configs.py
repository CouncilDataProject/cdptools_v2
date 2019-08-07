#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .cdp_instance import CDPInstanceConfig

SEATTLE = CDPInstanceConfig(
    database_module_path="cdptools.databases.cloud_firestore_database",
    database_object_name="CloudFirestoreDatabase",
    database_object_kwargs={"project_id": "cdp-seattle"},
    file_store_module_path="cdptools.file_stores.gcs_file_store",
    file_store_object_name="GCSFileStore",
    file_store_object_kwargs={"bucket_name": "cdp-seattle.appspot.com"}
)
