import discord
from discord import app_commands
from discord.ext import commands

from database.repositories.game_session_repository import ensure_user
from database.repositories.steam_repository import set_user_steam_id
from services.steam_service import resolve_steam_id


class SteamCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="steamlink",
        description="Link your Steam account to the gaming tracker.",
    )
    @app_commands.describe(
        steam="Steam profile URL, SteamID64, or custom profile name",
    )
    async def steamlink(
        self,
        interaction: discord.Interaction,
        steam: str,
    ):
        await interaction.response.defer(
            ephemeral=True,
        )

        steam_id = await resolve_steam_id(steam)

        if steam_id is None:
            await interaction.followup.send(
                "❌ I couldn't find that Steam account.",
                ephemeral=True,
            )
            return

        ensure_user(
            discord_user_id=interaction.user.id,
            username=interaction.user.name,
            display_name=interaction.user.display_name,
        )

        set_user_steam_id(
            discord_user_id=interaction.user.id,
            steam_id=steam_id,
        )

        await interaction.followup.send(
            "✅ Steam account linked!\n"
            f"SteamID64: `{steam_id}`",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(
        SteamCommands(bot)
    )