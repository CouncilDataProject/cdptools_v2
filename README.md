# cdptools

[![build status](https://travis-ci.com/CouncilDataProject/cdptools.svg?branch=master)](https://travis-ci.com/CouncilDataProject/cdptools)
[![codecov](https://codecov.io/gh/CouncilDataProject/cdptools/branch/master/graph/badge.svg)](https://codecov.io/gh/CouncilDataProject/cdptools)


Making City Council data more accessible and actions taken by city council members more discoverable and trackable.

## User Features
* Plain text query for events or minutes items
* Database schema allows for simple querying of:
    * events (meetings)
    * voting history of a city council or city council member
    * bodies (committees)
    * members
    * minutes items
    * event transcripts
* File stores and databases can be used in combination to download audio of the meeting or the entire transcripts

## Developer Features
* Modular system for gathering city council events, transcribing, and indexing them to make searchable.
* Data pipelines are highly customizable to fit your cities needs.
* From:
    * video ->
    * storing audio ->
    * generating transcripts ->
    * indexing ->
    * analysis


## Quickstart Documentation

***Search for events using plain text:***
```python
from cdptools.databases import CloudFirestoreDatabase
db = CloudFirestoreDatabase("cdp-seattle")

matching_events = db.search_events("bicycle infrastructure, pedestrian mobility, greenways")
# Returns list of Match objects sorted most to least relevant
# [Match, Match, ...]

# Use the `Match.data` attribute to view the matches data
matching_events[0].data
# {
#   'event_id': '05258417-9ad3-4d42-be1d-95eafcfa03c5',
#   'legistar_event_id': 4053,
#   'event_datetime': datetime.datetime(2019, 8, 5, 9, 30),
#   ...
# }
```

***Get all data from a table:***
```python
from cdptools.databases import CloudFirestoreDatabase
db = CloudFirestoreDatabase("cdp-seattle")

all_events = db.select_rows_as_list("event")
# Returns list of dictionaries with event information
# [{"event_id": "0123", ...}, ...]
```

***Download the most recent transcripts for all events:***
```python
from cdptools.databases import CloudFirestoreDatabase
from cdptools.file_stores import GCSFileStore
from cdptools.research_utils import download_most_recent_transcripts
db = CloudFirestoreDatabase("cdp-seattle")
fs = GCSFileStore("cdp-seattle.appspot.com")

event_corpus_map = download_most_recent_transcripts(db, fs)
# Returns a dictionary mapping event id to a local path of the transcript
# {"0123abc...": "~/4567def..."}
```

Please view the [examples](/examples) directory which contains Jupyter notebooks with more examples on how to use CDP
databases and file stores.

For additional information on system design, look at [system_design.md](docs/system_design.md).

## Installation
`cdptools` is available on [pypi.org](https://pypi.org/project/cdptools/).

#### Per city installation:
* Seattle: `pip install cdptools[google-cloud]`

#### All city installation:
`pip install cdptools[all]`

**Free software: BSD-3-Clause license**

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter).
