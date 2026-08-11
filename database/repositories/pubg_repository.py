from datetime import datetime, timezone
from typing import Any

from sqlalchemy import case, desc, func, select

from database.database import SessionLocal
from database import models
from database.models.pubg_account_model import PubgAccount
from database.models.pubg_announcement_model import PubgAnnouncement
from database.models.pubg_match_model import PubgMatch
from database.models.pubg_player_match_stat_model import PubgPlayerMatchStat


VALID_GAME_MODES = {
    "solo",
    "solo-fpp",
    "duo",
    "duo-fpp",
    "squad",
    "squad-fpp",
}


def add_tracked_account(
    *,
    username: str,
    platform: str,
    pubg_account_id: str | None = None,
) -> PubgAccount:
    with SessionLocal() as session:
        account = session.scalar(
            select(PubgAccount)
            .where(
                func.lower(
                    PubgAccount.username
                ) == username.lower()
            )
            .limit(1)
        )

        if account is None and pubg_account_id:
            account = session.scalar(
                select(PubgAccount)
                .where(
                    PubgAccount.pubg_account_id == pubg_account_id
                )
                .limit(1)
            )

        if account is None:
            account = PubgAccount(
                username=username,
                pubg_account_id=pubg_account_id,
                platform=platform,
                is_active=True,
            )
            session.add(account)
        else:
            account.username = username
            account.platform = platform
            account.is_active = True

            if pubg_account_id:
                account.pubg_account_id = pubg_account_id

        session.commit()
        session.refresh(account)

        return account


def get_active_accounts() -> list[PubgAccount]:
    with SessionLocal() as session:
        accounts = session.scalars(
            select(PubgAccount)
            .where(
                PubgAccount.is_active.is_(True)
            )
            .order_by(
                PubgAccount.username
            )
        ).all()

        return list(accounts)


def get_tracked_accounts() -> list[PubgAccount]:
    with SessionLocal() as session:
        accounts = session.scalars(
            select(PubgAccount)
            .order_by(
                PubgAccount.is_active.desc(),
                PubgAccount.username,
            )
        ).all()

        return list(accounts)


def set_pubg_account_id(
    username: str,
    pubg_account_id: str,
) -> None:
    with SessionLocal() as session:
        account = session.scalar(
            select(PubgAccount)
            .where(
                PubgAccount.username == username
            )
        )

        if account is None:
            return

        account.pubg_account_id = pubg_account_id
        session.commit()


def has_player_match_stat(
    match_id: str,
    pubg_account_id: str,
) -> bool:
    with SessionLocal() as session:
        existing = session.scalar(
            select(PubgPlayerMatchStat.id)
            .where(
                PubgPlayerMatchStat.match_id == match_id,
                PubgPlayerMatchStat.pubg_account_id == pubg_account_id,
            )
            .limit(1)
        )

        return existing is not None


def save_player_match_stat(
    *,
    match_id: str,
    platform: str,
    game_mode: str,
    match_type: str | None,
    played_at: datetime | None,
    pubg_account_id: str,
    username: str,
    stats: dict[str, Any],
) -> PubgPlayerMatchStat | None:
    if game_mode not in VALID_GAME_MODES:
        return None

    if match_type == "custom":
        return None

    with SessionLocal() as session:
        existing = session.scalar(
            select(PubgPlayerMatchStat)
            .where(
                PubgPlayerMatchStat.match_id == match_id,
                PubgPlayerMatchStat.pubg_account_id == pubg_account_id,
            )
            .limit(1)
        )

        if existing:
            return None

        account = session.scalar(
            select(PubgAccount)
            .where(
                PubgAccount.pubg_account_id == pubg_account_id
            )
        )

        if account:
            account.username = username

        match = session.get(
            PubgMatch,
            match_id,
        )

        if match is None:
            match = PubgMatch(
                match_id=match_id,
                platform=platform,
                game_mode=game_mode,
                match_type=match_type,
                played_at=played_at,
            )
            session.add(match)

        stat = PubgPlayerMatchStat(
            match_id=match_id,
            pubg_account_id=pubg_account_id,
            username=username,
            win_place=stats.get("winPlace"),
            kills=int(
                stats.get("kills") or 0
            ),
            damage_dealt=float(
                stats.get("damageDealt") or 0
            ),
            longest_kill=float(
                stats.get("longestKill") or 0
            ),
        )

        session.add(stat)
        session.commit()
        session.refresh(stat)

        return stat


def get_best_longest_kill_before(
    pubg_account_id: str,
    match_id: str,
) -> float:
    with SessionLocal() as session:
        best = session.scalar(
            select(
                func.max(
                    PubgPlayerMatchStat.longest_kill
                )
            )
            .where(
                PubgPlayerMatchStat.pubg_account_id == pubg_account_id,
                PubgPlayerMatchStat.match_id != match_id,
            )
        )

        return float(best or 0)


def create_announcement(
    *,
    event_type: str,
    match_id: str,
    pubg_account_id: str,
) -> PubgAnnouncement | None:
    with SessionLocal() as session:
        existing = session.scalar(
            select(PubgAnnouncement)
            .where(
                PubgAnnouncement.event_type == event_type,
                PubgAnnouncement.match_id == match_id,
                PubgAnnouncement.pubg_account_id == pubg_account_id,
            )
            .limit(1)
        )

        if existing:
            return None

        announcement = PubgAnnouncement(
            event_type=event_type,
            match_id=match_id,
            pubg_account_id=pubg_account_id,
        )

        session.add(announcement)
        session.commit()
        session.refresh(announcement)

        return announcement


def mark_announcement_sent(
    announcement_id: int,
) -> None:
    with SessionLocal() as session:
        announcement = session.get(
            PubgAnnouncement,
            announcement_id,
        )

        if announcement is None:
            return

        announcement.sent_at = datetime.now(timezone.utc)
        session.commit()


def get_player_summary(
    username: str,
) -> dict[str, float | int | str] | None:
    with SessionLocal() as session:
        row = session.execute(
            select(
                PubgPlayerMatchStat.username,
                func.count(
                    PubgPlayerMatchStat.id
                ),
                func.sum(
                    PubgPlayerMatchStat.kills
                ),
                func.sum(
                    PubgPlayerMatchStat.damage_dealt
                ),
                func.max(
                    PubgPlayerMatchStat.longest_kill
                ),
                func.sum(
                    case(
                        (
                            PubgPlayerMatchStat.win_place == 1,
                            1,
                        ),
                        else_=0,
                    )
                ),
            )
            .where(
                func.lower(
                    PubgPlayerMatchStat.username
                ) == username.lower()
            )
            .group_by(
                PubgPlayerMatchStat.username
            )
        ).one_or_none()

        if row is None:
            return None

        name, matches, kills, damage, longest, wins = row

        return {
            "username": name,
            "matches": int(matches or 0),
            "kills": int(kills or 0),
            "damage": float(damage or 0),
            "longest_kill": float(longest or 0),
            "wins": int(wins or 0),
        }


def get_leaderboard(
    metric: str,
    limit: int = 10,
) -> list[dict[str, float | int | str]]:
    metric_column = {
        "wins": func.sum(
            case(
                (
                    PubgPlayerMatchStat.win_place == 1,
                    1,
                ),
                else_=0,
            )
        ),
        "kills": func.sum(
            PubgPlayerMatchStat.kills
        ),
        "damage": func.sum(
            PubgPlayerMatchStat.damage_dealt
        ),
        "longest": func.max(
            PubgPlayerMatchStat.longest_kill
        ),
    }[metric]

    with SessionLocal() as session:
        rows = session.execute(
            select(
                PubgPlayerMatchStat.username,
                metric_column.label("score"),
                func.count(
                    PubgPlayerMatchStat.id
                ).label("matches"),
            )
            .group_by(
                PubgPlayerMatchStat.username
            )
            .order_by(
                desc("score")
            )
            .limit(limit)
        ).all()

        return [
            {
                "username": username,
                "score": float(score or 0),
                "matches": int(matches or 0),
            }
            for username, score, matches in rows
        ]
