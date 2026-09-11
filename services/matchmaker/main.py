from fastapi import FastAPI
from fastapi.responses import JSONResponse
from uuid import uuid4
from redis.redis_client import redis_client

from crud import (
    join_queue,
    leave_queue,
    get_queue_position,
    get_queue_size,
    try_form_match,
    create_lobby_for_match,
    PlayerNotInQueueError,
)
from models_api import (
    QueueJoinRequest,
    QueueLeaveRequest,
    QueueStatusRequest,
    MatchResponse,
)

app = FastAPI(title="Matchmaker Service")

@app.exception_handler(PlayerNotInQueueError)
async def _handle_not_in_queue(request, exc) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})

# routes
@app.post("/queue/join")
async def join_queue_route(body: QueueJoinRequest):
    await join_queue(body.player_id)
    matched_players = await try_form_match()
    if matched_players is not None:
        lobby_id = await create_lobby_for_match(matched_players)
        return MatchResponse(match_id=str(uuid4()), player_ids=matched_players, lobby_id=lobby_id)
    else:
        return await _build_status_response(body.player_id)

@app.post("/queue/leave")
async def leave_queue_route(body: QueueLeaveRequest):
    await leave_queue(body.player_id)
    return {"player_id": body.player_id, "left_queue": True}

@app.get("/queue/status/{player_id}", response_model=QueueStatusRequest)
async def get_queue_status_route(player_id: str) -> QueueStatusRequest:
    return await _build_status_response(player_id)

@app.get("/health")
async def health():
    try:
        await redis_client.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "unreachable"
    return {"service": "matchmaker", "status": "ok", "redis": redis_status}

# helpers
async def _build_status_response(player_id: str) -> QueueStatusRequest:
    position = await get_queue_position(player_id)
    size = await get_queue_size()
    return QueueStatusRequest(player_id=player_id, position=position, players_in_queue=size)

