import asyncio
from datetime import datetime, timedelta, timezone

import discord

from commands.overall_gaming.today import (
    build_summary,
    format_duration,
)
from database.repositories.game_session_repository import (
    get_sessions_between,
)


async def handle_week(
    interaction: discord.Interaction,
):
    await interaction.response.defer()

    now = datetime.now(
        timezone.utc
    )

    start = (
        now
        - timedelta(
            days=now.weekday()
        )
    ).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    end = (
        start
        + timedelta(days=7)
    )

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

    lines, total = build_summary(
        rows
    )

    if total <= 0:
        await interaction.followup.send(
            "🎮 No gaming time recorded this week."
        )
        return

    message = (
        "## 🎮 Gaming this week\n\n"
        + "\n".join(lines)
        + "\n\n"
        + f"**Total: {format_duration(total)}**"
    )

    await interaction.followup.send(
        message
    )