import sqlite3
from datetime import datetime, timezone

DB_PATH = "gaming_tracker.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS game_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_user_id INTEGER NOT NULL,
                game_name TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                duration_seconds INTEGER
            )
            """
        )


def start_session(discord_user_id: int, game_name: str):
    now = datetime.now(timezone.utc)

    with get_connection() as connection:
        existing = connection.execute(
            """
            SELECT id
            FROM game_sessions
            WHERE discord_user_id = ?
              AND game_name = ?
              AND ended_at IS NULL
            LIMIT 1
            """,
            (discord_user_id, game_name),
        ).fetchone()

        if existing:
            return

        connection.execute(
            """
            INSERT INTO game_sessions (
                discord_user_id,
                game_name,
                started_at
            )
            VALUES (?, ?, ?)
            """,
            (
                discord_user_id,
                game_name,
                now.isoformat(),
            ),
        )


def stop_session(discord_user_id: int, game_name: str):
    now = datetime.now(timezone.utc)

    with get_connection() as connection:
        session = connection.execute(
            """
            SELECT id, started_at
            FROM game_sessions
            WHERE discord_user_id = ?
              AND game_name = ?
              AND ended_at IS NULL
            ORDER BY started_at DESC
            LIMIT 1
            """,
            (discord_user_id, game_name),
        ).fetchone()

        if not session:
            return

        started_at = datetime.fromisoformat(session["started_at"])

        duration_seconds = int(
            (now - started_at).total_seconds()
        )

        connection.execute(
            """
            UPDATE game_sessions
            SET ended_at = ?,
                duration_seconds = ?
            WHERE id = ?
            """,
            (
                now.isoformat(),
                duration_seconds,
                session["id"],
            ),
        )


def get_sessions_between(
    discord_user_id: int,
    start: datetime,
    end: datetime,
):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                game_name,
                started_at,
                ended_at,
                duration_seconds
            FROM game_sessions
            WHERE discord_user_id = ?
              AND started_at >= ?
              AND started_at < ?
            ORDER BY started_at DESC
            """,
            (
                discord_user_id,
                start.isoformat(),
                end.isoformat(),
            ),
        ).fetchall()

    return rows