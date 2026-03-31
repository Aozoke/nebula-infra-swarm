import logging
import os

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from psycopg import connect

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("users-api")


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


def ensure_schema() -> None:
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    handle TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS follows (
                    follower_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    followed_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (follower_id, followed_id)
                )
                """
            )
        connection.commit()


@app.on_event("startup")
def startup() -> None:
    ensure_schema()
    logger.info("postgres connected")


class UserCreate(BaseModel):
    handle: str


class FollowChange(BaseModel):
    follower_id: str
    followed_id: str


def parse_user_id(user_id: str) -> int:
    if not user_id.startswith("user-"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    raw_id = user_id.removeprefix("user-")
    if not raw_id.isdigit():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return int(raw_id)


def fetch_user_row(user_db_id: int):
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, handle
                FROM users
                WHERE id = %s
                """,
                (user_db_id,),
            )
            return cursor.fetchone()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "users-api",
    }


@app.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate):
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (handle)
                VALUES (%s)
                ON CONFLICT (handle) DO NOTHING
                RETURNING id, handle
                """,
                (payload.handle,),
            )
            row = cursor.fetchone()
        connection.commit()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Handle already exists",
        )

    return {
        "id": f"user-{row[0]}",
        "handle": row[1],
    }


@app.get("/users/{user_id}")
def get_user(user_id: str):
    row = fetch_user_row(parse_user_id(user_id))

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {
        "id": f"user-{row[0]}",
        "handle": row[1],
    }


@app.post("/follows", status_code=status.HTTP_201_CREATED)
def create_follow(payload: FollowChange):
    follower_db_id = parse_user_id(payload.follower_id)
    followed_db_id = parse_user_id(payload.followed_id)

    if follower_db_id == followed_db_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user cannot follow itself",
        )

    if fetch_user_row(follower_db_id) is None or fetch_user_row(followed_db_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO follows (follower_id, followed_id)
                VALUES (%s, %s)
                ON CONFLICT (follower_id, followed_id) DO NOTHING
                """,
                (follower_db_id, followed_db_id),
            )
        connection.commit()

    return {
        "follower_id": payload.follower_id,
        "followed_id": payload.followed_id,
        "status": "following",
    }


@app.delete("/follows", status_code=status.HTTP_204_NO_CONTENT)
def delete_follow(payload: FollowChange):
    follower_db_id = parse_user_id(payload.follower_id)
    followed_db_id = parse_user_id(payload.followed_id)

    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM follows
                WHERE follower_id = %s AND followed_id = %s
                """,
                (follower_db_id, followed_db_id),
            )
        connection.commit()


@app.get("/internal/ping")
def internal_ping():
    return {
        "status": "ok",
        "service": "users-api",
    }


@app.get("/internal/users/{user_id}/exists")
def user_exists(user_id: str):
    row = fetch_user_row(parse_user_id(user_id))
    return {
        "exists": row is not None,
    }


@app.get("/internal/users/{user_id}/followers")
def get_followers(user_id: str):
    user_db_id = parse_user_id(user_id)

    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT follower_id
                FROM follows
                WHERE followed_id = %s
                ORDER BY follower_id ASC
                """,
                (user_db_id,),
            )
            rows = cursor.fetchall()

    return {
        "followers": [f"user-{row[0]}" for row in rows],
    }
