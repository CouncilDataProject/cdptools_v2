#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cdptools import cdp_instances, databases, file_stores


def test_seattle():
    # Assert basic objects are constructed properly
    assert isinstance(cdp_instances.seattle.database, databases.CloudFirestoreDatabase)
    assert isinstance(cdp_instances.seattle.file_store, file_stores.GCSFileStore)
