import discord

from commands.pubg.formatting import format_distance, format_number
from database.repositories.pubg_repository import get_player_summary


async def handle_stats(
    interaction: discord.Interaction,
    username: str,
) -> None:
    await interaction.response.defer()

    summary = get_player_summary(
        username
    )

    if summary is None:
        await interaction.followup.send(
            f"No PUBG stats recorded for **{username}** yet."
        )
        return

    matches = int(
        summary["matches"]
    )
    kills = int(
        summary["kills"]
    )
    damage = float(
        summary["damage"]
    )
    wins = int(
        summary["wins"]
    )

    average_damage = (
        damage / matches
        if matches
        else 0
    )

    kills_per_match = (
        kills / matches
        if matches
        else 0
    )

    embed = discord.Embed(
        title=f"PUBG Statistics - {summary['username']}",
        colour=discord.Colour.blurple(),
    )

    embed.add_field(
        name="Matches",
        value=str(matches),
        inline=True,
    )

    embed.add_field(
        name="Wins",
        value=str(wins),
        inline=True,
    )

    embed.add_field(
        name="Win rate",
        value=f"{(wins / matches * 100):.1f}%" if matches else "0%",
        inline=True,
    )

    embed.add_field(
        name="Kills",
        value=str(kills),
        inline=True,
    )

    embed.add_field(
        name="Kills / match",
        value=f"{kills_per_match:.2f}",
        inline=True,
    )

    embed.add_field(
        name="Damage / match",
        value=format_number(
            average_damage
        ),
        inline=True,
    )

    embed.add_field(
        name="Total damage",
        value=format_number(
            damage
        ),
        inline=True,
    )

    embed.add_field(
        name="Longest kill",
        value=format_distance(
            float(summary["longest_kill"])
        ),
        inline=True,
    )

    embed.set_footer(
        text="Stats update when the background PUBG poller sees new matches."
    )

    await interaction.followup.send(
        embed=embed,
    )
