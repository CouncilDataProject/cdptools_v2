#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from typing import Optional

from ..databases.database import Database

###############################################################################

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)4s: %(module)s:%(lineno)4s %(asctime)s] %(message)s'
)
log = logging.getLogger(__file__)

###############################################################################


class RunManager(object):

    def __init__(
        self,
        database_module: Database,
        algorithm_name: str,
        algorithm_version: str,
        algorithm_description: Optional[str] = None,
        source: Optional[str] = None
    ):
        # Save db reference
        self._db = database_module

        # Get or upload algorithm details
        self._algorithm_details = self._db.get_or_upload_algorithm(
            name=algorithm_name,
            version=algorithm_version,
            description=algorithm_description,
            source=source
        )
