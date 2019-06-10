from datetime import datetime, timedelta
import logging
from typing import Dict, List

from fuzzywuzzy import fuzz
import requests

###############################################################################

log = logging.getLogger(__name__)

###############################################################################

LEGISTAR_EVENT_BASE = "http://webapi.legistar.com/v1/{client}/events"


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
    request_format = LEGISTAR_EVENT_BASE + "/{event_id}/EventItems?AgendaNote=1&MinutesNote=1&Attachments=1"
    for event in response:
        # Attach the Event Items to the event
        event["EventItems"] = requests.get(
            request_format.format(
                client=client,
                event_id=event["EventId"]
            )
        ).json()

    log.debug(f"Collected {len(response)} Legistar events")
    return response


def get_matching_legistar_event_by_agenda_match(
    agenda_items_provided: List[str],
    legistar_events: List[Dict]
) -> AgendaMatchResults:
    # Quick return
    if len(legistar_events) == 1:
        return AgendaMatchResults(legistar_events[0], {legistar_events[0]["EventId"]: 100})

    # Calculate fuzzy match agenda list of string
    elif len(legistar_events) > 1:
        # Clean all strings
        agenda_items_provided = [aip.lower() for aip in agenda_items_provided]

        # Create rankings for each event
        max_score = 0.0
        selected_event = None
        scores = {}
        for event in legistar_events:
            event_agenda_items = [str(ei["EventItemTitle"]).lower() for ei in event["EventItems"]]
            match_score = fuzz.token_sort_ratio(agenda_items_provided, event_agenda_items)

            # Add score to map
            scores[event["EventId"]] = match_score

            # Update selected
            if match_score > max_score:
                max_score = match_score
                selected_event = event

        return AgendaMatchResults(selected_event, scores)

    else:
        return AgendaMatchResults({}, {})


#######################################################################################################################
# Used to join legistar details with basic event info

# # Get Legistar events
# legistar_events = legistar_tools.get_legistar_events_for_timespan(
#     self.legistar_client,
#     begin=self.pstnow() - timedelta(days=self.delta),
#     end=self.pstnow()
# )
#
# # Expand results only when legistar details are available
# results = ParsedEvents()
# for body_results in seattle_channel_results:
#     for event in body_results.success:
#         try:
#             # Attach legistar details by look up
#             result = self._attach_legistar_details(event, legistar_events)
#
#             # Successful attach
#             results.success.append(result)
#
#         except errors.LegistarLookupError as e:
#             # For logging purposes, return the errors
#             results.error.append((event, e))
#             log.error(e)
#
# @staticmethod
#
#
# @staticmethod
# def _attach_legistar_details(event: Dict, legistar_events: List[Dict]) -> Dict:
#     # Create a list of events that match bodies
#     body_matches = []
#     for legistar_event in legistar_events:
#         # Because of style differences in naming conventions on legistar vs seattle channel we must
#         # compute a diff ratio to detect for body similarity. The 85 threshold is arbitrary but works well.
#         # Generally, the style differences come down to "and" vs "&" and similar.
#         if fuzz.ratio(event["body"], legistar_event["EventBodyName"]) >= 85:
#             body_matches.append(legistar_event)
#
#     # It may be a body match, but there are occasionally multiple events by the same body on the same day.
#     # In this case we should
#     log.debug("Found {} body matches for event: {} {}".format(
#         len(body_matches), event["body"], event["event_datetime"])
#     )
#
#     # Find the correct event match when multiple events from same body
#     if len(body_matches) > 1:
#         # Check for agenda matches
#         agenda_matches = []
#         for body_match in body_matches:
#             # TODO:
#             # Consider using a text diff ratio on the agenda sets too
#
#             # Check if agenda matches
#             if SeattleEventScraper._shared_items_in_list_exist_and_ordered(
#                 event["agenda"],
#                 [e["EventItemTitle"] for e in body_match["EventItems"]]
#             ):
#                 # Add this body match to the agenda matches
#                 agenda_matches.append(body_match)
#
#         # Handle multiple or no agenda matches by raising error
#         if len(agenda_matches) > 1 or len(agenda_matches) == 0:
#             raise errors.LegistarLookupError(event["body"], event["event_datetime"])
#         # Found a single match: attach the details
#         else:
#             event["legistar_details"] = agenda_matches[0]
#
#     # Check if no matching bodies were found
#     elif len(body_matches) == 0:
#         raise errors.LegistarLookupError(event["body"], event["event_datetime"])
#     # Only a single body match was found: attach the details
#     else:
#         event["legistar_details"] = body_matches[0]
#
#     # Fix event datetime with legistar datetime
#     # Event date comes as a string datetime but with no time attachment, this splits the date and time portions
#     # and grabs only the date portion
#     event_date = event["legistar_details"]["EventDate"].split("T")[0]
#     event_time = event["legistar_details"]["EventTime"]
#
#     # Get the datetime from the formatted string
#     event_datetime = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %I:%M %p")
#
#     # Save a formatted string
#     event["event_datetime"] = str(event_datetime).replace(" ", "T")
#
#     # Save parsed datetime
#     event["parsed_datetime"] = str(datetime.utcnow()).replace(" ", "T")
#
#     return event
