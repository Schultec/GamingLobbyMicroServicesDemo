from datetime import datetime
from dataclasses import dataclass


@dataclass
class LobbyRecord:
    host_id: str
    status: str
    max_players: int
    created_at: datetime

@dataclass
class PlayerState:
    player_id: str
    ready: bool
    joined_at: datetime