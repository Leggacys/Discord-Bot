import discord
from discord import app_commands
from discord.ext import commands

from commands.pubg.add_player import handle_add_player
from commands.pubg.leaderboard import handle_leaderboard
from commands.pubg.player_stats import handle_stats
from commands.pubg.players import handle_players


class PubgCommand(commands.Cog):
    pubg = app_commands.Group(
        name="pubg",
        description="PUBG stats and leaderboards.",
    )

    def __init__(
        self,
        bot: commands.Bot,
    ):
        self.bot = bot

    @pubg.command(
        name="add_player",
        description="Track a PUBG player.",
    )
    @app_commands.describe(
        username="PUBG username to track",
    )
    async def add_player(
        self,
        interaction: discord.Interaction,
        username: str,
    ):
        await handle_add_player(
            interaction,
            username,
        )

    @pubg.command(
        name="players",
        description="List tracked PUBG players.",
    )
    async def players(
        self,
        interaction: discord.Interaction,
    ):
        await handle_players(
            interaction
        )

    @pubg.command(
        name="stats",
        description="Show PUBG stats for a tracked player.",
    )
    @app_commands.describe(
        username="PUBG username",
    )
    async def stats(
        self,
        interaction: discord.Interaction,
        username: str,
    ):
        await handle_stats(
            interaction,
            username,
        )

    @pubg.command(
        name="leaderboard",
        description="Show a PUBG leaderboard.",
    )
    @app_commands.describe(
        metric="Leaderboard metric",
    )
    @app_commands.choices(
        metric=[
            app_commands.Choice(
                name="Wins",
                value="wins",
            ),
            app_commands.Choice(
                name="Kills",
                value="kills",
            ),
            app_commands.Choice(
                name="Damage",
                value="damage",
            ),
            app_commands.Choice(
                name="Longest kill",
                value="longest",
            ),
        ]
    )
    async def leaderboard(
        self,
        interaction: discord.Interaction,
        metric: app_commands.Choice[str],
    ):
        await handle_leaderboard(
            interaction,
            metric.value,
        )


async def setup(
    bot: commands.Bot,
):
    await bot.add_cog(
        PubgCommand(bot)
    )
