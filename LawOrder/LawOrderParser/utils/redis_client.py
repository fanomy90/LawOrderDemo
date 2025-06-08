import redis
import os

# redis_client = redis.StrictRedis(
#     host=os.getenv("REDIS_HOST", "redis"),
#     port=int(os.getenv("REDIS_PORT", 6379)),
#     db=int(os.getenv("REDIS_DB", 0)),
#     decode_responses=True
# )

redis_client = redis.StrictRedis(
    host='redis',
    port=6379,
    db=0,
    decode_responses=True
)