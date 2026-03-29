import redis
import data

redis_conn = redis.Redis(
    host=data.host,
    port=data.port,
    decode_responses=True
)