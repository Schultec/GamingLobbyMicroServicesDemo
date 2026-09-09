from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class LobbyStatus(str, Enum):
    OPEN = "OPEN"
    FULL = "FULL"
    IN_PROGRESS = "IN_PROGRESS"

class LobbyCreateRequest(BaseModel):
    host_id: str
    max_players: int = Field(gt=0, le=10)

class LobbyJoinRequest(BaseModel):
    player_id: str

class ReadyRequest(BaseModel):
    player_id: str
    ready: bool

class LobbyResponse(BaseModel):
    lobby_id: str
    host_id: str
    status: LobbyStatus
    max_players: int
    player_count: int

class PlayerResponse(BaseModel):
    player_id: str
    ready: bool
    joined_at: datetime