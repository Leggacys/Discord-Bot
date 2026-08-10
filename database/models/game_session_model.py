from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base
from .user_model import User

class GameSession(Base):
    __tablename__ = "game_sessions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    discord_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.discord_user_id"),
        nullable=False,
        index=True,
    )

    game_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="sessions",
    )