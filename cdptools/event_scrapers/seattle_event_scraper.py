#!/usr/bin/env python
# -*- coding: utf-8 -*-

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import hashlib
import logging
import os
import re
from typing import Dict, List, Union

from bs4 import BeautifulSoup
import requests

from . import errors
from .event_scraper import EventScraper


###############################################################################

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)4s: %(module)s:%(lineno)4s %(asctime)s] %(message)s'
)
log = logging.getLogger(__file__)

###############################################################################


class ParsedEvents(object):

    def __init__(
        self,
        success: List[Dict] = None,
        warning: List[errors.EventOutOfTimeboundsError] = None,
        error: List[Union[errors.EventParseError, errors.LegistarLookupError]] = None
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
        legistar_client: str = "seattle",
        max_concurrent_requests: int = None,
        **kwargs
    ):
        # Store configuration
        self.main_route = main_route
        self.legistar_client = legistar_client
        if max_concurrent_requests:
            self.max_concurrent_requests = max_concurrent_requests
        else:
            self.max_concurrent_requests = os.cpu_count() * 5

    @staticmethod
    def _resolve_route(complete_sibling: str, route: str) -> str:
        """
        Resolve a url route.
        If "http" or "https" is found in the route it is assumed the route is already complete.
        If not, the sibling is split, tail removed, and the route is attached.
        :param complete_sibling: A complete sibling route to retrieve the complete parent from.
        :param route: A route to attach to the parent of the sibling.
        :return: The parent of sibling joined with route as a child.
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
        :param s: The string to clean.
        :return: The cleaned string.
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
    def _parse_seattle_channel_event(event_container: BeautifulSoup, complete_sibling: str) -> Dict:
        """
        Parse a single event from the html of a Seattle Channel event block.
        :param event_container: A BeautifulSoup object created from reading a single event div block.
        :param complete_sibling: A complete sibling to the sub route currently being processed.
        :return: A dictionary of event details that have been parsed from the provided html block.
        """
        # Find event details
        event_details = event_container.find("div", class_="col-xs-12 col-sm-8 col-md-9")
        body = event_details.find("h2").text.replace("\n", "")
        date = event_details.find("div", class_="videoDate").text

        # Split date into components
        month, day, year = tuple(date.split("/"))
        # Create datetime string
        event_dt = datetime(int(year), int(month), int(day))

        # Agendas have mixed formatting
        try:
            agenda = event_details.find("div", class_="titleExcerptText").find("p").text
        except AttributeError:
            try:
                agenda = event_details.find("div", class_="titleExcerptText").text
            except AttributeError:
                raise errors.EventParseError(body, event_dt)

        # Check executive session
        if "executive session" in agenda.lower():
            raise errors.ExecutiveSessionError(body, event_dt)

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
        thumbnail = video_and_thumbnail.find("a").find("img").get("src")
        video = video_and_thumbnail.find("a").get("onclick")
        seattle_channel_page = video_and_thumbnail.find("a").get("href")

        # Onclick returns a javascript function
        # Try to find the url the function redirects to
        try:
            # All seattle channel videos are hosted at "video.seattle.gov:8080/..."
            # This will find the true url by searching for a substring that matches the above pattern
            # Note: some of the urls have spaces in the video filename which is why the space is included in the
            # regex search pattern.
            video = re.search(r"http://video\.seattle\.gov\:8080[a-zA-Z0-9\/_ ]*\.(mp4|flv)", video).group(0)
        except AttributeError:
            raise errors.EventParseError(body, event_dt)

        # If the event was not today, ignore it.
        # now = SeattleEventScraper.pstnow()
        # yesterday = now - timedelta(days=1)
        # if not (dt > yesterday and dt < now):
        #     raise errors.EventOutOfTimeboundsError(dt, yesterday, now)

        # Construct event
        event = {
            "agenda": [SeattleEventScraper._clean_string(item) for item in agenda],
            "body": SeattleEventScraper._clean_string(body),
            "event_datetime": str(event_dt).replace(" ", "T"),
            "parsed_datetime": datetime.utcnow(),
            "source_url": SeattleEventScraper._resolve_route(complete_sibling, seattle_channel_page),
            "thumbnail_url": SeattleEventScraper._resolve_route(complete_sibling, thumbnail),
            "video_url": video.replace(" ", "")
        }

        # Add SHA256 to act as a key
        key = hashlib.sha256(event["video_url"].encode("utf8")).hexdigest()
        event["key"] = key

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
                event = self._parse_seattle_channel_event(container, self.main_route)

                # Successful parse
                events.success.append(event)

            except (errors.EventOutOfTimeboundsError, errors.ExecutiveSessionError) as e:
                # For logging purposes, return the errors
                events.warning.append((container, e))

            except errors.EventParseError as e:
                # For logging purposes, return the errors
                events.error.append((container, e))

        # Return processed events
        log.debug(f"Collected {len(events.success)}. Errors: {len(events.error)}. {url}")
        return events

    def get_events(self) -> List[Dict]:
        # Complete seattle channel event collection in threadpool
        with ThreadPoolExecutor(min(self.max_concurrent_requests, os.cpu_count() * 5)) as exe:
            seattle_channel_results = list(exe.map(self._collect_sub_route_events, self.get_routes()))

        # Reduce and summarize in log
        success = []
        warning = []
        error = []
        for body_result in seattle_channel_results:
            success += body_result.success
            warning += body_result.warning
            error += body_result.error
        results = ParsedEvents(
            success,
            warning,
            error
        )
        log.info(f"Collected: {len(results.success)}. "
                 f"Ignored: {len(results.warning)}. "
                 f"Errored: {len(results.error)}.")

        # Return events
        return results.success

    def __str__(self):
        return f"<SeattleEventScraper [{self.main_route}]>"

    def __repr__(self):
        return str(self)
