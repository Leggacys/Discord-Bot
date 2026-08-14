import discord


async def handle_playing(
    interaction: discord.Interaction,
):
    member = interaction.guild.get_member(
        interaction.user.id
    )

    if member is None:
        await interaction.response.send_message(
            "❌ Could not find your Discord member.",
            ephemeral=True,
        )
        return

    games = [
        activity.name
        for activity in member.activities
        if (
            activity.type
            == discord.ActivityType.playing
            and activity.name
        )
    ]

    if not games:
        await interaction.response.send_message(
            "🎮 Discord doesn't detect you playing anything right now."
        )
        return

    if len(games) == 1:
        message = (
            f"🎮 You're currently playing "
            f"**{games[0]}**."
        )
    else:
        message = (
            "🎮 Discord currently detects:\n"
            + "\n".join(
                f"• **{game}**"
                for game in games
            )
        )

    await interaction.response.send_message(
        message
    )