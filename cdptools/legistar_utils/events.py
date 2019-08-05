#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Union

import requests
from fuzzywuzzy import fuzz

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
    begin: datetime = (datetime.utcnow()),
    end: datetime = (datetime.utcnow() + timedelta(days=1)),
    store_each_response: bool = False
) -> List[Dict]:
    """
    Get all legistar events and each events minutes items, people, and votes, for a client for a given timespan.

    Parameters
    ----------
    client: str
        Which legistar client to target. Ex: "seattle"
    begin: datetime
        The timespan beginning datetime to query for events after.
    end: datetime
        The timespan end datetime to query for events before.
    store_each_response: bool
        Option to store each response as they come in. Used to store the data for testing the event gather pipeline.

    Returns
    -------
    events: List[Dict]
        All legistar events that occur between the datetimes provided for the client provided. Additionally, requests
        and attaches agenda items, minutes items, any attachments, called "EventItems", requests votes for any of these
        "EventItems", and requests person information for any vote.
    """
    # Request counter
    request_counter = 0

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
    if store_each_response:
        with open(f"request_{request_counter}_events.json", "w") as write_out:
            json.dump(response, write_out)
    request_counter += 1

    # Get all event items for each event
    item_request_format = LEGISTAR_EVENT_BASE + "/{event_id}/EventItems?AgendaNote=1&MinutesNote=1&Attachments=1"
    for i, event in enumerate(response):
        # Attach the Event Items to the event
        event["EventItems"] = requests.get(
            item_request_format.format(
                client=client,
                event_id=event["EventId"]
            )
        ).json()
        if store_each_response:
            with open(f"request_{request_counter}_event_{i}_items.json", "w") as write_out:
                json.dump(event["EventItems"], write_out)
        request_counter += 1

        # Get vote information
        for j, event_item in enumerate(event["EventItems"]):
            vote_request_format = LEGISTAR_VOTE_BASE + "/{event_item_id}/Votes"
            event_item["EventItemVoteInfo"] = requests.get(
                vote_request_format.format(
                    client=client,
                    event_item_id=event_item["EventItemId"]
                )
            ).json()
            if store_each_response:
                with open(f"request_{request_counter}_event_{i}_item_{j}_votes.json", "w") as write_out:
                    json.dump(event_item["EventItemVoteInfo"], write_out)
            request_counter += 1

            # Get person information
            for k, vote_info in enumerate(event_item["EventItemVoteInfo"]):
                person_request_format = LEGISTAR_PERSON_BASE + "/{person_id}"
                vote_info["PersonInfo"] = requests.get(
                    person_request_format.format(
                        client=client,
                        person_id=vote_info["VotePersonId"]
                    )
                ).json()
                if store_each_response:
                    with open(f"request_{request_counter}_event_{i}_item_{j}_vote_{k}_person.json", "w") as write_out:
                        json.dump(vote_info["PersonInfo"], write_out)
                request_counter += 1

    log.debug(f"Collected {len(response)} Legistar events")
    return response


def get_matching_legistar_event_by_minutes_match(
    minutes_items_provided: List[str],
    legistar_events: List[Dict]
) -> AgendaMatchResults:
    """
    Provided a list of strings that represent "display name" minutes items, find the closest matching legistar event
    for the list provided. An example of this function being used may be found in SeattleEventScraper, but as a general
    use case, this will be used when a city has two separate systems for storing video and storing legistar data and
    you need to match up the video data with the legistar data. Event matching is determined by minutes item text set
    difference. For details, on that algorithm, look at `fuzzywuzzy.fuzz.token_set_ratio`.

    Parameters
    ----------
    minutes_items_provided: List[str]
        The minutes items provided from the non-legistar system.
    legistar_events: List[Dict]
        The legistar events list produced from `get_legistar_events_for_timespan`.

    Returns
    -------
    match_details: AgendaMatchResults
        An object to store the match results. Which contains an attribute for the highest matching and then the scores
        for the rest of the checked event.
    """
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
            # Choose name based off available data
            event_minutes_items = []
            for ei in event["EventItems"]:
                if ei["EventItemMatterName"]:
                    event_minutes_items.append(ei["EventItemMatterName"])
                else:
                    event_minutes_items.append(ei["EventItemTitle"])

            # Token set ratio
            match_score = fuzz.token_set_ratio(minutes_items_provided, event_minutes_items)

            # Add score to map
            scores[event["EventId"]] = match_score

            # Update selected
            if match_score > max_score:
                max_score = match_score
                selected_event = event

        return AgendaMatchResults(selected_event, scores)

    else:
        return AgendaMatchResults({}, {})


def _clean_legistar_string_data(text: Union[str, None]) -> Union[str, None]:
    if text:
        return str(text).replace("\r", "").replace("\n", "").replace("_", "")

    return text


def parse_legistar_event_details(legistar_event_details: Dict, ignore_minutes_items: List[str] = []) -> Dict:
    """
    Parse the full legistar event details and format into the CDP ready JSON dictionary for upload.

    Parameters
    ----------
    legistar_event_details: Dict
        The full legistar event details with source and video URIs added.
    ignore_minutes_items: List[str]
        It is fairly common to have minutes items that can be ignored. Any strings added to this list will be dropped
        during the formatting of the CDP ready JSON object.

    Returns
    -------
    formatted: Dict
        The parsed and CDP storage ready formatted JSON object to upload.
    """
    # Parse official datetime
    event_date = legistar_event_details["EventDate"].split("T")[0]
    event_dt = "{}T{}".format(event_date, legistar_event_details["EventTime"])
    event_dt = datetime.strptime(event_dt, "%Y-%m-%dT%I:%M %p")

    # Parse event items
    minutes_items = []
    for legistar_event_item in legistar_event_details["EventItems"]:
        # Choose name based off available data
        if legistar_event_item["EventItemMatterName"]:
            minutes_item_name = _clean_legistar_string_data(legistar_event_item["EventItemMatterName"])
        else:
            minutes_item_name = _clean_legistar_string_data(legistar_event_item["EventItemTitle"])

        # Choose matter name based off available data
        if legistar_event_item["EventItemMatterName"]:
            minutes_item_matter = _clean_legistar_string_data(legistar_event_item["EventItemMatterName"])
        else:
            minutes_item_matter = _clean_legistar_string_data(legistar_event_item["EventItemMatterFile"])

        # Only continue if the minutes item name is not ignored
        if minutes_item_name not in ignore_minutes_items:
            # Sometimes this is missing...
            # Not sure why
            index = legistar_event_item["EventItemMinutesSequence"]

            # In the case it is present, add it
            if index:
                index = int(index)
            # In the case it isn't. Default to -1
            else:
                index = -1

            # Construct minutes item
            minutes_item = {
                "name": minutes_item_name,
                "matter": minutes_item_matter,
                "index": index,
                "legistar_event_item_id": int(legistar_event_item["EventItemId"])
            }

            # Parse attachments
            item_attachments = []
            for matter_attachment in legistar_event_item["EventItemMatterAttachments"]:
                item_attachment = {
                    "name": _clean_legistar_string_data(matter_attachment["MatterAttachmentName"]),
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
