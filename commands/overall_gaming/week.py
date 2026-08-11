import asyncio
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands

from commands.overall_gaming.today import build_summary, format_duration
from database.repositories.game_session_repository import get_sessions_between


class WeekCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="week",
        description="Show your gaming time this week.",
    )
    async def week(
        self,
        interaction: discord.Interaction,
    ):
        # Acknowledge the interaction immediately
        await interaction.response.defer()

        now = datetime.now(timezone.utc)

        start = (
            now - timedelta(days=now.weekday())
        ).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        end = start + timedelta(days=7)

        rows = await asyncio.to_thread(
            get_sessions_between,
            interaction.user.id,
            start,
            end,
        )

        if not rows:
            await interaction.followup.send(
                "🎮 No gaming sessions recorded this week."
            )
            return

        lines, total = build_summary(rows)

        message = (
            "## 🎮 Gaming this week\n\n"
            + "\n".join(lines)
            + "\n\n"
            + f"**Total: {format_duration(total)}**"
        )

        await interaction.followup.send(message)


async def setup(bot: commands.Bot):
    await bot.add_cog(WeekCommand(bot))