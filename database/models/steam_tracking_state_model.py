from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .user_model import User


class SteamTrackingState(Base):
    __tablename__ = "steam_tracking_states"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    discord_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "users.discord_user_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    steam_app_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    game_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    playtime_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="steam_tracking_states",
    )

    __table_args__ = (
        UniqueConstraint(
            "discord_user_id",
            "steam_app_id",
            name="uq_steam_tracking_user_game",
        ),
    )