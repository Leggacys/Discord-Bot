import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from database.game_session_repository import (
    ensure_user,
    start_session,
    stop_session,
)

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing")


def get_games(member: discord.Member) -> set[str]:
    return {
        activity.name
        for activity in member.activities
        if activity.type == discord.ActivityType.playing
        and activity.name
    }


class GamingTrackerBot(commands.Bot):
    async def setup_hook(self):
        await self.load_extension("commands.playing")
        await self.load_extension("commands.today")
        await self.load_extension("commands.week")
        await self.load_extension("commands.stats")

       
        guild = discord.Object(
            id=1535000769789562962
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
    print(f"Connected as {bot.user}", flush=True)


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


bot.run(TOKEN)