from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base

if TYPE_CHECKING:
    from .game_session_model import GameSession
    from .steam_tracking_state_model import SteamTrackingState


class User(Base):
    __tablename__ = "users"

    discord_user_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    display_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    steam_id: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
        index=True,
    )

    daily_gaming_limit_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    sessions: Mapped[list["GameSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    steam_tracking_states: Mapped[list["SteamTrackingState"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )