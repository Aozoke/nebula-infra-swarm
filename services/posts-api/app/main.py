import json
import logging
import os

import httpx
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from psycopg import connect
from redis import Redis

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("posts-api")


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
                CREATE TABLE IF NOT EXISTS posts (
                    id BIGSERIAL PRIMARY KEY,
                    author_id BIGINT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        connection.commit()


def users_api_base_url() -> str:
    return os.getenv("USERS_API_BASE_URL", "http://users-api:8000")


def redis_stream_name() -> str:
    return os.getenv("REDIS_STREAM_NAME", "nebula.events")


def check_author_exists(author_id: str) -> bool:
    url = f"{users_api_base_url()}/internal/users/{author_id}/exists"

    try:
        response = httpx.get(url, timeout=5.0)
    except httpx.HTTPError as exc:
        logger.exception("users-api call failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="users-api unreachable",
        ) from exc

    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="users-api returned an unexpected response",
        )

    payload = response.json()
    logger.info("users-api exists check completed for %s", author_id)
    return payload.get("exists", False)


def publish_post_created_event(post_id: str, author_id: str, content: str) -> None:
    payload = json.dumps(
        {
            "post_id": post_id,
            "author_id": author_id,
            "content": content,
        }
    )

    try:
        get_redis_client().xadd(
            redis_stream_name(),
            {
                "type": "post.created",
                "payload": payload,
            },
        )
    except Exception as exc:
        logger.exception("redis stream publish failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="redis unavailable",
        ) from exc

    logger.info("event pushed to stream %s", redis_stream_name())


@app.on_event("startup")
def startup() -> None:
    ensure_schema()
    logger.info("postgres connected")
    get_redis_client().ping()
    logger.info("redis connected")


class PostCreate(BaseModel):
    author_id: str
    content: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "posts-api",
    }


@app.post("/posts", status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate):
    if not check_author_exists(payload.author_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found",
        )

    raw_author_id = payload.author_id.removeprefix("user-")

    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO posts (author_id, content)
                VALUES (%s, %s)
                RETURNING id, author_id, content
                """,
                (int(raw_author_id), payload.content),
            )
            row = cursor.fetchone()
        connection.commit()

    post_id = f"post-{row[0]}"
    author_id = f"user-{row[1]}"
    publish_post_created_event(post_id, author_id, row[2])

    return {
        "id": post_id,
        "author_id": author_id,
        "content": row[2],
    }
