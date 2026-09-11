from datetime import datetime
from dataclasses import dataclass
from typing import List


@dataclass
class QueueEntry:
    player_id: str
    queued_at: datetime

@dataclass
class MatchRecord:
    match_id: str
    player_ids: List[str]
    lobby_id: str
    created_at: datetime