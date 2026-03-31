import json
import logging
import os

from fastapi import FastAPI
from psycopg import connect
from redis import Redis

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("feed-api")


def read_db_password() -> str:
    password_file = os.getenv("DATABASE_PASSWORD_FILE")
    if not password_file:
        raise RuntimeError("DATABASE_PASSWORD_FILE is not configured")

    with open(password_file, "r", encoding="utf-8") as secret_file:
        return secret_file.read().strip()


def get_db_connection():
    return connect(
        host=os.getenv("DATABASE_HOST", "postgres"),
        port=os.getenv("DATABASE_PORT", "5432"),
        dbname=os.getenv("DATABASE_NAME", "nebula"),
        user=os.getenv("DATABASE_USER", "nebula"),
        password=read_db_password(),
    )


def get_redis_client() -> Redis:
    return Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        decode_responses=True,
    )


def feed_cache_ttl() -> int:
    return int(os.getenv("FEED_CACHE_TTL", "30"))


@app.on_event("startup")
def startup() -> None:
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    logger.info("postgres connected")
    get_redis_client().ping()
    logger.info("redis connected")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "feed-api",
    }


def load_feed_items():
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, post_id, author_id, content, created_at
                FROM feed_events
                ORDER BY id DESC
                LIMIT 20
                """
            )
            rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "post_id": row[1],
            "author_id": row[2],
            "content": row[3],
            "created_at": row[4].isoformat(),
        }
        for row in rows
    ]


@app.get("/feed/{user_id}")
def get_feed(user_id: str):
    redis_client = get_redis_client()
    cache_key = f"feed:user:{user_id}"

    try:
        cached_payload = redis_client.get(cache_key)
        if cached_payload:
            logger.info("cache hit for %s", user_id)
            return json.loads(cached_payload)
    except Exception:
        logger.exception("redis read failed, falling back to postgres")

    items = load_feed_items()
    payload = {
        "user_id": user_id,
        "items": items,
    }

    try:
        redis_client.setex(cache_key, feed_cache_ttl(), json.dumps(payload))
        logger.info("cache miss for %s, cached %s items", user_id, len(items))
    except Exception:
        logger.exception("redis write failed, returning uncached response")

    logger.info("feed returned for %s with %s items", user_id, len(items))

    return payload
