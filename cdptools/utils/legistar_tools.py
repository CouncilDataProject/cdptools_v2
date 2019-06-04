#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import logging
from typing import Dict, List

from fuzzywuzzy import fuzz
import requests

###############################################################################

log = logging.getLogger(__name__)

###############################################################################

LEGISTAR_BASE = "http://webapi.legistar.com/v1/{client}"
LEGISTAR_VOTE_BASE = LEGISTAR_BASE + "/EventItems"
LEGISTAR_EVENT_BASE = LEGISTAR_BASE + "/Events"
LEGISTAR_MATTER_BASE = LEGISTAR_BASE + "/Matters"
LEGISTAR_PERSON_BASE = LEGISTAR_BASE + "/Persons"


class AgendaMatchResults:
    def __init__(self, selected_event: Dict, match_scores: Dict):
        self.selected_event = selected_event
        self.match_scores = match_scores

###############################################################################


def get_legistar_events_for_timespan(
    client: str,
    begin: datetime = (datetime.utcnow() - timedelta(days=1)),
    end: datetime = (datetime.utcnow() + timedelta(days=1))
) -> List[Dict]:
    """
    Get all legistar events for a client for a given timespan.
    :param client: Which legistar client to target. Ex: "Seattle", "Tacoma", etc.
    :param begin: The timespan begin datetime. Default: Today (datetime.utcnow()) - timedelta(days=1))
    :param end: The timespan end datetime. Default: Yesterday (datetime.utcnow() + timedelta(days=1))
    :return: A list of dictionaries of event details.
    """
    # The unformatted request parts
    filter_datetime_format = "EventDate+{op}+datetime%27{dt}%27"
    request_format = LEGISTAR_EVENT_BASE + "?$filter={begin}+and+{end}"

    # Get response from formatted request
    log.debug(f"Querying Legistar for events between: {begin} - {end}")
    response = requests.get(
        request_format.format(
            client=client,
            begin=filter_datetime_format.format(op="ge", dt=str(begin).replace(" ", "T")),
            end=filter_datetime_format.format(op="lt", dt=str(end).replace(" ", "T"))
        )
    ).json()

    # Get all event items for each event
    item_request_format = LEGISTAR_EVENT_BASE + "/{event_id}/EventItems?AgendaNote=1&MinutesNote=1&Attachments=1"
    for event in response:
        # Attach the Event Items to the event
        event["EventItems"] = requests.get(
            item_request_format.format(
                client=client,
                event_id=event["EventId"]
            )
        ).json()

        # Get vote information
        for event_item in event["EventItems"]:
            vote_request_format = LEGISTAR_VOTE_BASE + "/{event_item_id}/Votes"
            event_item["EventItemVoteInfo"] = requests.get(
                vote_request_format.format(
                    client=client,
                    event_item_id=event_item["EventItemId"]
                )
            ).json()

            # Get person information
            for vote_info in event_item["EventItemVoteInfo"]:
                person_request_format = LEGISTAR_PERSON_BASE + "/{person_id}"
                vote_info["PersonInfo"] = requests.get(
                    person_request_format.format(
                        client=client,
                        person_id=vote_info["VotePersonId"]
                    )
                ).json()

    log.debug(f"Collected {len(response)} Legistar events")
    return response


def get_matching_legistar_event_by_minutes_match(
    minutes_items_provided: List[str],
    legistar_events: List[Dict]
) -> AgendaMatchResults:
    # Quick return
    if len(legistar_events) == 1:
        return AgendaMatchResults(legistar_events[0], {legistar_events[0]["EventId"]: 100})

    # Calculate fuzzy match agenda list of string
    elif len(legistar_events) > 1:
        # Clean all strings
        minutes_items_provided = [aip.lower() for aip in minutes_items_provided]

        # Create rankings for each event
        max_score = 0.0
        selected_event = None
        scores = {}
        for event in legistar_events:
            event_minutes_items = [str(ei["EventItemTitle"]).lower() for ei in event["EventItems"]]
            match_score = fuzz.token_sort_ratio(minutes_items_provided, event_minutes_items)

            # Add score to map
            scores[event["EventId"]] = match_score

            # Update selected
            if match_score > max_score:
                max_score = match_score
                selected_event = event

        return AgendaMatchResults(selected_event, scores)

    else:
        return AgendaMatchResults({}, {})


def parse_legistar_event_details(legistar_event_details: Dict, ignore_minutes_items: List[str] = []) -> Dict:
    # Parse official datetime
    event_date = legistar_event_details["EventDate"].split("T")[0]
    event_dt = "{}T{}".format(event_date, legistar_event_details["EventTime"])
    event_dt = datetime.strptime(event_dt, "%Y-%m-%dT%I:%M %p")

    # Parse event items
    minutes_items = []
    for legistar_event_item in legistar_event_details["EventItems"]:
        # Choose name based off available data
        if legistar_event_item["EventItemMatterName"]:
            minutes_item_name = legistar_event_item["EventItemMatterName"]
        else:
            minutes_item_name = legistar_event_item["EventItemTitle"]

        # Only continue if the minutes item name is not ignored
        if minutes_item_name not in ignore_minutes_items:
            # Construct minutes item
            minutes_item = {
                "name": minutes_item_name,
                "index": int(legistar_event_item["EventItemMinutesSequence"]),
                "legistar_event_item_id": int(legistar_event_item["EventItemId"])
            }

            # Parse attachments
            item_attachments = []
            for matter_attachment in legistar_event_item["EventItemMatterAttachments"]:
                item_attachment = {
                    "name": matter_attachment["MatterAttachmentName"],
                    "uri": matter_attachment["MatterAttachmentHyperlink"],
                    "legistar_matter_attachment_id": int(matter_attachment["MatterAttachmentId"])
                }
                item_attachments.append(item_attachment)

            # Parse votes
            votes = []
            if legistar_event_item["EventItemPassedFlagName"]:
                for vote_info in legistar_event_item["EventItemVoteInfo"]:
                    votes.append({
                        "decision": vote_info["VoteValueName"],
                        "legistar_event_item_vote_id": int(vote_info["VoteId"]),
                        "person": {
                            "full_name": vote_info["PersonInfo"]["PersonFullName"],
                            "email": vote_info["PersonInfo"]["PersonEmail"],
                            "phone": vote_info["PersonInfo"]["PersonPhone"],
                            "website": vote_info["PersonInfo"]["PersonWWW"],
                            "legistar_person_id": vote_info["PersonInfo"]["PersonId"]
                        }
                    })
                    minutes_item["decision"] = legistar_event_item["EventItemPassedFlagName"]
            else:
                minutes_item["decision"] = None

            minutes_item["votes"] = votes

            # Update and add the agenda item
            minutes_item["attachments"] = item_attachments
            minutes_items.append(minutes_item)

    # Sort by index
    minutes_items = sorted(minutes_items, key=lambda i: i["index"])

    # Store the details
    parsed_details = {
        "agenda_file_uri": legistar_event_details["EventAgendaFile"],
        "body": legistar_event_details["EventBodyName"],
        "event_datetime": event_dt,
        "minutes_items": minutes_items,
        "legistar_event_id": int(legistar_event_details["EventId"]),
        "legistar_event_link": legistar_event_details["EventInSiteURL"],
        "minutes_file_uri": legistar_event_details["EventMinutesFile"]
    }

    return parsed_details
