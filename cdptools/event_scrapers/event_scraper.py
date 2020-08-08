#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from cdptools.databases.doctypes.event import Event

###############################################################################


class EventScraper(ABC):
    @abstractmethod
    def get_events(self) -> List[Event]:
        """
        Get a list of event details required to run the rest of an event pipeline.

        Many get events functions are meant to be run on a schedule so it may be best
        to consider implementing an OutOfTimeBoundsError somewhere during the
        processing to ignore events you believe should have already been retrieved
        during a prior run.

        Returns
        -------
        events: List[Event]
            A list of Events containing event details for the rest of
            an event pipeline to use for processing and storage information.
        """
        return []

    @abstractmethod
    def get_single_event(self, uri: str, backfill: bool = False) -> Event:
        """
        Get event details for a single event required to run the rest of an event
        pipeline.

        This can be used for processing single events that might not have been properly
        processed with the above get_events method when running a EventGatherPipeline.

        Returns
        -------
        event: Event
            An Event containing event details for the rest of an event pipeline to
            use for processing and storage info.
        """
        return Event.from_dict({})
