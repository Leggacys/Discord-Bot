import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from database.repositories.game_session_repository import (
    ensure_user,
    start_session,
    stop_session,
)
from services.pubg_service import PubgMatchPoller, get_pubg_config

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("DISCORD_GUILD_ID")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing")

if not GUILD_ID:
    raise RuntimeError("DISCORD_GUILD_ID is missing")

GUILD_ID = int(GUILD_ID)


def get_games(member: discord.Member) -> set[str]:
    return {
        activity.name
        for activity in member.activities
        if activity.type == discord.ActivityType.playing
        and activity.name
    }


class GamingTrackerBot(commands.Bot):
    async def setup_hook(self):
        await self.load_extension("commands.overall_gaming.playing")
        await self.load_extension("commands.overall_gaming.today")
        await self.load_extension("commands.overall_gaming.week")
        await self.load_extension("commands.overall_gaming.stats")
        await self.load_extension("commands.overall_gaming.top")
        await self.load_extension("commands.pubg.commands")

        pubg_config = get_pubg_config()

        if pubg_config:
            self.pubg_match_poller = PubgMatchPoller(
                self,
                pubg_config,
            )
            self.pubg_match_poller.start()

            print(
                "PUBG match poller started.",
                flush=True,
            )
        else:
            print(
                "PUBG match poller disabled. "
                "Set PUBG_API_KEY to enable it.",
                flush=True,
            )

        guild = discord.Object(
            id=GUILD_ID
        )

        self.tree.copy_global_to(
            guild=guild
        )

        print(
            "Commands loaded locally:",
            flush=True,
        )

        for command in self.tree.get_commands(
            guild=guild
        ):
            print(
                f"  /{command.name}",
                flush=True,
            )

        synced = await self.tree.sync(
            guild=guild
        )

        print(
            f"Synced {len(synced)} slash commands "
            f"to guild {guild.id}:",
            flush=True,
        )

        for command in synced:
            print(
                f"  /{command.name} - "
                f"{command.description}",
                flush=True,
            )


intents = discord.Intents.default()
intents.members = True
intents.presences = True

bot = GamingTrackerBot(
    command_prefix="!",
    intents=intents,
)


@bot.event
async def on_ready():
    print(
        f"Connected as {bot.user}",
        flush=True,
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

    if not started_games and not stopped_games:
        return

    ensure_user(
        discord_user_id=after.id,
        username=after.name,
        display_name=after.display_name,
    )

    for game in started_games:
        print(
            f"{after.display_name} started {game}",
            flush=True,
        )

        start_session(
            discord_user_id=after.id,
            game_name=game,
        )

    for game in stopped_games:
        print(
            f"{after.display_name} stopped {game}",
            flush=True,
        )

        stop_session(
            discord_user_id=after.id,
            game_name=game,
        )


bot.run(TOKEN)
