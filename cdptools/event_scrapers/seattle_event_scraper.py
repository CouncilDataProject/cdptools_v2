#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from functools import partial
from typing import Any, Dict, List, Optional, Union

import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import process

from ..legistar_utils import events as legistar_event_tools
from . import exceptions
from .event_scraper import EventScraper

###############################################################################

log = logging.getLogger(__name__)

###############################################################################


class ParsedEvents(object):

    def __init__(
        self,
        success: List[Dict] = None,
        warning: List[exceptions.EventOutOfTimeboundsError] = None,
        error: List[Union[exceptions.EventParseError, exceptions.LegistarLookupError]] = None
    ):
        self.success = success if success else []
        self.warning = warning if warning else []
        self.error = error if error else []


class SeattleEventScraper(EventScraper):

    @staticmethod
    def pstnow():
        return datetime.utcnow() - timedelta(hours=7)

    def __init__(
        self,
        main_route: str = "http://www.seattlechannel.org/CityCouncil",
        backfill: bool = False,
        ignore_minutes_items: List[str] = [],
        legistar_client: str = "seattle",
        max_concurrent_requests: int = None,
        **kwargs
    ):
        # Store configuration
        self.main_route = main_route
        self.backfill = backfill
        self.legistar_client = legistar_client
        self.ignore_minutes_items = ignore_minutes_items
        if max_concurrent_requests:
            self.max_concurrent_requests = max_concurrent_requests
        else:
            self.max_concurrent_requests = os.cpu_count() * 5

    @staticmethod
    def _resolve_route(complete_sibling: str, route: str) -> str:
        """
        Resolve a url route.

        Parameters
        ----------
        complete_sibling: str
            A completed sibling route that can be used to find mutual parents or other contextual information.
        route: str
            The route to resolve.

        Returns
        -------
        resolved_route: str
            If "http" or "https" is found in the route it is assumed the route is already complete.
            If not, the sibling is split, tail removed, and the route is attached.
            Returned is the parent sibling joined with the provided route as a child.
        """
        # Check if route is already resolved
        if "http://" in route or "https://" in route:
            return route
        else:
            # Remove trailing and beginning '/' from parent and route
            if complete_sibling[-1] == "/":
                complete_sibling = complete_sibling[:-1]
            if route[0] == "/":
                route = route[1:]

            # Split sibling into its parts
            sibling_parts = complete_sibling.split("/")

            # Join back all except last to create the relative path
            parent = "/".join(sibling_parts[:-1])

            # Expand route
            return f"{parent}/{route}"

    def get_routes(self) -> List[str]:
        # Get page
        response = requests.get(self.main_route)

        # Check status
        response.raise_for_status()

        # Convert to soup
        soup = BeautifulSoup(response.content, "html.parser")

        # Find all routes
        content = soup.find("div", id="mainContent")
        routes = []
        for item in content.findAll("li"):
            link = item.find("a")
            if link:
                routes.append(link.get("href"))

        # Expand relative routes
        routes = [self._resolve_route(self.main_route, route) for route in routes]

        return routes

    @staticmethod
    def _clean_string(s: str) -> str:
        """
        Simply remove any leading and trailing spaces and punctuation.

        Parameters
        ----------
        s: str
            The string to be cleaned.

        Returns
        -------
        cleaned: str
            The cleaned string that has had leading and trailing spaces and punctuation removed.
        """
        # Basic cleaning
        s = s.replace("\n", "")
        s = s.replace("\t", "")
        s = s.replace("\xa0", "")

        # Removing leading
        if s[0] == " ":
            s = s[1:]
        # Removing trailing
        if s[-1] == " ":
            s = s[:-1]
        # Removing trailing "."
        if s[-1] == ".":
            s = s[:-1]

        return s

    @staticmethod
    def _parse_seattle_channel_event(
        event_container: BeautifulSoup,
        complete_sibling: str,
        ignore_date: bool = False
    ) -> Dict[str, Any]:
        """
        Parse a single event from the html of a Seattle Channel event block.

        Parameters
        ----------
        event_container: BeautifulSoup
            A BeautifulSoup object created from reading a single event div block from SeattleChannel.
        complete_sibling: str
            A complete sibling to the current event containers host page.
        ignore_date: bool
            A boolean information whether or not to ignore the parsed event based of the parsed date.

        Returns
        -------
        event_details: Dict[str, Any]
            The fully parsed event details.
        """
        # Find event details
        event_details = event_container.find("div", class_="col-xs-12 col-sm-8 col-md-9")

        # Find and clean body name
        body = event_details.find("h2").text.replace("\n", "")
        body = body.replace(" - Special Meeting", "")
        body = body.replace(" Special Meeting - Public Hearing", "")
        body_includes_date = re.search(r"[0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4}$", body)
        if body_includes_date:
            body = body.replace(f" {body_includes_date.group(0)}", "")

        # Find and clean date
        date = event_details.find("div", class_="videoDate").text
        month, day, year = tuple(date.split("/"))
        event_dt = datetime(int(year), int(month), int(day))

        # Agendas have mixed formatting
        try:
            agenda = event_details.find("div", class_="titleExcerptText").find("p").text
        except AttributeError:
            try:
                agenda = event_details.find("div", class_="titleExcerptText").text
            except AttributeError:
                raise exceptions.EventParseError(body, event_dt)

        # The agenda is returned as a single string
        # Clean it and split it into its parts
        agenda = agenda.replace("Agenda:", "")
        agenda = agenda.replace("Agenda Items:", "")

        # Older agendas used commas instead of semicolons
        if ";" in agenda:
            agenda = agenda.split(";")
        else:
            agenda = agenda.split(",")

        # Find video and thumbnail urls
        video_and_thumbnail = event_container.find("div", class_="col-xs-12 col-sm-4 col-md-3")
        video = video_and_thumbnail.find("a").get("onclick")
        seattle_channel_page = video_and_thumbnail.find("a").get("href")

        # Onclick returns a javascript function
        # Try to find the url the function redirects to
        try:
            # All seattle channel videos are hosted at "video.seattle.gov/..."
            # This will find the true url by searching for a substring that matches the above pattern
            # Note: some of the urls have spaces in the video filename which is why the space is included in the
            # regex search pattern.
            video = re.search(r"video\.seattle\.gov[a-zA-Z0-9\/_ ]*\.(mp4|flv)", video).group(0)
            video = f"https://{video}"
        except AttributeError:
            raise exceptions.EventParseError(body, event_dt)

        # If the event was not today, ignore it.
        if not ignore_date:
            now = SeattleEventScraper.pstnow()
            yesterday = now - timedelta(days=1)
            if not (event_dt > yesterday and event_dt < now):
                raise exceptions.EventOutOfTimeboundsError(event_dt, yesterday, now)

        # Construct event
        event = {
            "minutes_items": [SeattleEventScraper._clean_string(item) for item in agenda],
            "body": SeattleEventScraper._clean_string(body),
            "event_datetime": event_dt,
            "source_uri": SeattleEventScraper._resolve_route(complete_sibling, seattle_channel_page),
            "video_uri": video.replace(" ", "")
        }
        return event

    def _collect_sub_route_events(self, url: str) -> List[Dict]:
        # Get page
        response = requests.get(url)

        # Check status
        response.raise_for_status()

        # Convert to soup
        soup = BeautifulSoup(response.content, "html.parser")

        # Find all event containers
        event_containers = soup.find_all("div", class_="row borderBottomNone paginationItem")

        # Process each event
        events = ParsedEvents()
        for container in event_containers:
            try:
                # Parse event details from html
                event = self._parse_seattle_channel_event(container, self.main_route, self.backfill)

                # Successful parse
                events.success.append(event)

            except (exceptions.EventOutOfTimeboundsError) as e:
                # For logging purposes, return the errors
                events.warning.append((container, e))

            except exceptions.EventParseError as e:
                # For logging purposes, return the errors
                events.error.append((container, e))

        # Return processed events
        log.debug(
            f"Collected {len(events.success)}. "
            f"Warnings: {len(events.warning)}. "
            f"Errors: {len(events.error)}. "
            f"from sub-route: {url}"
        )
        return events

    @staticmethod
    def _attach_legistar_details_to_event(
        event: Dict[str, Any],
        ignore_minutes_items: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Query for and attach the best matching legistar event information to the provided event details.

        Parameters
        ----------
        event: Dict[str, Any]
            The parsed event details from the SeattleChannel website.
        ignore_minutes_items: Optional[List[str]]
            A list of minute item names to ignore when parsing the minutes items from legistar.
            Useful for minute items that are so commonly used they lack specific value.

        Returns
        -------
        joined: Dict[str, Any]
            The base event details object combined with the found legistar data.
        """
        # Get all legistar events surrounding the provided event date
        legistar_events = legistar_event_tools.get_legistar_events_for_timespan(
            "seattle",
            event["event_datetime"],
            event["event_datetime"] + timedelta(days=1)
        )
        log.debug("Pulled legistar details for event: {}".format(event["source_uri"]))

        # Fast return for only one event returned
        if len(legistar_events) == 1:
            selected_event = legistar_events[0]
        else:
            # Reduce events to not include cancelled events
            cancelled_reduced = [e for e in legistar_events if e["EventAgendaStatusName"] != "Cancelled"]

            # Get body names
            available_bodies = set([e["EventBodyName"] for e in cancelled_reduced])

            # Check if the Seattle Channel body name (basically a "display name") is present in the list
            # If so, choose the events with that exact body name
            if event["body"] in available_bodies:
                legistar_events = [e for e in cancelled_reduced if e["EventBodyName"] == event["body"]]
            # No exact match available, find the closest body name by text diff
            else:
                # Returns the closest name and the score that made it the closest
                closest_body_name, score = process.extractOne(event["body"], available_bodies)

                # For reasons somewhat unknown to me, SeattleChannel has videos for events that don't exist in legistar
                # We can somewhat detect this by filtering out body names that are drastically different
                # In the case that the closest body name is less than a 50% match, return None to be cleaned up after
                # The body names shouldn't be _that_ different which is why we are just ignoring for now
                if score < 50:
                    return None

                # Otherwise, use the found body name
                legistar_events = [e for e in cancelled_reduced if e["EventBodyName"] == closest_body_name]

            # Run agenda matching against the events
            agenda_match_details = legistar_event_tools.get_matching_legistar_event_by_minutes_match(
                event["minutes_items"],
                legistar_events
            )

            # Add the details
            selected_event = agenda_match_details.selected_event

        # Parse details
        if ignore_minutes_items is None:
            ignore_minutes_items = []
        parsed_details = legistar_event_tools.parse_legistar_event_details(selected_event, ignore_minutes_items)

        # Format the event details
        formatted_event_details = {
            **parsed_details,
            "source_uri": event["source_uri"],
            "video_uri": event["video_uri"]
        }
        log.debug("Attached legistar event details for event: {}".format(formatted_event_details["source_uri"]))
        return formatted_event_details

    def get_events(self) -> List[Dict]:
        # Complete seattle channel event collection in threadpool
        with ThreadPoolExecutor(min(self.max_concurrent_requests, os.cpu_count() * 5)) as exe:
            seattle_channel_results = list(exe.map(self._collect_sub_route_events, self.get_routes()))

        # Join body events to single object
        success = []
        warning = []
        error = []
        for body_result in seattle_channel_results:
            success += body_result.success
            warning += body_result.warning
            error += body_result.error
        results = ParsedEvents(success, warning, error)
        log.info(f"Found {len(results.success)} events from initial gather.")

        # Attach legistar agenda item details
        with ThreadPoolExecutor(min(self.max_concurrent_requests, os.cpu_count() * 5)) as exe:
            f = partial(self._attach_legistar_details_to_event, ignore_minutes_items=self.ignore_minutes_items)
            parsed_events = list(exe.map(f, results.success))

        # Parsed events can be "None" in the case where legistar lookup failed
        # Clean out the "None"s
        parsed_events = [event for event in parsed_events if event is not None]

        log.info(f"Collected: {len(results.success)}. "
                 f"Ignored: {len(results.warning)}. "
                 f"Errored: {len(results.error)}.")

        # Return events
        return parsed_events

    def __str__(self):
        return f"<SeattleEventScraper [{self.main_route}]>"

    def __repr__(self):
        return str(self)
