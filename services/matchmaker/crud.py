from uuid import uuid4
from datetime import datetime
from redis.redis_client import redis_client
from models_store import QueueEntry, MatchRecord
import dataclasses
import httpx


PLAYERS_PER_MATCH = 10
LOBBY_SERVICE_URL = "http://lobby:8081"

# Exceptions
class PlayerNotInQueueError(Exception): pass

# Crud
async def join_queue(player_id: str) -> None:
    score = datetime.now().timestamp()
    await redis_client.zadd("matchmaking:queue", {player_id: score})

async def leave_queue(player_id: str) -> None:
    record = await redis_client.zrem("matchmaking:queue", player_id)
    if record == 0:
        raise PlayerNotInQueueError

async def get_queue_position(player_id: str) -> int:
    rank  = await redis_client.zrank("matchmaking:queue", player_id)
    if rank is None:
        raise PlayerNotInQueueError
    return rank

async def get_queue_size() -> int:
    count = await redis_client.zcard("matchmaking:queue")
    return count

async def try_form_match() -> list[str] | None:
    size = await get_queue_size()
    if size < PLAYERS_PER_MATCH:
        return None
    players = await redis_client.zrange("matchmaking:queue", 0, PLAYERS_PER_MATCH -1)
    await redis_client.zrem("matchmaking:queue", *players)
    return players

async def create_lobby_for_match(player_ids: list[str]) -> str:
    payload = {"player_ids": player_ids, "max_players": PLAYERS_PER_MATCH}
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{LOBBY_SERVICE_URL}/lobbies/batch", json=payload)
    data = response.json()
    lobby_id = data["lobby_id"]
    return lobby_id