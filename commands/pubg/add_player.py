import os

import discord

from database.repositories.pubg_repository import add_tracked_account
from services.pubg_service import DEFAULT_PLATFORM, PubgApiClient


async def handle_add_player(
    interaction: discord.Interaction,
    username: str,
) -> None:
    await interaction.response.defer()

    api_key = os.getenv("PUBG_API_KEY")
    platform = os.getenv(
        "PUBG_PLATFORM",
        DEFAULT_PLATFORM,
    )

    if not api_key:
        await interaction.followup.send(
            "PUBG_API_KEY is not configured, so I cannot validate players yet."
        )
        return

    client = PubgApiClient(
        api_key=api_key,
        platform=platform,
    )

    pubg_account_id = await client.get_player_account_id(
        username
    )

    if not pubg_account_id:
        await interaction.followup.send(
            f"I could not find a PUBG player named **{username}** on `{platform}`."
        )
        return

    account = add_tracked_account(
        username=username,
        platform=platform,
        pubg_account_id=pubg_account_id,
    )

    embed = discord.Embed(
        title="PUBG Player Added",
        colour=discord.Colour.green(),
    )

    embed.add_field(
        name="Player",
        value=f"**{account.username}**",
        inline=True,
    )

    embed.add_field(
        name="Platform",
        value=f"`{account.platform}`",
        inline=True,
    )

    embed.add_field(
        name="Status",
        value="Tracking enabled",
        inline=True,
    )

    embed.set_footer(
        text="Recent matches will be imported by the background poller."
    )

    await interaction.followup.send(
        embed=embed,
    )
