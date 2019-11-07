# cdptools

[![Build Status](https://github.com/CouncilDataProject/cdptools/workflows/Build%20Master/badge.svg)](https://github.com/CouncilDataProject/cdptools/actions)
[![Documentation](https://github.com/CouncilDataProject/cdptools/workflows/Documentation/badge.svg)](https://CouncilDataProject.github.io/cdptools)
[![Code Coverage](https://codecov.io/gh/CouncilDataProject/cdptools/branch/master/graph/badge.svg)](https://codecov.io/gh/CouncilDataProject/cdptools)

Making City Council data more accessible and actions taken by city council members more discoverable and trackable.

---

## About
We wondered why it was so hard to find out what was being discussed in Seattle City Council about a specific topic, so
we set out to solve that. The first step to this is basic data processing: automated transcript creation for city
council events, indexing those transcripts, and finally making them available on the web via our website and database.
We also wanted the entire system to aim to be low cost, modular, and open access, so that it would be relatively easy
for other CDP instances to be created and maintained. For us that means, databases and file stores are open access to
read from, the websites that users can interact with the data can be run on free hosting services such as GitHub Pages,
and computation choices should be flexible so that cost isn't a barrier issue.

The first CDP instance to be deployed was for Seattle and an example of the data that is produced and available from
these systems can be seen on our [Seattle instance website](https://councildataproject.github.io/seattle/). The
repository and code for the instance website can be found [here](https://github.com/CouncilDataProject/seattle).

This repository and Python package is a collection of tools, pipelines, and processing functions, that are used by
servers to retrieve, package, store, and process data required by CouncilDataProject instances.

While this package is primarily targeted towards developers of the CDP instances and backend services, a main mission
of CDP was to make city council data easier to access in all forms, on the web and programmatically, so included in
this package are objects to do just that; connect and request data from CDP instance databases and file stores
(examples below).

## User Features
* Plain text query for events or minutes items

* [Database schema](https://councildataproject.github.io/cdptools/_images/database_diagram.png) allows for simple querying of:
    * events (meetings)
    * voting history of a city council or city council member
    * bodies (committees)
    * members
    * minutes items
    * event transcripts

* File stores and databases can be used in combination to download audio or the entire transcript of a meeting

## Quickstart
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
**Stable Release:** `pip install cdptools`<br>
**Development Head:** `pip install git+https://github.com/CouncilDataProject/cdptools.git`

#### All City Installation:
`pip install cdptools[all]`

#### Individual City Installation:
* Seattle: `pip install cdptools[google-cloud]`

## Developer Features
* Modular system for gathering city council events, transcribing, and indexing them to make searchable.
* Data pipelines are highly customizable to fit your cities needs.
* Deploy and run pipelines using Docker to ensure your system has everything it needs.

For additional information on system design please refer to our
[documentation](https://CouncilDataProject.github.io/cdptools).

## Documentation
For full package documentation please visit [CouncilDataProject.github.io/cdptools](https://CouncilDataProject.github.io/cdptools).

## Development
See [CONTRIBUTING.md](CONTRIBUTING.md) for information related to developing the code.

**Free software: BSD-3-Clause license**

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter).
