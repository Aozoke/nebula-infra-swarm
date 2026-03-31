import json
import logging
import os
import time

from psycopg import connect
from redis import Redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("feed-worker")


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


def ensure_schema() -> None:
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS feed_events (
                    id BIGSERIAL PRIMARY KEY,
                    post_id TEXT NOT NULL,
                    author_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        connection.commit()


def store_feed_event(post_id: str, author_id: str, content: str) -> None:
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO feed_events (post_id, author_id, content)
                VALUES (%s, %s, %s)
                """,
                (post_id, author_id, content),
            )
        connection.commit()


def main() -> None:
    ensure_schema()
    logger.info("postgres connected")

    redis_client = get_redis_client()
    redis_client.ping()
    logger.info("redis connected")

    stream_name = os.getenv("REDIS_STREAM_NAME", "nebula.events")
    last_id = "0-0"

    logger.info("listening on stream %s", stream_name)

    while True:
        entries = redis_client.xread(
            {stream_name: last_id},
            block=5000,
            count=10,
        )

        if not entries:
            continue

        for _, messages in entries:
            for message_id, fields in messages:
                last_id = message_id

                event_type = fields.get("type")
                if event_type != "post.created":
                    logger.info("ignored event type %s", event_type)
                    continue

                raw_payload = fields.get("payload")
                if not raw_payload:
                    logger.warning("event %s has no payload", message_id)
                    continue

                payload = json.loads(raw_payload)
                post_id = payload["post_id"]
                author_id = payload["author_id"]
                content = payload["content"]

                logger.info("event received post.created for %s", post_id)
                store_feed_event(post_id, author_id, content)
                logger.info("feed event stored for %s", post_id)


if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception:
            logger.exception("feed-worker crashed, retrying")
            time.sleep(5)
