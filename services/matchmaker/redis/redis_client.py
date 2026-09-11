import os
import redis.asyncio as redis

REDIS_HOST = os.getenv("REDIS_HOST", "my-redis-service")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)