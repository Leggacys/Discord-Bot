import discord
from discord import app_commands
from discord.ext import commands


def get_games(member: discord.Member) -> set[str]:
    return {
        activity.name
        for activity in member.activities
        if activity.type == discord.ActivityType.playing
        and activity.name
    }


class PlayingCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="playing",
        description="Show the game Discord currently detects.",
    )
    async def playing(
        self,
        interaction: discord.Interaction,
    ):
        if not isinstance(
            interaction.user,
            discord.Member,
        ):
            await interaction.response.send_message(
                "Use this command inside a Discord server."
            )
            return

        games = get_games(interaction.user)

        if not games:
            await interaction.response.send_message(
                "🎮 I don't currently detect a game."
            )
            return

        game_list = "\n".join(
            f"🎮 {game}"
            for game in sorted(games)
        )

        await interaction.response.send_message(
            f"**Currently playing:**\n{game_list}"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(PlayingCommand(bot))