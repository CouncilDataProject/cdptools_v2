from datetime import datetime
from typing import NamedTuple, Optional


class MinimalEventData(NamedTuple):
    body: str
    event_datetime: datetime
    video_uri: str
    caption_uri: Optional[str]
    external_source_id: Optional[str]
