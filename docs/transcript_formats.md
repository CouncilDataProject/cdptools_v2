# Transcript Format
### Index
1. [Introduction](#introduction)
2. [Formats](#formats)
    1. [Raw](#format:-raw)
    2. [Timestamped Words](#format:-timestamped-words)
    3. [Timestamped Sentences](#format:-timestamped-sentences)
3. [Notes](#notes)

---
## Introduction
Modularity and customization of CDP instances is a core goal of the entire project, it can lead to downstream problems
if outputs do not follow specified formats. A core output of a CDP instance is the produced transcript(s) for an event.
Because multiple pipelines and tasks in each pipeline need to interact with these transcripts it is best to have
specific formats for how they can be stored for interoperability with other modules.

---
## Formats
The basic layout of a format currently for CDP instances will be the following JSON block:
```json
{
    "format": "{TRANSCRIPT_FORMAT_TYPE}",
    "annotations": [
        {}
    ],
    "confidence": 0.0,
    "data": [
        {
            "start_time": 0.0,
            "text": "{TRANSCRIPT_TEXT_PORTION}",
            "end_time": 2.6
        }
    ]
}
```

All variants will be only slightly different from this and the following sections explain how.

### Format: Raw
The most basic transcript format. It has the core information of `format`, `annotations`, and `confidence`, but it's
`data` section is simply the entire transcript dumped into a single text block.

### Format: Timestamped Words
Currently the most expansive transcript format. As with all formats it has the basic `format`, `annotations`, and
`confidence`, but, unlike `format: raw` it's `data` portion is a large list where each `text` portion of each
dictionary in the list is only a single word (including any punctuation returned from the model).

### Format: Timestamped Sentences
A middle ground between `format: raw` and `format: timestamped-words`. Like all, it has the basic `format`,
`annotations`, and `confidence`. However, to facilitate the development of speaker turn taking annotations (which
happen on a sentence level), ten `data` portion is a large list where each `text` portion of each dictionary in the list
is a single sentence (including any punctuation returned from the model).

---
## Notes
The `EventGatherPipeline` will set the "primary" transcript for each event gathered to `timestamped-sentences` if
available. If `timestamped-sentences` was not returned by the speech recognition model in the outputs object, it will
then choose, `timestamped-words`. Again if `timestamped-words` is not available, it will default to `raw` which should
always be available regardless of which speech recognition model you choose or create.
