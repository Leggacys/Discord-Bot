from sqlalchemy import select

from database.database import SessionLocal
from database.models.user_model import User


def get_user(
    discord_user_id: int,
) -> User | None:
    with SessionLocal() as session:
        return session.scalar(
            select(User)
            .where(
                User.discord_user_id
                == discord_user_id
            )
        )


def get_daily_gaming_limit(
    discord_user_id: int,
) -> int | None:
    """
    Return the user's daily gaming limit
    in minutes.

    Returns None if:
    - the user does not exist
    - the user has no limit configured
    """

    with SessionLocal() as session:
        user = session.get(
            User,
            discord_user_id,
        )

        if user is None:
            return None

        return user.daily_gaming_limit_minutes


def set_daily_gaming_limit(
    *,
    discord_user_id: int,
    minutes: int,
) -> bool:
    """
    Set the user's daily gaming limit.

    Returns False if the user does not exist.
    """

    if minutes <= 0:
        raise ValueError(
            "Gaming limit must be greater than 0."
        )

    with SessionLocal() as session:
        user = session.get(
            User,
            discord_user_id,
        )

        if user is None:
            return False

        user.daily_gaming_limit_minutes = minutes

        session.commit()

        return True


def remove_daily_gaming_limit(
    discord_user_id: int,
) -> bool:
    """
    Remove the user's daily gaming limit.

    Returns False if the user does not exist.
    """

    with SessionLocal() as session:
        user = session.get(
            User,
            discord_user_id,
        )

        if user is None:
            return False

        user.daily_gaming_limit_minutes = None

        session.commit()

        return True


def get_users_with_gaming_limits() -> list[dict]:
    """
    Return all users that have configured
    a daily gaming limit.

    Useful later for automatic limit warnings.
    """

    with SessionLocal() as session:
        users = session.scalars(
            select(User)
            .where(
                User.daily_gaming_limit_minutes
                .is_not(None)
            )
        ).all()

        return [
            {
                "discord_user_id":
                    user.discord_user_id,

                "username":
                    user.username,

                "display_name":
                    user.display_name,

                "daily_gaming_limit_minutes":
                    user.daily_gaming_limit_minutes,
            }
            for user in users
        ]