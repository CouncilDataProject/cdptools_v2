#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime

import pytest
from bs4 import BeautifulSoup

from cdptools.event_scrapers.seattle_event_scraper import SeattleEventScraper


@pytest.mark.parametrize("sibling, route, expected", [
    (
        "http://www.seattlechannel.org/CityCouncil",
        "images/seattlechannel/videoimages/channelGeneric.jpg",
        "http://www.seattlechannel.org/images/seattlechannel/videoimages/channelGeneric.jpg"
    ),
    (
        "http://www.seattlechannel.org/CityCouncil/",
        "/images/seattlechannel/videoimages/channelGeneric.jpg",
        "http://www.seattlechannel.org/images/seattlechannel/videoimages/channelGeneric.jpg"
    ),
    (
        "http://www.seattlechannel.org/CityCouncil",
        "http://www.seattlechannel.org/images/seattlechannel/videoimages/channelGeneric.jpg",
        "http://www.seattlechannel.org/images/seattlechannel/videoimages/channelGeneric.jpg"
    ),
    (
        "http://www.seattlechannel.org/CityCouncil/",
        "http://www.seattlechannel.org/images/seattlechannel/videoimages/channelGeneric.jpg",
        "http://www.seattlechannel.org/images/seattlechannel/videoimages/channelGeneric.jpg"
    )
])
def test_resolve_route(sibling, route, expected):
    actual = SeattleEventScraper._resolve_route(sibling, route)
    assert actual == expected


@pytest.mark.parametrize("s, expected", [
    ("hello world", "hello world"),
    (" hello world", "hello world"),
    ("hello world ", "hello world"),
    (" hello world ", "hello world"),
    ("hello world.", "hello world"),
    (" hello world. ", "hello world"),
    ("\n\t\t\t\xa0\xa0he\xa0ll\no \t\twor\xa0\nld\t", "hello world"),
    (" \n\t\t\t\xa0\xa0he\xa0ll\no \t\twor\xa0\nld\t. ", "hello world")
])
def test_clean_string(s, expected):
    actual = SeattleEventScraper._clean_string(s)
    assert actual == expected


MOCK_SOUP_SINGLE_EVENT = ""
with open("cdptools/tests/event_scrapers/test_data/seattle-channel.html") as markup:
    MOCK_SOUP_SINGLE_EVENT = BeautifulSoup(markup.read(), features="html.parser")

MOCK_URI_SINGLE_EVENT = "http://www.seattlechannel.org/mayor-and-council/city-council/2018/2019-civic-development-public-assets-and-native-communities-committee/?videoid=x107461"  # noqa: E501
EXPECTED_SINGLE_EVENT = {
    'minutes_items': ["Chair's Report", 'Public Comment', 'Appointments and Reappointments to Board of Park Commissioners,Seattle Park District Community Oversight Committee, andCentral Waterfront Oversight committee', 'Review of Amended and Restated Monorail System Concession Agreement', 'CB 119661 -relating to Seattle Parks and Recreation (Terry Pettus Park Addition)', 'CB 119700: relating to the Central Waterfront Project (Ocean Pavilion)'],  # noqa: E501
    'body': 'Civic Development, Public Assets, and Native Communities Committee',
    'event_datetime': datetime(2019, 12, 4, 0, 0),
    'source_uri': 'http://www.seattlechannel.org/mayor-and-council/city-council/2018/2019-civic-development-public-assets-and-native-communities-committee/?videoid=x107461',  # noqa: E501
    'video_uri': 'https://video.seattle.gov/media/council/civdev_120419_2541939V.mp4', 'caption_uri': 'https://seattlechannel.org/documents/seattlechannel/closedcaption/2019/civdev_120419_2541939.vtt'  # noqa: E501
}


def test_parse_single_seattle_channel_event():
    event = SeattleEventScraper._parse_single_seattle_channel_event_by_main_content(MOCK_SOUP_SINGLE_EVENT,
                                                                                    MOCK_URI_SINGLE_EVENT,
                                                                                    ignore_date=True)
    assert event == EXPECTED_SINGLE_EVENT


now = SeattleEventScraper.pstnow()
MOCK_EVENT = {
    "agenda_items": ["Public Comment", "CB 999999"],
    "body": "Example Body on Tests",
    "event_datetime": datetime(now.year, now.month, now.day).isoformat(),
    "source_uri": "http://www.seattlechannel.org/testing?videoid=x99999",
    "video_uri": "http://video.seattle.gov:8080/media/council/tests_032919.mp4"
}
m_d_y = "{}/{}/{}".format(now.month, now.day, now.year)
m_d_sy = "{}/{}/{}".format(now.month, now.day, str(now.year)[2:])
MOCK_EVENT_HTML = """<div class="row borderBottomNone paginationItem"><div class="col-xs-12 col-sm-4 col-md-3"><a href="/testing?videoid=x99999" onclick="javascript:loadJWPlayer7('http://video.seattle.gov:8080/media/council/tests_032919.mp4','/images/seattlechannel/videoimages/channelGeneric.jpg', &quot;&lt;p&gt;The City of Seattle conducts a hearing on testing Council Data Project parsers. &lt;/p&gt;&lt;p&gt;&lt;/p&gt;&quot;, 'Example Body on Tests', '{m_d_sy}', '1:31:24', '9021807', false,'x93428', '', '', '', '', '', '', '', '', ''); return false;" target=""><img alt="Example Body on Tests {m_d_sy}" class="img-responsive" src="images/seattlechannel/videoimages/channelGeneric.jpg" title="Example Body on Tests {m_d_sy}"/></a></div><div class="col-xs-12 col-sm-8 col-md-9"><div class="titleDateContainer"><h2 class="paginationTitle"><a href="/testing?videoid=x99999" onclick="javascript:loadJWPlayer7('http://video.seattle.gov:8080/media/council/tests_032919.mp4','images/seattlechannel/videoimages/channelGeneric.jpg', &quot;&lt;p&gt;The City of Seattle conducts a hearing on testing Council Data Project parsers. &lt;/p&gt;&lt;p&gt;&lt;/p&gt;&quot;, 'Example Body on Tests', '{m_d_sy}', '1:31:24', '9021807', false,'x93428', '', '', '', '', '', '', '', '', ''); return false;" title="Example Body on Tests {m_d_sy}">Example Body on Tests</a></h2><div class="videoDate">{m_d_y}</div></div><div class="titleExcerptText"><p>Agenda: Public Comment; CB 999999.</p><p></p></div></div></div>""".format(m_d_y=m_d_y, m_d_sy=m_d_sy)  # noqa: E501
MOCK_EVENT_SOUP = BeautifulSoup(MOCK_EVENT_HTML, "html.parser")
SIBLING_ROUTE = "http://www.seattlechannel.org/CityCouncil"


# def test_parse_seattle_channel_event():
#     event = SeattleEventScraper._parse_seattle_channel_event(MOCK_EVENT_SOUP, SIBLING_ROUTE)
#
#     assert event == MOCK_EVENT


# @pytest.mark.parametrize("a, b, expected", [
#     (["Hello", "World"], ["Hello", "World"], True),
#     (["Hello", "Test", "World"], ["Hello", "World"], True),
#     (["Hello", "World"], ["Hello", "Test", "World"], True),
#     (["Hello"], ["World"], False),
#     (["World", "Hello"], ["Hello", "World"], False),
#     (["This", "Is", "A", "Test"], ["Hello", "Is", "A", "World"], False)
# ])
# def test_two_items_list_match(a, b, expected):
#     assert expected == SeattleEventScraper._shared_items_in_list_exist_and_ordered(a, b)


# TODO:
# Create tests for mock requests to get routes
