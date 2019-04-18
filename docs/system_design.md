# Backend Design
### Index
1. [Introduction](#introduction)
2. [Modules](#modules)
    1. [Event Scrapers](#event-scrapers)
    2. [File Stores](#file-stores)
    3. [Audio Splitters](#audio-splitters)
    4. [Databases](#databases)
        * [Database Schema Diagram](#database-schema-diagram)
    5. [Speech Recognition Models](#speech-recognition-models)
    6. [Pipelines](#pipelines)
3. [Why not Airflow?](#why-not-airflow)

---
## Introduction
Council Data Project tools are built with a goal of being both extremely modular (to a limit) and easy to deploy.
There are a few core components which will be discussed in the [modules](#modules) section next, but in short, if the
mission of Council Data Project is to make city council activities more transparent and discoverable, it is
unsustainable to build an entirely new system for each city government we want to produce data and analysis for. By
trying to make components modular, customizable, and most importantly, reusable across cities, it may be possible to
make systems like CDP, sustainable. However, there is always going to be an inherent fear of "customization introducing
complexity". Which leads us to the question:

> *How much customization is understandable and deployable for a non CDP-dev?*

This design document/ spec/ whatever you want to call it will go over the basics of how designs for new modules should
be scrutinized and in turn, built and deployed. From the basics of data gathering, to data storage, and finally,
data analysis.

---
## Modules
As stated previously, CDP is an attempt to make a data analysis and activity discovery system for any city government.
Because of this, we must use customizable modules to have a a chance at sustainability of a code base. This next
section will go over the basics of the major components developed thus far. Each module type will have what other
languages would call an [interface](https://www.w3schools.com/java/java_interface.asp) but in Python, to my knowledge,
are most related to [abstract base classes](https://docs.python.org/3/library/abc.html). These layout the "must have"
functions and properties that each module type must have. Anything else a deployed module has is just icing on the cake!
And if each module has all the properties and functions of the abstract base class, the modules *should* be
interoperable with one another. For example: If you want to use a local system file store, use the
`file_stores.AppDirsFileStore`, but, if you want to store your files with Google Cloud Storage, use the
`file_stores.GCSFileStores`.

### Event Scrapers
Event scrapers are likely going to be the most varied from one another as they each are simply a method of retrieved
data about city council activities and formatting that data into a format expected by the rest of the system. For cities
fortunate enough to have all data required for CDP processing to be completed available on Legistar: great, write a
LegistarEventScraper. However, some cities don't have all the required data available on Legistar; Seattle for example
actually has *most* of the data CDP systems need on the cities broadcasting website
[seattlechannel.org](http://www.seattlechannel.org). The remaining data can be retrieved by querying very specific
Legistar endpoints. Because of this, the `event_scrapers.SeattleEventScraper` uses a mix of web scraping and JSON
requests.

**To sum up:** Event scrapers are a module usually tailored for each city, unless they have the Legistar data easily
accessible, that retrieves the data and formats it into a system wide expectation of what event data should look like.

### File Stores
File stores are largely wrappers around other already well known file storage solutions. `file_stores.AppDirsFileStore`
uses a method of using the SHA256 hash of a files bytes to generate a storage location and id for the file.
On the other end of the spectrum, `file_stores.GCSFileStore` really is just a simple wrapper around Google Cloud
Storage to make their functions fit nicely with the rest of the processing stack for CDP. Choosing a file store really
comes down to your choice in other modules, for Seattle, the stack is entirely Google services based, so using the
`file_stores.GCSFileStore` makes sense. If you have enough storage and compute on your local machine though, it may be
best to run a docker container for you database, and use `file_stores.AppDirsFileStore` for storage, and a locally
trained speech recognition model for processing. Choose what works best for you. They all should work together thanks
to the shared spec. For the sake of transparency, it is recommended that file stores be open read, understandably,
`file_stores.AppDirsFileStore` will probably never be open read as it is entirely about storing files on the local
machine.

### Audio Splitters
Being honest, I assume there will only ever be one audio splitter module. `FFmpeg` is the defacto standard for video and
audio format processing. In the case others want to use a different audio splitter, the module specification is
available.

### Databases
Much like file stores, CDP attempts to make enough abstraction on the module level for any database to be used. The
schema diagram linked below is an example of this, while the diagram is relational, Seattle use Firebase's Cloud
Firestore which is a NoSQL Document Store. As long the modules api delivers data in a manner that is consistent with the
schema, there will be no issues with downstream processing. Similar to file stores, databases are also recommended to be
open read, as if collaborators want to use the data stored by a CDP instance, it makes it easy for them to do so. Just
ask them nicely to not slam the database with requests.

[Database Schema Diagram](resources/database_diagram.pdf)
*Created with dbdiagram.io*

### Speech Recognition Model
Things can start to get tricky here. Speech recognition models are where the standard idea of processing may be a bit
odd. Let's compare a city like Seattle which doesn't produce transcripts of city council meetings to an unnamed city
that does. The speech recognition model available for Seattle, is the `sr_models.GoogleCloudSRModel`, which accepts
a URI to an audio file, and returns a saved transcript text local path. However, if your city already produces
transcripts for city council meetings, maybe you will write a module that simply takes an audio URI and requests the
already high quality transcript back, no need for any processing. These are both valid speech recognition models, it's
simply that one of them produces transcripts that have 100% confidence.

### Pipelines
Finally we arrive at pipelines. Pipelines should, similarly to modules, follow the `pipelines.Pipeline` abstract base
class specification, but they really simply are just a task graph that gets carried out with each task being one of the
modules already defined. Commonly, a pipeline like these is called a "DAG", or "Directed Acyclic Graph". This style of
managing task graphs has been made popular by tools like [Apache Airflow](https://github.com/apache/airflow). Pipeline
configuration files that dictate which modules to use and any extra arguments needed to be passed to them then allow the
entire pipeline to run.

## Why not Airflow
Circling back to the original intent of these tools: CDP aims to be high modular, and still reusable by nearly every
city. However, if individuals who want to see data for their own city council can't set up Airflow, and don't have a
computation cluster to support it's operations, then what is the point of making the system modular? So yes, while many
CDP operations could be very efficiently handled by Airflow, ease of use is also a factor and until we dedicate time to
wrapping all the processes and pipelines in as easy to use configuration files tailored for Airflow, this is the format
we are going with for now. Contributions welcome on that front though.
---

Now go make transparency research happen.
