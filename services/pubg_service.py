import os
from dataclasses import dataclass
from datetime import datetime, timezone

import discord
import httpx
from discord.ext import tasks

from database.repositories.pubg_repository import (
    create_announcement,
    get_active_accounts,
    get_best_longest_kill_before,
    has_player_match_stat,
    mark_announcement_sent,
    save_player_match_stat,
    set_pubg_account_id,
)


PUBG_ACCEPT_HEADER = "application/vnd.api+json"
DEFAULT_PLATFORM = "steam"
DEFAULT_POLL_MINUTES = 5


def log_pubg(
    message: str,
) -> None:
    print(
        f"[PUBG] {message}",
        flush=True,
    )


def get_rate_limit_log(
    response: httpx.Response,
) -> str:
    limit = response.headers.get(
        "X-RateLimit-Limit"
    )
    remaining = response.headers.get(
        "X-RateLimit-Remaining"
    )
    reset = response.headers.get(
        "X-RateLimit-Reset"
    )
    retry_after = response.headers.get(
        "Retry-After"
    )

    parts = []

    if limit:
        parts.append(
            f"limit={limit}"
        )

    if remaining:
        parts.append(
            f"remaining={remaining}"
        )

    if reset:
        parts.append(
            f"reset={reset}"
        )

    if retry_after:
        parts.append(
            f"retry_after={retry_after}s"
        )

    if not parts:
        return "rate_limit_headers=none"

    return " ".join(parts)


@dataclass(frozen=True)
class PubgConfig:
    api_key: str
    platform: str
    channel_id: int | None
    poll_minutes: float


class PubgApiClient:
    def __init__(
        self,
        api_key: str,
        platform: str,
    ):
        self.api_key = api_key
        self.platform = platform

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": PUBG_ACCEPT_HEADER,
        }

    async def get_player_account_id(
        self,
        username: str,
    ) -> str | None:
        url = (
            f"https://api.pubg.com/shards/{self.platform}/players"
            f"?filter[playerNames]={username}"
        )

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                url,
                headers=self.headers,
            )

        log_pubg(
            "player lookup "
            f"username={username} status={response.status_code} "
            f"{get_rate_limit_log(response)}"
        )

        if response.status_code != 200:
            log_pubg(
                f"PUBG player lookup failed for {username}: "
                f"{response.status_code}"
            )
            return None

        rows = response.json().get(
            "data",
            [],
        )

        if not rows:
            log_pubg(
                f"player lookup returned no rows username={username}"
            )
            return None

        log_pubg(
            f"player lookup resolved username={username} account_id={rows[0]['id']}"
        )

        return rows[0]["id"]

    async def get_recent_match_ids(
        self,
        pubg_account_id: str,
    ) -> list[str]:
        url = (
            f"https://api.pubg.com/shards/{self.platform}/players/"
            f"{pubg_account_id}"
        )

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                url,
                headers=self.headers,
            )

        log_pubg(
            "recent matches lookup "
            f"account_id={pubg_account_id} status={response.status_code} "
            f"{get_rate_limit_log(response)}"
        )

        if response.status_code != 200:
            log_pubg(
                f"PUBG matches lookup failed for {pubg_account_id}: "
                f"{response.status_code}"
            )
            return []

        matches = (
            response.json()
            .get("data", {})
            .get("relationships", {})
            .get("matches", {})
            .get("data", [])
        )

        match_ids = [
            match["id"]
            for match in matches
            if match.get("id")
        ]

        log_pubg(
            f"recent matches found account_id={pubg_account_id} count={len(match_ids)}"
        )

        return match_ids

    async def get_match(
        self,
        match_id: str,
    ) -> dict | None:
        url = (
            f"https://api.pubg.com/shards/{self.platform}/matches/"
            f"{match_id}"
        )

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                url,
                headers=self.headers,
            )

        log_pubg(
            "match lookup "
            f"match_id={match_id} status={response.status_code} "
            f"{get_rate_limit_log(response)}"
        )

        if response.status_code != 200:
            log_pubg(
                f"PUBG match lookup failed for {match_id}: "
                f"{response.status_code}"
            )
            return None

        return response.json()


def get_pubg_config() -> PubgConfig | None:
    api_key = os.getenv("PUBG_API_KEY")

    if not api_key:
        return None

    channel_id_value = os.getenv("PUBG_CHANNEL_ID")
    channel_id = (
        int(channel_id_value)
        if channel_id_value
        else None
    )

    poll_minutes = float(
        os.getenv(
            "PUBG_POLL_MINUTES",
            str(DEFAULT_POLL_MINUTES),
        )
    )

    return PubgConfig(
        api_key=api_key,
        platform=os.getenv(
            "PUBG_PLATFORM",
            DEFAULT_PLATFORM,
        ),
        channel_id=channel_id,
        poll_minutes=poll_minutes,
    )


def parse_played_at(
    value: str | None,
) -> datetime | None:
    if not value:
        return None

    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )


def normalize_datetime(
    value: datetime,
) -> datetime:
    if value.tzinfo is None:
        return value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(
        timezone.utc
    )


def find_participant(
    match_data: dict,
    pubg_account_id: str,
) -> dict | None:
    for item in match_data.get(
        "included",
        [],
    ):
        if item.get("type") != "participant":
            continue

        stats = (
            item.get("attributes", {})
            .get("stats", {})
        )

        if stats.get("playerId") == pubg_account_id:
            return stats

    return None


def build_pubg_announcement_embed(
    *,
    title: str,
    username: str,
    stat,
) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        colour=discord.Colour.gold(),
    )

    embed.add_field(
        name="Player",
        value=f"**{username}**",
        inline=True,
    )

    embed.add_field(
        name="Placement",
        value=(
            f"#{stat.win_place}"
            if stat.win_place is not None
            else "Unknown"
        ),
        inline=True,
    )

    embed.add_field(
        name="Kills",
        value=str(stat.kills),
        inline=True,
    )

    embed.add_field(
        name="Damage",
        value=f"{stat.damage_dealt:.0f}",
        inline=True,
    )

    embed.add_field(
        name="Longest kill",
        value=f"{stat.longest_kill:.1f} m",
        inline=True,
    )

    embed.set_footer(
        text=f"PUBG match {stat.match_id}",
    )

    return embed


class PubgMatchPoller:
    def __init__(
        self,
        bot: discord.Client,
        config: PubgConfig,
    ):
        self.bot = bot
        self.config = config
        self.client = PubgApiClient(
            api_key=config.api_key,
            platform=config.platform,
        )

        self.poll.change_interval(
            minutes=config.poll_minutes
        )

    def start(self) -> None:
        log_pubg(
            "poller starting "
            f"platform={self.config.platform} "
            f"poll_minutes={self.config.poll_minutes} "
            f"announcements={'enabled' if self.config.channel_id else 'disabled'}"
        )

        self.poll.start()

    @tasks.loop(minutes=DEFAULT_POLL_MINUTES)
    async def poll(self) -> None:
        try:
            accounts = get_active_accounts()
        except Exception as exc:
            log_pubg(
                f"poll failed while loading active accounts: {exc}"
            )
            return

        log_pubg(
            f"poll started active_accounts={len(accounts)}"
        )

        if not accounts:
            log_pubg(
                "poll finished no active accounts"
            )
            return

        for account in accounts:
            try:
                await self.poll_account(
                    account
                )
            except Exception as exc:
                log_pubg(
                    f"poll account failed username={account.username} error={exc}"
                )

        log_pubg(
            "poll finished"
        )

    async def poll_account(
        self,
        account,
    ) -> None:
        pubg_account_id = account.pubg_account_id

        log_pubg(
            f"checking account username={account.username} linked={bool(pubg_account_id)}"
        )

        if not pubg_account_id:
            pubg_account_id = await self.client.get_player_account_id(
                account.username
            )

            if not pubg_account_id:
                log_pubg(
                    f"skipping username={account.username} reason=player_not_found"
                )
                return

            set_pubg_account_id(
                account.username,
                pubg_account_id,
            )

            log_pubg(
                f"stored account id username={account.username} account_id={pubg_account_id}"
            )

        match_ids = await self.client.get_recent_match_ids(
            pubg_account_id
        )

        skipped_existing = 0

        for match_id in match_ids:
            if has_player_match_stat(
                match_id,
                pubg_account_id,
            ):
                skipped_existing += 1
                continue

            match_data = await self.client.get_match(
                match_id
            )

            if not match_data:
                continue

            await self.process_match(
                match_data=match_data,
                match_id=match_id,
                pubg_account_id=pubg_account_id,
                tracked_after=account.created_at,
            )

        log_pubg(
            f"account finished username={account.username} "
            f"matches_seen={len(match_ids)} skipped_existing={skipped_existing}"
        )

    @poll.before_loop
    async def before_poll(self) -> None:
        await self.bot.wait_until_ready()

    async def process_match(
        self,
        *,
        match_data: dict,
        match_id: str,
        pubg_account_id: str,
        tracked_after: datetime,
    ) -> None:
        attributes = (
            match_data.get("data", {})
            .get("attributes", {})
        )

        played_at = parse_played_at(
            attributes.get("createdAt")
        )

        if played_at is None:
            log_pubg(
                f"match skipped match_id={match_id} reason=missing_created_at"
            )
            return

        if normalize_datetime(played_at) < normalize_datetime(tracked_after):
            log_pubg(
                f"match skipped match_id={match_id} reason=before_tracking_start "
                f"played_at={normalize_datetime(played_at).isoformat()} "
                f"tracked_after={normalize_datetime(tracked_after).isoformat()}"
            )
            return

        participant_stats = find_participant(
            match_data,
            pubg_account_id,
        )

        if not participant_stats:
            log_pubg(
                f"match skipped match_id={match_id} reason=participant_not_found"
            )
            return

        previous_longest = get_best_longest_kill_before(
            pubg_account_id,
            match_id,
        )

        stat = save_player_match_stat(
            match_id=match_id,
            platform=self.config.platform,
            game_mode=attributes.get(
                "gameMode",
                "",
            ),
            match_type=attributes.get("matchType"),
            played_at=played_at,
            pubg_account_id=pubg_account_id,
            username=participant_stats.get("name", "Unknown"),
            stats=participant_stats,
        )

        if stat is None:
            log_pubg(
                f"match skipped match_id={match_id} reason=not_saveable_or_duplicate"
            )
            return

        log_pubg(
            f"match saved match_id={match_id} username={stat.username} "
            f"place={stat.win_place} kills={stat.kills} "
            f"damage={stat.damage_dealt:.0f} longest_kill={stat.longest_kill:.1f}"
        )

        if stat.win_place == 1:
            await self.send_announcement(
                event_type="win",
                stat=stat,
                title="PUBG Winner Winner Chicken Dinner",
            )

        if stat.longest_kill > previous_longest:
            await self.send_announcement(
                event_type="longest_kill",
                stat=stat,
                title="PUBG New Longest Kill",
            )

    async def send_announcement(
        self,
        *,
        event_type: str,
        stat,
        title: str,
    ) -> None:
        if not self.config.channel_id:
            log_pubg(
                f"announcement skipped event={event_type} reason=no_channel_config"
            )
            return

        channel = self.bot.get_channel(
            self.config.channel_id
        )

        if channel is None:
            log_pubg(
                f"announcement skipped event={event_type} "
                f"reason=channel_not_found channel_id={self.config.channel_id}"
            )
            return

        announcement = create_announcement(
            event_type=event_type,
            match_id=stat.match_id,
            pubg_account_id=stat.pubg_account_id,
        )

        if announcement is None:
            log_pubg(
                f"announcement skipped event={event_type} "
                f"match_id={stat.match_id} reason=already_created"
            )
            return

        embed = build_pubg_announcement_embed(
            title=title,
            username=stat.username,
            stat=stat,
        )

        await channel.send(
            embed=embed,
        )

        mark_announcement_sent(
            announcement.id
        )

        log_pubg(
            f"announcement sent event={event_type} match_id={stat.match_id} "
            f"username={stat.username}"
        )
