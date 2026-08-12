import discord

from commands.pubg.formatting import format_distance, format_number
from database.repositories.pubg_repository import get_leaderboard


METRIC_TITLES = {
    "wins": "Wins",
    "kills": "Kills",
    "damage": "Damage",
    "longest": "Longest Kill",
}


async def handle_leaderboard(
    interaction: discord.Interaction,
    metric: str,
) -> None:
    await interaction.response.defer()

    rows = get_leaderboard(
        metric
    )

    if not rows:
        await interaction.followup.send(
            "No PUBG matches have been recorded yet."
        )
        return

    lines = []

    for index, row in enumerate(rows):
        position = f"{index + 1}."
        score = float(
            row["score"]
        )

        if metric == "longest":
            score_text = format_distance(
                score
            )
        else:
            score_text = format_number(
                score
            )

        lines.append(
            f"`{position}` **{row['username']}** - "
            f"{score_text} ({row['matches']} matches)"
        )

    embed = discord.Embed(
        title=f"PUBG Top - {METRIC_TITLES[metric]}",
        description="\n".join(lines),
        colour=discord.Colour.orange(),
    )

    winner = rows[0]
    leader_score = lines[0].split(
        " - ",
        1,
    )[1].split(
        " (",
        1,
    )[0]

    embed.add_field(
        name="Current leader",
        value=(
            f"**{winner['username']}**\n"
            f"{METRIC_TITLES[metric]}: {leader_score}"
        ),
        inline=False,
    )

    embed.set_footer(
        text="Rankings are based on tracked PUBG matches in Postgres."
    )

    await interaction.followup.send(
        embed=embed,
    )
