# cdptools

[![build status](https://travis-ci.com/CouncilDataProject/cdptools.svg?branch=master)](https://travis-ci.com/CouncilDataProject/cdptools)
[![codecov](https://codecov.io/gh/CouncilDataProject/cdptools/branch/master/graph/badge.svg)](https://codecov.io/gh/CouncilDataProject/cdptools)


Making City Council data more accessible and actions taken by city council members more discoverable and trackable.

## User Features
* Plain text query for events or minutes items
* [Database schema](docs/resources/database_diagram.pdf) allows for simple querying of:
    * events (meetings)
    * voting history of a city council or city council member
    * bodies (committees)
    * members
    * minutes items
    * event transcripts
* File stores and databases can be used in combination to download audio or the entire transcript of a meeting

## Quickstart Documentation

***Search for events using plain text:***
```python
from cdptools import CDPInstance, configs
seattle = CDPInstance(configs.SEATTLE)

matching_events = seattle.database.search_events("bicycle infrastructure, pedestrian mobility")
# Returns list of Match objects sorted most to least relevant
# [Match, Match, ...]

# Use the `Match.data` attribute to view the match's data
matching_events[0].data
# {
#   'event_id': '05258417-9ad3-4d42-be1d-95eafcfa03c5',
#   'legistar_event_id': 4053,
#   'event_datetime': datetime.datetime(2019, 8, 5, 9, 30),
#   ...
# }
```

***Search for bills, appointments, 'minutes items' using plain text:***
```python
from cdptools import CDPInstance, configs
seattle = CDPInstance(configs.SEATTLE)

matching_minutes_items = seattle.database.search_minutes_items("bicycle infrastructure")
# Returns list of Match objects sorted most to least relevant
# [Match, Match, ...]
```

***Get all data from a table:***
```python
from cdptools import CDPInstance, configs
seattle = CDPInstance(configs.SEATTLE)

all_events = seattle.database.select_rows_as_list("event")
# Returns list of dictionaries with event information
# [{"event_id": "0123", ...}, ...]
```

***Download the most recent transcripts for all events:***
```python
from cdptools import CDPInstance, configs
seattle = CDPInstance(configs.SEATTLE)

event_corpus_map = seattle.download_most_recent_transcripts()
# Returns a dictionary mapping event id to a local path of the transcript
# {"0123abc...": "~/4567def..."}
```

Please view the [examples](/examples) directory which contains Jupyter notebooks with more examples on how to use CDP
databases and file stores.

## Installation
`cdptools` is available on [pypi.org](https://pypi.org/project/cdptools/).

#### All City Installation:
`pip install cdptools[all]`

#### Individual City Installation:
* Seattle: `pip install cdptools[google-cloud]`

## Developer Features
* Modular system for gathering city council events, transcribing, and indexing them to make searchable.
* Data pipelines are highly customizable to fit your cities needs.
* Deploy and run pipelines using Docker to ensure your system has everything it needs.

For additional information on system design, refer to [system_design.md](docs/system_design.md).
For information on deploying a new CDP instance refer to the [deployment with Docker documentation](deploy/).

**Free software: BSD-3-Clause license**

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter).
