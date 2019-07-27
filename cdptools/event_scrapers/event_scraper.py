#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from typing import Any, Dict, List

###############################################################################


class EventScraper(ABC):

    @abstractmethod
    def get_events(self) -> List[Dict[str, Any]]:
        """
        Get a list of event details required to run the rest of an event pipeline.

        Many get events functions are meant to be run on a schedule so it may be best to consider implementing an
        OutOfTimeBoundsError somewhere during the processing to ignore events you believe should have already been
        retrieved during a prior run.

        Returns
        -------
        events: List[Dict[str, Any]]
            A list of dictionaries with each dictionary containing event details for the rest of an event pipeline to
            use for processing and storage information.
        """
        return []
