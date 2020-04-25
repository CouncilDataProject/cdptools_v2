# Document Store Schema

## Event
An event can be a normally scheduled meeting, a special event such as a press conference or election debate, and, can be
upcoming or historical.

_Schema_
```
event_id: {
    body: {
        id: str
        name: str
    }
    event_datetime: datetime
    thumbnail_static_file: {
        id: str
        uri: str
    }
    thumbnail_hover_file: {
        id: str
        uri: str
    }
    video_uri: optional[str]
    keywords: [
        {
            id: str
            phrase: str
        }
    ]
    matters: [
        {
            id: str
            name: str
            decision: str
        }
    ]
    minutes_items: [
        {
            id: str
            name: str
        }
    ]
    people: [
        {
            id: str
            name: str
        }
    ]
    external_source_id: optional[any]
    agenda_uri: str
    minutes_uri: optional[str]
    updated: datetime
    created: datetime
}
```

_Examples_

_Notes_
Because the `event` collection can contain future events, their may be no thumbnail for the video. In this case, having
a default thumbnail is suggested. Once an event have occurred, do not make a new event, but update the same event.
Instead of labeling them as optional, any of the list attributes are rather just empty lists until filled.


## Person
Primarily the councilors, this could technically include the mayor or city manager, or any other "normal" presenters and
attendees of meetings.

_Schema_
```
person_id: {
    router_id: optional[str]
    name: str
    email: optional[str]
    phone: optional[str]
    website: optional[str]
    picture_file: {
        id: str
        uri: str
    }
    is_active: bool
    is_council_president: bool
    most_recent_seat: {
        id: str
        name: str
        electoral_area: str
        map_file_id: str
        map_uri: str
    }
    most_recent_chair_body: {
        id: str
        name: str
    }
    terms_serving_in_current_seat_role: int
    terms_serving_in_current_committee_chair_role: int
    external_source_id: optional[any]
    updated: datetime
    created: datetime
}
```

_Examples_


## Body
A body, also known as committee, is a subset of city council members that stands for a certain topic/purpose.
An example would be the Seattle "Governance and Education" committee which consists of 6 of the 9 city council members.
This can however include general categories such as "Debate", or "Press Conference", etc.

_Schema_
```
body_id: {
    name: str
    tag: str
    description: optional[str]
    start_date: datetime
    end_date: optional[datetime]
    is_active: bool
    chair_person_id: str
    external_source_id: optional[any]
    updated: datetime
    created: datetime
}
```

_Examples_


## File
A collection to coordinate file details between a database and file store.

_Schema_
```
file_id: {
    uri: str
    filename: str
    description: optional[str]
    content_type: optional[str]
    created: datetime
}
```

_Examples_


## Transcript
The primary transcript for an event.

_Schema_
```
transcript_id: {
    event_id: str
    file_id: str
    confidence: float
    created: datetime
}
```

_Examples_


## Seat
A seat is an electable office on the City Council or Executive position.

_Schema_
```
seat_id: {
    name: str
    electoral_area: str
    electoral_type: str
    map_file_id: str
    map_uri: str
    created: datetime
}
```

_Examples_

_Notes_
These are managed from a pre-populate database script that should be ran prior to any other "streaming" data entering
the system.


## Role
A role is a person's job for a period of time in the city council. A person can (and should) have multiple roles.
For example: a person has two terms as city council member for D4 then a term as city council member for all-city.
Roles can also be tied to committee chairs. For example: a council member spends a term on the transportation committee
and then spends a term on the finance committee.

_Schema_
```
role_id: {
    person: {
        id: str
        name: str
    }
    title: str
    body: {
        id: str
        name: str
    }
    start_date: datetime
    end_date: optional[datetime]
    seat_id: str
    external_source_id: optional[any]
    created: datetime
}
```

_Examples_


## Minutes Item
A minutes item is anything found on the agenda / minutes. This can be a matter but it can be a presentation or budget
file, etc

_Schema_
```
minutes_item_id: {
    name: str
    description: optional[str]
    matter: {
      id: str
      name: str
      title: str
    }
    external_source_id: optional[any]
    created: datetime
}
```

_Examples_

_Notes_
The `matter` field is optional based off if the minutes is tied to a matter or not.


## Event Minutes Item
A reference tying a specific minutes item to a specific event.

_Schema_
```
event_minutes_item_id: {
    event_id: str
    minutes_item: {
      id: str
      name: str
    }
    index: int
    decision: optional[str]
    matter: {
      id: str
      name: str
      title: str
    }
    votes: [
        {
            vote_id: str
            person_id: str
            person_name: str
            vote_decision: str
        }
    ]
    files: [
        {
           name: str
           uri: str
        }
    ]
}
```

_Examples_

_Notes_
Similar to `Minutes Item`, `matter`, `votes`, and `files` are all optional depending on if they are actually present.

These files can be thought are any supporting document for a specific events minutes item. Previously this was on the
Minutes Item relationship but that was incorrect as when querying for every level data, all minutes item documents
would be returned regardless of meeting. Example: an event showing all "future" amendments to a matter.

And, while this is labeled with `files`, these are not "internal-to-CDP" files. Meaning, these files aren't stored in a
CDP file store and details of the files are not stored in a CDP database. These are references to files stored by the
local municipality.


## Vote
A reference typing a specific person, and an event minutes item together.

_Schema_
```
vote_id: {
    matter: {
        id: str
        title: str
        name: str
        type: str
    }
    event: {
        id: str
        body_name: str
        event_datetime: datetime
    }
    event_minutes_item: {
        id: str
        decision: str
    }
    person: {
        id: str
        name: str
    }
    vote_decision: str
    is_majority: bool
    external_vote_item_id: optional[any]
    created: datetime
}
```

_Examples_


## Matter
A matter is specifically a legislative matter. A bill, resolution, initiative, etc.

_Schema_
```
matter_id: {
    name: str
    matter_type: {
        id: str
        name: str
    }
    title: str
    status: str
    most_recent_event: {
        id: str
        body: str
        datetime: datetime
    }
    next_event : {
        id: str
        body_name: str
        datetime: datetime
    }
    keywords: [
        {
            id: str
            phrase: str
        }
    ]
    external_source_id: optional[any]
    updated: datetime
    created: datetime
}
```

_Examples_

_Notes_
Depending on if the matter has gone through council yet, `most_recent_event` and `next_event` can be optional.


## Matter Type
A matter type can be Council Bill, Resolution, Appointment, etc.

_Schema_
```
matter_type_id: {
    name: str
    external_source_id: optional[all]
    created: datetime
}
```

_Examples_

---

## General Notes

There are additional indexing tables that are used to populate any of the `keywords` lists. These are generated from the
`index` pipelines. More details to come.
