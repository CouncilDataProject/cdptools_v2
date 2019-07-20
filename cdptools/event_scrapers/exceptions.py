#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime


class EventParseError(Exception):
    def __init__(self, body: str, dt: datetime, **kwargs):
        super().__init__(**kwargs)
        self.body = body
        self.dt = dt

    def __str__(self):
        return f"Could not parse event for: {self.body} {self.dt}"


class LegistarLookupError(Exception):
    def __init__(self, body: str, dt: datetime, **kwargs):
        super().__init__(**kwargs)
        self.body = body
        self.dt = dt

    def __str__(self):
        return f"Could not find Legistar event for: {self.body} {self.dt}"


class EventOutOfTimeboundsError(Exception):
    def __init__(self, current: datetime, begin: datetime, end: datetime, **kwargs):
        super().__init__(**kwargs)
        self.current = current
        self.begin = begin
        self.end = end

    def __str__(self):
        return f"Event is out of expected time bounds. Received: {self.current} Bounds: {self.begin} - {self.end}"
