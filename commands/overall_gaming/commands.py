import discord
from discord import app_commands
from discord.ext import commands

from commands.overall_gaming.limit import (
    handle_limit_remove,
    handle_limit_set,
    handle_limit_show,
)
from commands.overall_gaming.playing import handle_playing
from commands.overall_gaming.stats import handle_stats
from commands.overall_gaming.today import handle_today
from commands.overall_gaming.top import handle_top
from commands.overall_gaming.week import handle_week


class GamingCommand(commands.Cog):
    gaming = app_commands.Group(
        name="gaming",
        description="Gaming activity, stats, and leaderboards.",
    )

    limit = app_commands.Group(
        name="limit",
        description="Manage your daily gaming limit.",
        parent=gaming,
    )

    def __init__(
        self,
        bot: commands.Bot,
    ):
        self.bot = bot

    @gaming.command(
        name="playing",
        description="Show the game Discord currently detects.",
    )
    async def playing(
        self,
        interaction: discord.Interaction,
    ):
        await handle_playing(
            interaction,
        )

    @gaming.command(
        name="today",
        description="Show your gaming time today.",
    )
    async def today(
        self,
        interaction: discord.Interaction,
    ):
        await handle_today(
            interaction,
        )

    @gaming.command(
        name="week",
        description="Show your gaming time this week.",
    )
    async def week(
        self,
        interaction: discord.Interaction,
    ):
        await handle_week(
            interaction,
        )

    @gaming.command(
        name="stats",
        description="Show your gaming statistics.",
    )
    @app_commands.describe(
        period="Statistics period",
    )
    @app_commands.choices(
        period=[
            app_commands.Choice(
                name="Today",
                value="today",
            ),
            app_commands.Choice(
                name="This week",
                value="week",
            ),
            app_commands.Choice(
                name="This month",
                value="month",
            ),
        ]
    )
    async def stats(
        self,
        interaction: discord.Interaction,
        period: app_commands.Choice[str],
    ):
        await handle_stats(
            interaction,
            period.value,
        )

    @gaming.command(
        name="top",
        description="Show the gaming leaderboard and roast the winner.",
    )
    @app_commands.describe(
        period="Leaderboard period",
    )
    @app_commands.choices(
        period=[
            app_commands.Choice(
                name="Today",
                value="today",
            ),
            app_commands.Choice(
                name="This week",
                value="week",
            ),
            app_commands.Choice(
                name="This month",
                value="month",
            ),
        ]
    )
    async def top(
        self,
        interaction: discord.Interaction,
        period: app_commands.Choice[str],
    ):
        await handle_top(
            interaction,
            period.value,
        )

    @limit.command(
        name="set",
        description="Set your daily gaming limit.",
    )
    @app_commands.describe(
        hours="Maximum gaming hours per day",
    )
    async def limit_set(
        self,
        interaction: discord.Interaction,
        hours: float,
    ):
        await handle_limit_set(
            interaction,
            hours,
        )

    @limit.command(
        name="show",
        description="Show your daily gaming limit.",
    )
    async def limit_show(
        self,
        interaction: discord.Interaction,
    ):
        await handle_limit_show(
            interaction,
        )

    @limit.command(
        name="remove",
        description="Remove your daily gaming limit.",
    )
    async def limit_remove(
        self,
        interaction: discord.Interaction,
    ):
        await handle_limit_remove(
            interaction,
        )


async def setup(
    bot: commands.Bot,
):
    await bot.add_cog(
        GamingCommand(bot)
    )