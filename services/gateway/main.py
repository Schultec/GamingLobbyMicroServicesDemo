import os

import redis.asyncio as redis
from fastapi import FastAPI

app = FastAPI(title="Gateway Service")

REDIS_HOST = os.getenv("REDIS_HOST", "my-redis-service")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


@app.get("/health")
async def health():
    try:
        await redis_client.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "unreachable"
    return {"service": "gateway", "status": "ok", "redis": redis_status}


# TODO: proxy client requests to lobby/matchmaker over the internal network,
# and/or fan out WebSocket events sourced from redis pub/sub.
