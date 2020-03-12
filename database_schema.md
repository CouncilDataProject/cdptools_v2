# NoSQL Collections

## Notes
Still debating if we should make a "upcoming_events" table as I am not sure if upcoming and past events can properly
be handled in the same table.

To generalize our model a bit further: `legistar_id` has been replaced by `external_source_id`.

### Event
```
event_id: {
    body_id: str
    body_name: str
    event_datetime: datetime
    thumbnail_static_file_id: str
    thumbnail_static_uri: str
    thumbnail_hover_file_id: str
    thumbnail_hover_uri: str
    video_uri: str
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
    external_source_id: int
    agenda_uri: str
    minutes_uri: str
    created: datetime
}
```

### Person
```
person_id: {
    router_id: str
    name: str
    email: str
    phone: str
    website: str
    picture_file_id: str
    picture_uri: str
    is_active: bool
    is_council_president: bool
    most_recent_seat_id: str
    most_recent_seat_name: str
    most_recent_seat_electoral_area: str
    most_recent_seat_map_file_id: str
    most_recent_seat_map_uri: str
    most_recent_chair_body_id: str
    most_recent_chair_body_name: str
    terms_serving_in_current_seat_role: int
    terms_serving_in_current_committee_chair_role: int
    external_source_id: int
    created: datetime
}
```

### Body
```
body_id: {
    name: str
    description: str
    created: datetime
    start_date: datetime
    end_date: datetime
    is_active: bool
    chair_person_id: str
    external_source_id: str
    tag: str
}
```

### File
```
file_id: {
    uri: str
    filename: str
    description: str
    content_type: str
    created: datetime
}
```

### Role
A role is a person's job for a period of time in the city council.
A person can (and should) have multiple roles.
For example: a person has two terms as city council member for D4 then a term as city council member for all-city.
Roles can also be tied to committee chairs.
For example: a council member spends a term on the transportation committee and then spends a term on the finance
committee.
```
role_id: {
    person_id: str
    person_name: str
    title: str
    body_id: str
    body_name: str
    start_date: datetime
    end_date: datetime
    seat_id: str
    external_source_id: int
    created: datetime
}
```

### Seat
A seat is an electable office on the City Council.
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

### Matter
A matter is specifically a legislative matter. A bill, resolution, initiative, etc.
```
matter_id: {
    name: str
    matter_type_id: str
    title: str
    status: str
    most_recent_event: {
        id: str
        body: str
        datetime: datetime
    }
    next_event : {
        id: str
        body: str
        datetime: datetime
    }
    keywords: [
        {
            id: str
            phrase: str
        }
    ]
    external_source_id: int
    updated: datetime
    created: datetime
}
```

### Matter Type
A matter type can be Council Bill, Resolution, Appointment, etc.
```
matter_type_id: {
    name: str
    external_source_id: int
    created: datetime
}
```

### Minutes Item
A minutes item is anything found on the agenda / minutes.
This can be a matter but it can be a presentation or budget file, etc

### Event Minutes Item
A reference tying a specific minutes item to a specific event.

### Vote
A reference typing a specific person, and an event minutes item together.

### Transcript
The primary transcript for an event.
```
transcript_id: {
    event_id: str
    file_id: str
    confidence: float
    created: datetime
}
```

### File
A table to coordinate file details between a database and file store.

### Event Minutes Item File
Any supporting document for a specific events minutes item. Previously this was on the Minutes Item relationship but
that was incorrect as when querying for every level data, all minutes item documents would be returned regardless of
meeting. Example: an event showing all "future" amendments to a matter.

### Body
A body, also known as committee, is a subset of city council members that stands for a certain topic/purpose.
An example would be the Seattle "Governance and Education" committee which consists of 6 of the 9 city council members.
