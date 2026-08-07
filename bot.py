import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from database import (
    get_sessions_between,
    init_database,
    start_session,
    stop_session,
)

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing from .env")


intents = discord.Intents.default()
intents.members = True
intents.presences = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
)


def get_games(member: discord.Member) -> set[str]:
    return {
        activity.name
        for activity in member.activities
        if activity.type == discord.ActivityType.playing
        and activity.name
    }


def format_duration(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    if hours > 0:
        return f"{hours}h {minutes}m"

    return f"{minutes}m"


def build_summary(rows) -> tuple[list[str], int]:
    totals = defaultdict(int)
    total_seconds = 0

    now = datetime.now(timezone.utc)

    for row in rows:
        if row["duration_seconds"] is not None:
            seconds = row["duration_seconds"]
        else:
            started_at = datetime.fromisoformat(row["started_at"])
            seconds = int(
                (now - started_at).total_seconds()
            )

        totals[row["game_name"]] += seconds
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


@bot.event
async def on_ready():
    init_database()

    print(f"Connected as {bot.user}")

    try:
        synced = await bot.tree.sync()

        print(
            f"Synced {len(synced)} slash commands."
        )

    except Exception as error:
        print(
            f"Could not sync commands: {error}"
        )


@bot.event
async def on_presence_update(
    before: discord.Member,
    after: discord.Member,
):
    if after.bot:
        return

    before_games = get_games(before)
    after_games = get_games(after)

    started_games = after_games - before_games
    stopped_games = before_games - after_games

    for game in started_games:
        print(
            f"{after.display_name} started {game}"
        )

        start_session(
            discord_user_id=after.id,
            game_name=game,
        )

    for game in stopped_games:
        print(
            f"{after.display_name} stopped {game}"
        )

        stop_session(
            discord_user_id=after.id,
            game_name=game,
        )


@bot.tree.command(
    name="playing",
    description="Show the game Discord currently detects.",
)
async def playing(
    interaction: discord.Interaction,
):
    if not isinstance(
        interaction.user,
        discord.Member,
    ):
        await interaction.response.send_message(
            "Use this command inside a Discord server.",
            ephemeral=True,
        )
        return

    games = get_games(interaction.user)

    if not games:
        await interaction.response.send_message(
            "🎮 I don't currently detect a game.",
            ephemeral=True,
        )
        return

    game_list = "\n".join(
        f"🎮 {game}"
        for game in sorted(games)
    )

    await interaction.response.send_message(
        f"**Currently playing:**\n{game_list}",
        ephemeral=True,
    )


@bot.tree.command(
    name="today",
    description="Show your gaming time today.",
)
async def today(
    interaction: discord.Interaction,
):
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
        await interaction.response.send_message(
            "🎮 No gaming sessions recorded today.",
            ephemeral=True,
        )
        return

    lines, total = build_summary(rows)

    message = (
        "## 🎮 Gaming today\n\n"
        + "\n".join(lines)
        + "\n\n"
        + f"**Total: {format_duration(total)}**"
    )

    await interaction.response.send_message(
        message,
        ephemeral=True,
    )


@bot.tree.command(
    name="week",
    description="Show your gaming time this week.",
)
async def week(
    interaction: discord.Interaction,
):
    now = datetime.now(timezone.utc)

    start = (
        now
        - timedelta(days=now.weekday())
    ).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    end = start + timedelta(days=7)

    rows = get_sessions_between(
        interaction.user.id,
        start,
        end,
    )

    if not rows:
        await interaction.response.send_message(
            "🎮 No gaming sessions recorded this week.",
            ephemeral=True,
        )
        return

    lines, total = build_summary(rows)

    message = (
        "## 🎮 Gaming this week\n\n"
        + "\n".join(lines)
        + "\n\n"
        + f"**Total: {format_duration(total)}**"
    )

    await interaction.response.send_message(
        message,
        ephemeral=True,
    )


bot.run(TOKEN)