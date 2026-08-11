from collections import defaultdict
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands

from database.repositories.game_session_repository import get_sessions_between


def format_duration(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    if hours:
        return f"{hours}h {minutes}m"

    return f"{minutes}m"


def build_summary(rows) -> tuple[list[str], int]:
    totals = defaultdict(int)
    total_seconds = 0

    now = datetime.now(timezone.utc)

    for row in rows:
        if row.duration_seconds is not None:
            seconds = row.duration_seconds
        else:
            seconds = int(
                (now - row.started_at).total_seconds()
            )

        totals[row.game_name] += seconds
        total_seconds += seconds

    sorted_games = sorted(
        totals.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    lines = [
        f"🎮 **{game}** — {format_duration(seconds)}"
        for game, seconds in sorted_games
    ]

    return lines, total_seconds


class TodayCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="today",
        description="Show your gaming time today.",
    )
    async def today(
        self,
        interaction: discord.Interaction,
    ):
        await interaction.response.defer()

        now = datetime.now(timezone.utc)

        start = now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        end = start + timedelta(days=1)

        rows = get_sessions_between(
            interaction.user.id,
            start,
            end,
        )

        if not rows:
            await interaction.followup.send(
                "🎮 No gaming sessions recorded today."
            )
            return

        lines, total = build_summary(rows)

        message = (
            "## 🎮 Gaming today\n\n"
            + "\n".join(lines)
            + "\n\n"
            + f"**Total: {format_duration(total)}**"
        )

        await interaction.followup.send(message)


async def setup(bot: commands.Bot):
    await bot.add_cog(TodayCommand(bot))