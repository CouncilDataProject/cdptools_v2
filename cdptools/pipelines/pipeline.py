#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from abc import ABC, abstractmethod
from typing import Dict

###############################################################################

log = logging.getLogger(__name__)

###############################################################################


class Pipeline(ABC):

    @abstractmethod
    def run(self):
        """
        Run the pipeline.
        """
        pass


class ValuesForTerm:
    """
    Used for multithreaded uploaded of index terms.
    Can't use NamedTuple here because dictionaries are mutuable.
    """

    def __init__(self, term: str, values: Dict[str, float]):
        self.term = term
        self.values = values
