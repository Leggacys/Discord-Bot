import asyncio

import discord
from discord.ext import commands

from services.roast_service import (
    generate_group_session_roast,
)


BATCH_SECONDS = 120

pending_sessions = []
batch_task: asyncio.Task | None = None


async def queue_finished_session(
    bot: commands.Bot,
    *,
    username: str,
    game_name: str,
    duration_seconds: int,
    channel_id: int,
):
    global batch_task

    pending_sessions.append(
        {
            "username": username,
            "game_name": game_name,
            "duration_seconds": duration_seconds,
            "channel_id": channel_id,
        }
    )

    if batch_task is None or batch_task.done():
        batch_task = asyncio.create_task(
            _flush_batch(bot)
        )


async def _flush_batch(
    bot: commands.Bot,
):
    global pending_sessions

    await asyncio.sleep(
        BATCH_SECONDS
    )

    sessions = pending_sessions
    pending_sessions = []

    if not sessions:
        return

    channel_id = sessions[0][
        "channel_id"
    ]

    channel = bot.get_channel(
        channel_id
    )

    if channel is None:
        return

    roast = await asyncio.to_thread(
        generate_group_session_roast,
        sessions=sessions,
    )

    await channel.send(
        f"## 💀 Gaming shift finished\n\n{roast}"
    )