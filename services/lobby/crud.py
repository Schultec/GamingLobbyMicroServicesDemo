from uuid import uuid4
from datetime import datetime
from redis.redis_client import redis_client
from models_store import LobbyRecord, PlayerState
from models_api import LobbyStatus
import dataclasses

# exceptions
class NotFoundError(Exception): pass
class LobbyNotFoundError(NotFoundError): pass
class PlayerNotFoundError(NotFoundError): pass

# Crud
async def create_lobby(host_id: str, max_players: int) -> tuple[str, LobbyRecord]:
    lobby_id = str(uuid4())
    record = LobbyRecord(host_id,LobbyStatus.OPEN.value, max_players, datetime.now())
    record_dict = _lobby_record_to_redis_dict(record)
    await redis_client.hset(f"lobby:{lobby_id}", mapping=record_dict)
    await join_lobby(lobby_id, host_id)
    await redis_client.sadd("lobbies:open", lobby_id)
    return lobby_id, record

async def join_lobby(lobby_id: str, player_id: str) -> None:
    lobby = await get_lobby(lobby_id)
    player = PlayerState(player_id, False, datetime.now())
    player_dict = _player_state_to_redis_dict(player)
    await redis_client.hset(f"lobby:{lobby_id}:player:{player_id}", mapping=player_dict)
    await redis_client.sadd(f"lobby:{lobby_id}:players", player_id)

async def get_lobby(lobby_id: str) -> LobbyRecord:
    data = await redis_client.hgetall(f"lobby:{lobby_id}")
    if not data:
        raise LobbyNotFoundError
    record = _redis_dict_to_lobby_record(data)
    return record

async def get_players(lobby_id: str) -> list[PlayerState]:
    lobby = await get_lobby(lobby_id)
    data = await redis_client.smembers(f"lobby:{lobby_id}:players")
    players = []
    for player_id in data:
        player = await redis_client.hgetall(f"lobby:{lobby_id}:player:{player_id}")
        players.append(_redis_dict_to_player_state(player))
    return players

async def set_ready(lobby_id: str, player_id: str, ready: bool) -> None:
    record = await get_lobby(lobby_id)
    data = await redis_client.hgetall(f"lobby:{lobby_id}:player:{player_id}")
    if not data:
        raise PlayerNotFoundError
    await redis_client.hset(f"lobby:{lobby_id}:player:{player_id}", "ready", str(ready))

async def list_open_lobbies() -> list[tuple[str, LobbyRecord]]:
    data = await redis_client.smembers("lobbies:open")
    lobbies = []
    for lobby_id in data:
        lobby = await redis_client.hgetall(f"lobby:{lobby_id}")
        if not lobby:
            raise LobbyNotFoundError
        lobbies.append((lobby_id, _redis_dict_to_lobby_record(lobby)))
    return lobbies

async def leave_lobby(lobby_id: str, player_id: str) -> None:
    lobby = await get_lobby(lobby_id)
    data = await redis_client.hgetall(f"lobby:{lobby_id}:player:{player_id}")
    if not data:
        raise PlayerNotFoundError
    await redis_client.delete(f"lobby:{lobby_id}:player:{player_id}")
    await redis_client.srem(f"lobby:{lobby_id}:players", player_id)
    remaining = await get_players(lobby_id)
    if not remaining:
        await redis_client.delete(f"lobby:{lobby_id}")
        await redis_client.srem(f"lobbies:open", lobby_id)
        return
    if player_id == lobby.host_id:
        sorted_remaining = sorted(remaining, key=lambda player: player.joined_at)
        lobby.host_id = sorted_remaining[0].player_id
    if lobby.status == LobbyStatus.FULL.value:
        lobby.status = LobbyStatus.OPEN.value
    updated_dict = _lobby_record_to_redis_dict(lobby)
    await redis_client.hset(f"lobby:{lobby_id}", mapping=updated_dict)

async def create_lobby_batch(player_ids: list[str], max_players: int) -> tuple[str, LobbyRecord]:
    host_id = player_ids[0]
    lobby_id = str(uuid4())
    record = LobbyRecord(host_id,LobbyStatus.OPEN.value, max_players, datetime.now())
    record_dict = _lobby_record_to_redis_dict(record)
    await redis_client.hset(f"lobby:{lobby_id}", mapping=record_dict)
    await join_lobby(lobby_id, host_id)
    await redis_client.sadd("lobbies:open", lobby_id)
    for player_id in player_ids[1:]:
        await join_lobby(lobby_id, player_id)
    return lobby_id, record


# helpers
def _lobby_record_to_redis_dict(record: LobbyRecord) -> dict[str, str]:
    d = dataclasses.asdict(record)
    d['max_players'] = str(d['max_players'])
    d['created_at'] = d['created_at'].isoformat()
    return d

def  _redis_dict_to_lobby_record(data: dict[str, str]) -> LobbyRecord:
    r = LobbyRecord(data['host_id'], data['status'], int(data['max_players']), datetime.fromisoformat(data['created_at']))
    return r

def _player_state_to_redis_dict(state: PlayerState) -> dict[str, str]:
    d = dataclasses.asdict(state)
    d['ready'] = str(d['ready'])
    d['joined_at'] = d['joined_at'].isoformat()
    return d

def _redis_dict_to_player_state(data: dict[str, str]) -> PlayerState:
    bool_map = {"true": True, "false": False}
    is_true = bool_map.get(data['ready'].strip().lower(), False)
    r = PlayerState(data['player_id'], is_true, datetime.fromisoformat(data['joined_at']))
    return r

# TODO: leave_lobby(lobby_id: str, player_id: str) -> None
#   raises LobbyNotFoundError if lobby or player not found
#   if leaving player is host, auto-promote another player to host_id