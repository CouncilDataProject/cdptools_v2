#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cdptools import CDPInstance, configs, databases, file_stores


def test_seattle():
    # Assert basic objects are constructed properly
    seattle = CDPInstance(configs.SEATTLE)
    assert isinstance(
        seattle.database, databases.cloud_firestore_database.CloudFirestoreDatabase
    )
    assert isinstance(seattle.file_store, file_stores.gcs_file_store.GCSFileStore)
