from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from database.database import SessionLocal
from database.models.game_session_model import GameSession
from database.models.steam_tracking_state_model import SteamTrackingState
from database.models.user_model import User


def get_users_with_steam_id() -> list[dict]:
    with SessionLocal() as session:
        users = session.scalars(
            select(User)
            .where(
                User.steam_id.is_not(None)
            )
        ).all()

        return [
            {
                "discord_user_id": user.discord_user_id,
                "username": user.username,
                "display_name": user.display_name,
                "steam_id": user.steam_id,
            }
            for user in users
        ]


def get_tracking_playtime(
    discord_user_id: int,
    steam_app_id: int,
) -> int | None:
    with SessionLocal() as session:
        state = session.scalar(
            select(SteamTrackingState)
            .where(
                SteamTrackingState.discord_user_id
                == discord_user_id,
                SteamTrackingState.steam_app_id
                == steam_app_id,
            )
            .limit(1)
        )

        if state is None:
            return None

        return state.playtime_minutes


def upsert_tracking_state(
    *,
    discord_user_id: int,
    steam_app_id: int,
    game_name: str,
    playtime_minutes: int,
) -> None:
    with SessionLocal() as session:
        state = session.scalar(
            select(SteamTrackingState)
            .where(
                SteamTrackingState.discord_user_id
                == discord_user_id,
                SteamTrackingState.steam_app_id
                == steam_app_id,
            )
            .limit(1)
        )

        now = datetime.now(timezone.utc)

        if state is None:
            state = SteamTrackingState(
                discord_user_id=discord_user_id,
                steam_app_id=steam_app_id,
                game_name=game_name,
                playtime_minutes=playtime_minutes,
                checked_at=now,
            )

            session.add(state)

        else:
            state.game_name = game_name
            state.playtime_minutes = playtime_minutes
            state.checked_at = now

        session.commit()


def set_user_steam_id(
    discord_user_id: int,
    steam_id: str,
) -> bool:
    with SessionLocal() as session:
        user = session.get(
            User,
            discord_user_id,
        )

        if user is None:
            return False

        user.steam_id = steam_id

        session.commit()

        return True


def remove_user_steam_id(
    discord_user_id: int,
) -> bool:
    with SessionLocal() as session:
        user = session.get(
            User,
            discord_user_id,
        )

        if user is None:
            return False

        user.steam_id = None

        session.commit()

        return True

def create_steam_session(
    *,
    discord_user_id: int,
    game_name: str,
    duration_seconds: int,
):
    if duration_seconds <= 0:
        return

    now = datetime.now(timezone.utc)

    started_at = now - timedelta(
        seconds=duration_seconds
    )

    with SessionLocal() as session:
        game_session = GameSession(
            discord_user_id=discord_user_id,
            game_name=game_name,
            started_at=started_at,
            ended_at=now,
            duration_seconds=duration_seconds,
            source="steam",
        )

        session.add(game_session)
        session.commit()