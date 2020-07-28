#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import pytest
from cdptools.databases.doctypes.body import Body
from cdptools.databases.doctypes.body_base import BodyBase
from cdptools.databases.doctypes.event import Event
from cdptools.databases.doctypes.event_base import EventBase
from cdptools.databases.doctypes.event_minutes_item import EventMinutesItem
from cdptools.databases.doctypes.event_minutes_item_base import EventMinutesItemBase
from cdptools.databases.doctypes.file import File
from cdptools.databases.doctypes.file_base import FileBase
from cdptools.databases.doctypes.matter import Matter
from cdptools.databases.doctypes.matter_base import MatterBase
from cdptools.databases.doctypes.matter_type import MatterType
from cdptools.databases.doctypes.matter_type_base import MatterTypeBase
from cdptools.databases.doctypes.minutes_item import MinutesItem
from cdptools.databases.doctypes.minutes_item_base import MinutesItemBase
from cdptools.databases.doctypes.person import Person
from cdptools.databases.doctypes.person_base import PersonBase
from cdptools.databases.doctypes.role import Role
from cdptools.databases.doctypes.seat import Seat
from cdptools.databases.doctypes.seat_base import SeatBase
from cdptools.databases.doctypes.transcript import Transcript
from cdptools.databases.doctypes.vote import Vote
from cdptools.databases.doctypes.vote_base import VoteBase


# Event


@pytest.mark.parametrize('event_base_dict', [
    (
        {
            "body_name": "fake_name",
            "event_datetime": "fake_event_datetime",
            "id": "fake_id"
        }
    )
])
def test_event_base(event_base_dict):
    """
    Create an EventBase and JSONify an EventBase
    """
    event_base_obj = EventBase.from_dict(event_base_dict)
    new_event_base_dict = event_base_obj.to_dict()

    assert isinstance(event_base_obj, EventBase)
    assert new_event_base_dict == event_base_dict


@pytest.mark.parametrize('event_dict', [
    (
        {
            "body": BodyBase(
                name = "fake_name",
                id = "fake_id"
            ).to_dict(),
            "event_datetime": str(datetime(2000, 1, 1, 0, 0, 0, 0)),
            "thumbnail_static_file": FileBase(
                name = "fake_name",
                uri = "fake/uri",
                id = "fake_id"
            ).to_dict(),
            "thumbnail_hover_file": FileBase(
                name = "fake_name",
                uri = "fake/uri",
                id = "fake_id"
            ).to_dict(),
            "video_uri": "fake/video_uri",
            "keywords": [
                {
                    "fake_key": "fake_value"
                }
            ],
            "matters": [
                MatterBase(
                    name = "fake_name",
                    title = "fake_title",
                    type = "fake_type",
                    decision = "fake_decision",
                    id = "fake_id"
                ).to_dict()
            ],
            "minutes_items": [
                MinutesItemBase(
                    name = "fake_name",
                    id = "fake_id"
                ).to_dict()
            ],
            "people": [
                PersonBase(
                    name = "fake_name",
                    id = "fake_id"
                ).to_dict()
            ],
            "external_source_id": "fake_external_source_id",
            "agenda_uri": "fake_agenda_uri",
            "minutes_uri": "fake_minutes_uri",
            "updated": str(datetime(2000, 1, 1, 0, 0, 0, 0)),
            "created": str(datetime(1999, 1, 1, 0, 0, 0, 0))
        }
    )
])
def test_event(event_dict):
    """
    Create an Event and JSONify an Event.
    """
    event_obj = Event.from_dict(event_dict)
    new_event_dict = event_obj.to_dict()

    assert isinstance(event_obj, Event)
    assert isinstance(event_obj.body, BodyBase)
    assert isinstance(event_obj.thumbnail_static_file, FileBase)
    assert isinstance(event_obj.thumbnail_hover_file, FileBase)
    assert isinstance(event_obj.matters[0], MatterBase)
    assert isinstance(event_obj.minutes_items[0], MinutesItemBase)
    assert isinstance(event_obj.people[0], PersonBase)

    assert new_event_dict == event_dict

# Person


@pytest.mark.parametrize('person_base_dict', [
    (
        {
            "name": "fake_name",
            "id": "fake_id"
        }
    )
])
def test_person_base(person_base_dict):
    """
    Create a PersonBase and JSONify a PersonBase.
    """
    person_base_obj = PersonBase.from_dict(person_base_dict)
    new_person_base_dict = person_base_obj.to_dict()

    assert isinstance(person_base_obj, PersonBase)
    assert new_person_base_dict == person_base_dict


@pytest.mark.parametrize('person_dict', [
    (
        {
            "router_id": "fake_router_id",
            "name": "fake_name",
            "email": "fake_email",
            "phone": "fake_phone",
            "website": "fake_website",
            "picture_file": FileBase(
                name = "fake_name",
                uri = "fake/uri",
                id = "fake_id"
            ).to_dict(),
            "is_active": False,
            "is_council_president": False,
            "most_recent_seat": SeatBase(
                name = "fake_name",
                electoral_area = "fake_electoral_area",
                map_file_id = "fake_map_file",
                map_uri = "fake/map_uri",
                id = "fake_id"
            ).to_dict(),
            "most_recent_chair_body": BodyBase(
                name = "fake_name",
                id = "fake_id"
            ).to_dict(),
            "terms_serving_in_current_seat_role": 0,
            "terms_serving_in_current_committee_chair_role": 0,
            "external_source_id": "fake_external_source_id",
            "updated": str(datetime(2000, 1, 1, 0, 0, 0, 0)),
            "created": str(datetime(2000, 1, 1, 0, 0, 0, 0))
        }
    )
])
def test_person(person_dict):
    """
    Create a Person and JSONify a Person.
    """
    person_obj = Person.from_dict(person_dict)
    new_person_dict = person_obj.to_dict()

    assert isinstance(person_obj, Person)
    assert isinstance(person_obj.picture_file, FileBase)
    assert isinstance(person_obj.most_recent_seat, SeatBase)
    assert isinstance(person_obj.most_recent_chair_body, BodyBase)

    assert new_person_dict == person_dict


# Body


@pytest.mark.parametrize('body_base_dict', [
    (
        {
            "name": "fake_name",
            "id": "fake_id"
        }
    )
])
def test_body_base(body_base_dict):
    """
    Create a BodyBase and JSONify a BodyBase.
    """
    body_base_obj = BodyBase.from_dict(body_base_dict)
    new_body_base_dict = body_base_obj.to_dict()

    assert isinstance(body_base_obj, BodyBase)
    assert new_body_base_dict == body_base_dict


@pytest.mark.parametrize('body_dict', [
    (
        {
            "name": "fake_name",
            "tag": "fake_tag",
            "description": "fake_description",
            "start_date": str(datetime(2000, 1, 1, 0, 0, 0, 0)),
            "end_date": str(datetime(2001, 1, 1, 0, 0, 0, 0)),
            "is_active": False,
            "chair_person_id": "fake_chair_person_id",
            "external_source_id": "fake_external_source_id",
            "updated": str(datetime(1999, 1, 1, 0, 0, 0, 0)),
            "created": str(datetime(1998, 1, 1, 0, 0, 0, 0))
        }
    )
])
def test_body(body_dict):
    """
    Create a Body and JSONify a Body.
    """
    body_obj = Body.from_dict(body_dict)
    new_body_dict = body_obj.to_dict()

    assert isinstance(body_obj, Body)
    assert new_body_dict == body_dict


# File


@pytest.mark.parametrize('file_base_dict', [
    (
        {
            "name": "fake_name",
            "uri": "fake/uri",
            "id": "fake_id"
        }
    )
])
def test_file_base(file_base_dict):
    """
    Create a FileBase and JSONify a FileBase.
    """
    file_base_obj = FileBase.from_dict(file_base_dict)
    new_file_base_dict = file_base_obj.to_dict()

    assert isinstance(file_base_obj, FileBase)
    assert new_file_base_dict == file_base_dict


@pytest.mark.parametrize('file_dict', [
    (
        {
            "uri": "fake/uri",
            "filename": "fake_filename",
            "description": "fake_description",
            "content_type": "fake_content_type",
            "created": str(datetime(2000, 1, 1, 0, 0, 0, 0))
        }
    )
])
def test_file(file_dict):
    """
    Create a File and JSONify a File.
    """
    file_obj = File.from_dict(file_dict)
    new_file_dict = file_obj.to_dict()

    assert isinstance(file_obj, File)
    assert new_file_dict == file_dict


# Transcript


@pytest.mark.parametrize('transcript_dict', [
    (
        {
            "event_id": "fake_event_id",
            "file_id": "fake_file_id",
            "confidence": 0.0,
            "created": str(datetime(2000, 1, 1, 0, 0, 0, 0))
        }
    )
])
def test_transcript(transcript_dict):
    """
    Create a Transcript and JSONify a Transcript.
    """
    transcript_obj = Transcript.from_dict(transcript_dict)
    new_transcript_dict = transcript_obj.to_dict()

    assert isinstance(transcript_obj, Transcript)
    assert new_transcript_dict == transcript_dict


# Seat


@pytest.mark.parametrize('seat_base_dict', [
    (
        {
            "name": "fake_name",
            "electoral_area": "fake_electoral_area",
            "map_file_id": "fake_map_file_id",
            "map_uri": "fake_map_uri",
            "id": "fake_id"
        }
    )
])
def test_seat_base(seat_base_dict):
    """
    Create a SeatBase and JSONify a SeatBase.
    """
    seat_base_obj = SeatBase.from_dict(seat_base_dict)
    new_seat_base_dict = seat_base_obj.to_dict()

    assert isinstance(seat_base_obj, SeatBase)
    assert new_seat_base_dict == seat_base_dict


@pytest.mark.parametrize('seat_dict', [
    (
        {
            "name": "fake_name",
            "electoral_area": "fake_electoral_area",
            "electoral_type": "fake_electoral_type",
            "map_file_id": "fake_map_file_id",
            "map_uri": "fake/map_uri",
            "created": str(datetime(2000, 1, 1, 0, 0, 0, 0))
        }
    )
])
def test_seat(seat_dict):
    """
    Create a Seat and JSONify a Seat.
    """
    seat_obj = Seat.from_dict(seat_dict)
    new_seat_dict = seat_obj.to_dict()

    assert isinstance(seat_obj, Seat)
    assert new_seat_dict == seat_dict


# Role


@pytest.mark.parametrize('role_dict', [
    (
        {
            "person": PersonBase(
                name = "fake_name",
                id = "fake_id"
            ).to_dict(),
            "title": "fake_title",
            "body": BodyBase(
                name = "fake_name",
                id = "fake_id"
            ).to_dict(),
            "start_date": str(datetime(2000, 1, 1, 0, 0, 0, 0)),
            "end_date": str(datetime(2001, 1, 1, 0, 0, 0, 0)),
            "seat_id": "fake_seat_id",
            "external_source_id": "fake_external_source_id",
            "created": str(datetime(1999, 1, 1, 0, 0, 0, 0))
        }
    )
])
def test_role(role_dict):
    """
    Create a Role and JSONify a Role.
    """
    role_obj = Role.from_dict(role_dict)
    new_role_dict = role_obj.to_dict()

    assert isinstance(role_obj, Role)
    assert isinstance(role_obj.person, PersonBase)
    assert isinstance(role_obj.body, BodyBase)

    assert new_role_dict == role_dict


# Minutes Item


@pytest.mark.parametrize('minutes_item_base_dict', [
    (
        {
            "name": "fake_name",
            "id": "fake_id"
        }
    )
])
def test_minutes_item_base(minutes_item_base_dict):
    """
    Create a MinutesItemBase and JSONify a MinutesItemBase.
    """
    minutes_item_base_obj = MinutesItemBase.from_dict(minutes_item_base_dict)
    new_minutes_item_base_dict = minutes_item_base_dict

    assert isinstance(minutes_item_base_obj, MinutesItemBase)
    assert new_minutes_item_base_dict == minutes_item_base_dict


@pytest.mark.parametrize('minutes_item_dict', [
    (
        {
            "name": "fake_name",
            "description": "fake_description",
            "matter": MatterBase(
                name = "fake_name",
                title = "fake_title",
                type = "fake_type",
                decision = "fake_decision",
                id = "fake_id"
            ).to_dict(),
            "external_source_id": "fake_external_source_id",
            "created": str(datetime(2000, 1, 1, 0, 0, 0, 0))
        }
    )
])
def test_minutes_item_dict(minutes_item_dict):
    """
    Create a MinutesItem and JSONify a MinutesItem.
    """
    minutes_item_obj = MinutesItem.from_dict(minutes_item_dict)
    new_minutes_item_dict = minutes_item_obj.to_dict()

    assert isinstance(minutes_item_obj, MinutesItem)
    assert isinstance(minutes_item_obj.matter, MatterBase)

    assert new_minutes_item_dict == minutes_item_dict


# Event Minutes Item


@pytest.mark.parametrize('event_minutes_item_base_dict', [
    (
        {
            "decision": "fake_decision",
            "id": "fake_id",
        }
    )
])
def test_event_minutes_item_base(event_minutes_item_base_dict):
    """
    Create an EventMinutesItemBase and JSONify an EventMinutesItemBase.
    """
    event_minutes_item_base_obj = EventMinutesItemBase.from_dict(event_minutes_item_base_dict)
    new_event_minutes_item_base_dict = event_minutes_item_base_obj.to_dict()

    assert isinstance(event_minutes_item_base_obj, EventMinutesItemBase)
    assert new_event_minutes_item_base_dict == event_minutes_item_base_dict


@pytest.mark.parametrize('event_minutes_item_dict', [
    (
        {
            "event_id": "fake_event_id",
            "minutes_item": MinutesItemBase(
                name = "fake_name",
                id = "fake_id"
            ).to_dict(),
            "index": 1,
            "decision": "fake_decision",
            "matter": MatterBase(
                name = "fake_name",
                title = "fake_title",
                type = "fake_type",
                decision = "fake_decision",
                id = "fake_id"
            ).to_dict(),
            "votes": [
                VoteBase(
                    vote_id = "fake_vote_id",
                    person_id = "fake_person_id",
                    person_name = "fake_person_name",
                    vote_decision = "fake_vote_decision"
                ).to_dict()
            ],
            "files": [
                FileBase(
                    name = "fake_name",
                    uri = "fake/uri",
                    id = "fake_id"
                ).to_dict()
            ]
        }
    )
])
def test_event_minutes_item(event_minutes_item_dict):
    """
    Create an EventMinutesItem and JSONify an EventMinutesItem.
    """
    event_minutes_item_obj = EventMinutesItem.from_dict(event_minutes_item_dict)
    new_event_minutes_item_dict = event_minutes_item_obj.to_dict()

    assert isinstance(event_minutes_item_obj, EventMinutesItem)
    assert isinstance(event_minutes_item_obj.minutes_item, MinutesItemBase)
    assert isinstance(event_minutes_item_obj.matter, MatterBase)
    assert isinstance(event_minutes_item_obj.votes[0], VoteBase)
    assert isinstance(event_minutes_item_obj.files[0], FileBase)

    assert new_event_minutes_item_dict == event_minutes_item_dict


# Vote


@pytest.mark.parametrize('vote_base_dict', [
    (
        {
            "vote_id": "fake_vote_id",
            "person_id": "fake_person_id",
            "person_name": "fake_person_name",
            "vote_decision": "fake_vote_decision"
        }
    )
])
def test_vote_base_dict(vote_base_dict):
    """
    Create a VoteBase and JSONify a VoteBase.
    """
    vote_base_obj = VoteBase.from_dict(vote_base_dict)
    new_vote_base_dict = vote_base_obj.to_dict()

    assert isinstance(vote_base_obj, VoteBase)
    assert new_vote_base_dict == vote_base_dict


@pytest.mark.parametrize('vote_dict', [
    (
        {
            "matter": MatterBase(
                name = "fake_name",
                title = "fake_title",
                type = "fake_type",
                decision = "fake_decision",
                id = "fake_id"
            ).to_dict(),
            "event": EventBase(
                event_datetime = "fake_event_datetime",
                id = "fake_id",
                body_name = "fake_body_name"
            ).to_dict(),
            "event_minutes_item": EventMinutesItemBase(
                decision = "fake_decision",
                id = "fake_id"
            ).to_dict(),
            "person": PersonBase(
                name = "fake_name",
                id = "fake_id"
            ).to_dict(),
            "vote_decision": "fake_vote_decision",
            "is_majority": False,
            "external_vote_item_id": "fake_external_source_id",
            "created": datetime(2000, 1, 1, 0, 0, 0, 0)
        }
    )
])
def test_vote(vote_dict):
    """
    Create a Vote and JSONify a Vote.
    """
    vote_obj = Vote.from_dict(vote_dict)
    new_vote_dict = vote_obj.to_dict()

    assert isinstance(vote_obj, Vote)
    assert isinstance(vote_obj.matter, MatterBase)
    assert isinstance(vote_obj.event, EventBase)
    assert isinstance(vote_obj.event_minutes_item, EventMinutesItemBase)
    assert isinstance(vote_obj.person, PersonBase)

    assert new_vote_dict == vote_dict


# Matter


@pytest.mark.parametrize('matter_base_dict', [
    (
        {
            "name": "fake_name",
            "title": "fake_title",
            "type": "fake_type",
            "decision": "fake_decision",
            "id": "fake_id"
        }
    )
])
def test_matter_base(matter_base_dict):
    """
    Create a MatterBase and JSONify a MatterBase.
    """
    matter_base_obj = MatterBase.from_dict(matter_base_dict)
    new_matter_base_dict = matter_base_obj.to_dict()

    assert isinstance(matter_base_obj, MatterBase)
    assert new_matter_base_dict == matter_base_dict


@pytest.mark.parametrize('matter_dict', [
    (
        {
            "name": "fake_name",
            "matter_type": MatterTypeBase(
                name = "fake_name",
                id = "fake_id"
            ).to_dict(),
            "title": "fake_title",
            "status": "fake_status",
            "most_recent_event": EventBase(
                event_datetime = "fake_event_datetime",
                id = "fake_id",
                body_name = "fake_body_name"
            ).to_dict(),
            "next_event": EventBase(
                event_datetime = "fake_event_datetime",
                id = "fake_id",
                body_name = "fake_body_name"
            ).to_dict(),
            "keywords": [
                {
                    "keyword": "value"
                }
            ],
            "external_source_id": "fake_external_source_id",
            "updated": datetime(2000, 1, 1, 0, 0, 0, 0),
            "created": datetime(1999, 1, 1, 0, 0, 0, 0)
        }
    )
])
def test_matter(matter_dict):
    """
    Create a Matter and JSONify a Matter.
    """
    matter_obj = Matter.from_dict(matter_dict)
    new_matter_dict = matter_obj.to_dict()

    assert isinstance(matter_obj, Matter)
    assert isinstance(matter_obj.matter_type, MatterTypeBase)
    assert isinstance(matter_obj.most_recent_event, EventBase)
    assert isinstance(matter_obj.next_event, EventBase)

    assert new_matter_dict == matter_dict


# MatterType


@pytest.mark.parametrize('matter_type_base_dict', [
    (
        {
            "name": "fake_name",
            "id": "fake_id"
        }
    )
])
def test_matter_type_base(matter_type_base_dict):
    """
    Create a MatterTypeBase and JSONify a MatterTypeBase
    """
    matter_type_base_obj = MatterTypeBase.from_dict(matter_type_base_dict)
    new_matter_type_base_dict = matter_type_base_obj.to_dict()

    assert isinstance(matter_type_base_obj, MatterTypeBase)
    assert new_matter_type_base_dict == matter_type_base_dict


@pytest.mark.parametrize('matter_type_dict', [
    (
        {
            "name": "fake_name",
            "external_source_id": "fake_external_source_id",
            "created": datetime(2000, 1, 1, 0, 0, 0, 0)
        }
    )
])
def test_matter_type(matter_type_dict):
    """
    Create a MatterType and JSONify a MatterType.
    """
    matter_type_obj = MatterType.from_dict(matter_type_dict)
    new_matter_type_dict = matter_type_obj.to_dict()

    assert isinstance(matter_type_obj, MatterType)
    assert new_matter_type_dict == matter_type_dict
