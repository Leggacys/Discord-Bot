from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base

if TYPE_CHECKING:
    from .pubg_player_match_stat_model import PubgPlayerMatchStat


class PubgMatch(Base):
    __tablename__ = "pubg_matches"

    match_id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
    )

    platform: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    game_mode: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    match_type: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )

    played_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    player_stats: Mapped[list["PubgPlayerMatchStat"]] = relationship(
        back_populates="match",
        cascade="all, delete-orphan",
    )
