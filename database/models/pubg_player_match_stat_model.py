from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base

if TYPE_CHECKING:
    from .pubg_account_model import PubgAccount
    from .pubg_match_model import PubgMatch


class PubgPlayerMatchStat(Base):
    __tablename__ = "pubg_player_match_stats"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    match_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey(
            "pubg_matches.match_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    pubg_account_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey(
            "pubg_accounts.pubg_account_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    win_place: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    kills: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    damage_dealt: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    longest_kill: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    match: Mapped["PubgMatch"] = relationship(
        back_populates="player_stats",
    )

    account: Mapped["PubgAccount"] = relationship(
        back_populates="stats",
    )

    __table_args__ = (
        UniqueConstraint(
            "match_id",
            "pubg_account_id",
            name="uq_pubg_stat_match_account",
        ),
    )
