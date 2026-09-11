from fastapi import FastAPI
from fastapi.responses import JSONResponse

from crud import (
    create_lobby,
    get_lobby,
    join_lobby,
    leave_lobby,
    set_ready,
    list_open_lobbies,
    get_players,
    NotFoundError,
    LobbyNotFoundError,
    create_lobby_batch
)
from services.lobby.redis_client import redis_client
from models_api import (
    LobbyCreateRequest,
    LobbyJoinRequest,
    ReadyRequest,
    LobbyResponse,
    PlayerResponse,
    LobbyStatus, LobbyBatchCreateRequest
)
from models_store import LobbyRecord, PlayerState

app = FastAPI(title="Lobby Service")

@app.exception_handler(NotFoundError)
async def _handle_not_found(request,exc) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})

# routes
@app.post("/lobbies", response_model=LobbyResponse)
async def create_lobby_route(body: LobbyCreateRequest) -> LobbyResponse:
    lobby_id, record = await create_lobby(body.host_id, body.max_players)
    response = await _record_to_response(record, lobby_id)
    return response

@app.get("/lobbies/{lobby_id}", response_model=LobbyResponse)
async def get_lobby_route(lobby_id: str) -> LobbyResponse:
    lobby = await get_lobby(lobby_id)
    response = await _record_to_response(lobby, lobby_id)
    return response

@app.get("/lobbies", response_model=list[LobbyResponse])
async def list_lobbies_route() -> list[LobbyResponse]:
    lobbies = await list_open_lobbies()
    responses = []
    for lobby_id, record in lobbies:
        responses.append(await _record_to_response(record, lobby_id))
    return responses

@app.post("/lobbies/{lobby_id}/join", response_model=LobbyResponse)
async def join_lobby_route(lobby_id: str, body: LobbyJoinRequest) -> LobbyResponse:
    await join_lobby(lobby_id, body.player_id)
    record = await get_lobby(lobby_id)
    response = await _record_to_response(record, lobby_id)
    return response

@app.post("/lobbies/{lobby_id}/leave")
async def leave_lobby_route(lobby_id: str, body: LobbyJoinRequest):
    await leave_lobby(lobby_id, body.player_id)
    try:
        record = await get_lobby(lobby_id)
    except LobbyNotFoundError:
        return {"lobby_deleted": True}
    response = await _record_to_response(record, lobby_id)
    return response

@app.get("/lobbies/{lobby_id}/players", response_model=list[PlayerResponse])
async def get_players_route(lobby_id: str) -> list[PlayerResponse]:
    players = await get_players(lobby_id)
    responses = []
    for player in players:
        responses.append(await _player_state_to_response(player, lobby_id))

    return responses

@app.post("/lobbies/{lobby_id}/ready", response_model=LobbyResponse)
async def set_ready_route(lobby_id: str, body: ReadyRequest) -> LobbyResponse:
    await set_ready(lobby_id, body.player_id, body.ready)
    record = await get_lobby(lobby_id)
    response = await _record_to_response(record, lobby_id)
    return response

@app.post("/lobbies/batch", response_model=LobbyResponse)
async def create_lobby_batch_route(body: LobbyBatchCreateRequest) -> LobbyResponse:
    lobby_id, record = await create_lobby_batch(body.player_ids, body.max_players)
    response = await _record_to_response(record, lobby_id)
    return response

@app.get("/health")
async def health():
    try:
        await redis_client.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "unreachable"
    return {"service": "lobby", "status": "ok", "redis": redis_status}

# helpers
async def _player_state_to_response(state: PlayerState, lobby_id: str) -> PlayerResponse:
    res=PlayerResponse(
        player_id=state.player_id,
        ready=state.ready,
        joined_at=state.joined_at
    )
    return res

async def _record_to_response(record: LobbyRecord, lobby_id: str) -> LobbyResponse:
    count = await redis_client.scard(f"lobby:{lobby_id}:players")
    res = LobbyResponse(lobby_id=lobby_id,
                        host_id=record.host_id,
                        status=LobbyStatus(record.status),
                        max_players=record.max_players,
                        player_count=count
                        )
    return res