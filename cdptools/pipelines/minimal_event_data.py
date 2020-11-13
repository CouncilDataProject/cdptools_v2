from datetime import datetime
from typing import NamedTuple, Optional, List


class MinimalSessionData(NamedTuple):
    session_datetime: datetime
    session_index: int
    video_uri: str
    caption_uri: Optional[str]
    external_source_id: Optional[str]


class MinimalEventData(NamedTuple):
    body: str
    event_datetime: datetime
    sessions: List[MinimalSessionData]
    external_source_id: Optional[str]


class MinimalEventAndSessionData(NamedTuple):
    body: str
    session_datetime: datetime
    session_index: int
    video_uri: str
    session_id: str
    linked_session_id: str
    caption_uri: Optional[str]
    external_source_id: Optional[str]
