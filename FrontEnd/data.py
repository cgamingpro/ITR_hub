import os

# job api usr

API2URL = os.getenv("TASKS_API_URL", "http://localhost:8080/job")

# =========================
# PostgreSQL config
# =========================

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Railway deployment
    import urllib.parse as urlparse

    url = urlparse.urlparse(DATABASE_URL)

    host = url.hostname
    database = url.path[1:]
    user = url.username
    password = url.password
    port = url.port
else:
    # Local dev
    from local_config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

    host = DB_HOST
    port = DB_PORT
    database = DB_NAME
    user = DB_USER
    password = DB_PASSWORD


# =========================
# Redis connection
# =========================

REDIS_URL = os.getenv("REDIS_URL")

if REDIS_URL:
    # Railway Redis
    redis_url = urlparse.urlparse(REDIS_URL)

    redis_host = redis_url.hostname
    redis_port = redis_url.port
    redis_user = redis_url.username
    redis_password = redis_url.password

else:
    # Local Redis
    redis_host = "localhost"
    redis_port = 6379
    redis_user = None
    redis_password = None