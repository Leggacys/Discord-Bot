from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base


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

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    sessions: Mapped[list["GameSession"]] = relationship(
        back_populates="user",
    )
