#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from typing import Dict, List

###############################################################################


class EventScraper(ABC):

    @abstractmethod
    def get_events(self) -> List[Dict]:
        """
        Return a list of dictionaries with each dictionary being event details.
        This is meant to be ran at least once a day so your scraper should handle out of time bounds errors.
        """
        return []
