from redis import Redis
from .settings import REDIS_HOST, REDIS_PORT

redis: Redis = Redis(REDIS_HOST, REDIS_PORT, 0, decode_responses=True)
