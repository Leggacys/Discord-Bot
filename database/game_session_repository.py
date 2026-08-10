from datetime import datetime, timezone

from sqlalchemy import select

from database.database import SessionLocal
from database.models.game_session_model import GameSession
from database.models.user_model import User


def ensure_user(
    discord_user_id: int,
    username: str,
    display_name: str | None,
):
    with SessionLocal() as session:
        user = session.get(User, discord_user_id)

        if user is None:
            user = User(
                discord_user_id=discord_user_id,
                username=username,
                display_name=display_name,
            )

            session.add(user)

        else:
            user.username = username
            user.display_name = display_name

        session.commit()


def start_session(
    discord_user_id: int,
    game_name: str,
):
    with SessionLocal() as session:
        existing = session.scalar(
            select(GameSession)
            .where(
                GameSession.discord_user_id == discord_user_id,
                GameSession.game_name == game_name,
                GameSession.ended_at.is_(None),
            )
            .limit(1)
        )

        if existing:
            return

        game_session = GameSession(
            discord_user_id=discord_user_id,
            game_name=game_name,
            started_at=datetime.now(timezone.utc),
        )

        session.add(game_session)
        session.commit()


def stop_session(
    discord_user_id: int,
    game_name: str,
):
    with SessionLocal() as session:
        game_session = session.scalar(
            select(GameSession)
            .where(
                GameSession.discord_user_id == discord_user_id,
                GameSession.game_name == game_name,
                GameSession.ended_at.is_(None),
            )
            .order_by(GameSession.started_at.desc())
            .limit(1)
        )

        if game_session is None:
            return

        now = datetime.now(timezone.utc)

        game_session.ended_at = now
        game_session.duration_seconds = max(
            0,
            int(
                (
                    now - game_session.started_at
                ).total_seconds()
            ),
        )

        session.commit()


def get_sessions_between(
    discord_user_id: int,
    start: datetime,
    end: datetime,
):
    with SessionLocal() as session:
        sessions = session.scalars(
            select(GameSession)
            .where(
                GameSession.discord_user_id == discord_user_id,
                GameSession.started_at >= start,
                GameSession.started_at < end,
            )
            .order_by(GameSession.started_at.desc())
        ).all()

        return list(sessions)