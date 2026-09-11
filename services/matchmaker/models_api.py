from pydantic import BaseModel


class QueueJoinRequest(BaseModel):
    player_id: str

class QueueLeaveRequest(BaseModel):
    player_id: str

class QueueStatusRequest(BaseModel):
    player_id: str
    position: int
    players_in_queue: int

class MatchResponse(BaseModel):
    match_id: str
    player_ids: list[str]
    lobby_id: str
