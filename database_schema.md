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
    transcript_id: str
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
    most_recent_district_id: str
    most_recent_district_name: str
    most_recent_district_map_file_id: str
    most_recent_district_map_uri: str
    most_recent_chair_body_id: str
    most_recent_chair_body_name: str
    terms_serving_in_current_district_role: int
    terms_serving_in_current_committee_chair_role: int
    external_source_id: int
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

### Matter
A matter is specifically a legislative matter. A bill, resolution, initiative, etc. It has a sponser which may be a
person or a body.

### Minutes Item
A minutes item is anything found on the agenda / minutes.
This can be a matter but it can be a presentation or budget file, etc

### Event Minutes Item
A reference tying a specific minutes item to a specific event.

### Vote
A reference typing a specific person, and an event minutes item together.

### Transcript
The primary transcript for an event.

### File
A table to coordinate file details between a database and file store.

### Event Minutes Item File
Any supporting document for a specific events minutes item. Previously this was on the Minutes Item relationship but
that was incorrect as when querying for every level data, all minutes item documents would be returned regardless of
meeting. Example: an event showing all "future" amendments to a matter.
