import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from database.repositories.game_session_repository import (
    ensure_user,
    start_session,
    stop_session,
)

from events.session_roast import (
    queue_finished_session,
)

from services.pubg_service import (
    PubgMatchPoller,
    get_pubg_config,
)

from services.steam_service import (
    SteamPlaytimePoller,
    get_steam_config,
)


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("DISCORD_GUILD_ID")

SESSION_ROAST_CHANNEL_ID = int(
    os.getenv(
        "SESSION_ROAST_CHANNEL_ID",
        "0",
    )
)

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN is missing"
    )

if not GUILD_ID:
    raise RuntimeError(
        "DISCORD_GUILD_ID is missing"
    )

GUILD_ID = int(GUILD_ID)


def get_games(
    member: discord.Member,
) -> set[str]:
    return {
        activity.name
        for activity in member.activities
        if activity.type
        == discord.ActivityType.playing
        and activity.name
    }


class GamingTrackerBot(commands.Bot):
    async def setup_hook(self):

        await self.load_extension(
            "commands.overall_gaming.commands"
        )

        await self.load_extension(
            "commands.pubg.commands"
        )

        await self.load_extension(
            "commands.steam.steam_link"
        )

        await self.load_extension(
            "events.everyone_roast"
        )

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

        steam_config = get_steam_config()

        if steam_config:
            self.steam_playtime_poller = (
                SteamPlaytimePoller(
                    self,
                    steam_config,
                )
            )

            self.steam_playtime_poller.start()

            print(
                "Steam playtime poller started.",
                flush=True,
            )

        else:
            print(
                "Steam playtime poller disabled. "
                "Set STEAM_API_KEY to enable it.",
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
intents.message_content = True

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

    before_games = get_games(
        before
    )

    after_games = get_games(
        after
    )

    started_games = (
        after_games - before_games
    )

    stopped_games = (
        before_games - after_games
    )

    if (
        not started_games
        and not stopped_games
    ):
        return

    ensure_user(
        discord_user_id=after.id,
        username=after.name,
        display_name=after.display_name,
    )

    for game in started_games:
        print(
            f"{after.display_name} "
            f"started {game}",
            flush=True,
        )

        start_session(
            discord_user_id=after.id,
            game_name=game,
        )

    for game in stopped_games:
        print(
            f"{after.display_name} "
            f"stopped {game}",
            flush=True,
        )

        duration_seconds = stop_session(
            discord_user_id=after.id,
            game_name=game,
        )

        if duration_seconds is None:
            continue

        if not SESSION_ROAST_CHANNEL_ID:
            print(
                "Session roast skipped: "
                "SESSION_ROAST_CHANNEL_ID is not configured.",
                flush=True,
            )
            continue

        await queue_finished_session(
            bot,
            username=after.display_name,
            game_name=game,
            duration_seconds=duration_seconds,
            channel_id=SESSION_ROAST_CHANNEL_ID,
        )


bot.run(TOKEN)