import redis
import data

redis_conn = redis.Redis(
    host=data.redis_host,
    port=data.redis_port,
    username=data.redis_user,
    password=data.redis_password,
    decode_responses=True
)