import discord

from database.repositories.pubg_repository import get_tracked_accounts


async def handle_players(
    interaction: discord.Interaction,
) -> None:
    await interaction.response.defer()

    accounts = get_tracked_accounts()

    if not accounts:
        await interaction.followup.send(
            "No PUBG players are being tracked yet."
        )
        return

    lines = []

    for account in accounts:
        status = (
            "active"
            if account.is_active
            else "inactive"
        )

        account_state = (
            "linked"
            if account.pubg_account_id
            else "pending lookup"
        )

        lines.append(
            f"**{account.username}** - `{account.platform}` "
            f"- {status}, {account_state}"
        )

    embed = discord.Embed(
        title="Tracked PUBG Players",
        description="\n".join(lines),
        colour=discord.Colour.blurple(),
    )

    embed.set_footer(
        text="Use /pubg add_player to track another player."
    )

    await interaction.followup.send(
        embed=embed,
    )
