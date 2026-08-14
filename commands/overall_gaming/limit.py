import discord

from database.repositories.game_session_repository import ensure_user
from database.repositories.user_repository import (
    get_daily_gaming_limit,
    remove_daily_gaming_limit,
    set_daily_gaming_limit,
)


async def handle_limit_set(
    interaction: discord.Interaction,
    hours: float,
):
    if hours <= 0:
        await interaction.response.send_message(
            "❌ Limit must be greater than 0 hours.",
            ephemeral=True,
        )
        return

    if hours > 24:
        await interaction.response.send_message(
            "❌ Limit cannot be greater than 24 hours.",
            ephemeral=True,
        )
        return

    ensure_user(
        discord_user_id=interaction.user.id,
        username=interaction.user.name,
        display_name=interaction.user.display_name,
    )

    minutes = round(
        hours * 60
    )

    success = set_daily_gaming_limit(
        discord_user_id=interaction.user.id,
        minutes=minutes,
    )

    if not success:
        await interaction.response.send_message(
            "❌ Failed to save your gaming limit.",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        (
            "✅ Daily gaming limit set to "
            f"**{hours:g} hours**."
        ),
        ephemeral=True,
    )


async def handle_limit_show(
    interaction: discord.Interaction,
):
    minutes = get_daily_gaming_limit(
        interaction.user.id
    )

    if minutes is None:
        await interaction.response.send_message(
            "🎮 You don't currently have a daily gaming limit.",
            ephemeral=True,
        )
        return

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes:
        formatted = (
            f"{hours}h {remaining_minutes}m"
        )
    else:
        formatted = (
            f"{hours}h"
        )

    await interaction.response.send_message(
        (
            "🎯 Your daily gaming limit is "
            f"**{formatted}**."
        ),
        ephemeral=True,
    )


async def handle_limit_remove(
    interaction: discord.Interaction,
):
    success = remove_daily_gaming_limit(
        interaction.user.id
    )

    if not success:
        await interaction.response.send_message(
            "❌ Could not find your user.",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        "✅ Daily gaming limit removed.",
        ephemeral=True,
    )