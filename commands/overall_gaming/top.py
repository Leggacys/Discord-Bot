from collections import defaultdict
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands

from commands.overall_gaming.today import format_duration
from database.repositories.game_session_repository import (
    get_all_sessions_between,
)
from services.roast_service import generate_roast


class TopCommand(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
    ):
        self.bot = bot

    @app_commands.command(
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
        await interaction.response.defer()

        now = datetime.now(timezone.utc)

        # --------------------------------------
        # Period
        # --------------------------------------

        if period.value == "today":
            start = now.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            end = start + timedelta(days=1)

            title = "Today"
            award_title = "💀 Degenerate of the Day"

        elif period.value == "week":
            start = (
                now - timedelta(days=now.weekday())
            ).replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            end = start + timedelta(days=7)

            title = "This Week"
            award_title = "💀 Degenerate of the Week"

        else:
            start = now.replace(
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            if start.month == 12:
                end = start.replace(
                    year=start.year + 1,
                    month=1,
                )
            else:
                end = start.replace(
                    month=start.month + 1,
                )

            title = "This Month"
            award_title = "💀 Degenerate of the Month"

        # --------------------------------------
        # Fetch sessions
        # --------------------------------------

        rows = get_all_sessions_between(
            start,
            end,
        )

        if not rows:
            await interaction.followup.send(
                f"🎮 No gaming sessions recorded for {title.lower()}."
            )
            return

        # --------------------------------------
        # Calculate totals
        # --------------------------------------

        user_totals = defaultdict(float)

        user_game_totals = defaultdict(
            lambda: defaultdict(float)
        )

        for session in rows:
            session_start = max(
                session.started_at,
                start,
            )

            session_end = min(
                session.ended_at or now,
                end,
                now,
            )

            duration = (
                session_end - session_start
            ).total_seconds()

            if duration <= 0:
                continue

            user_id = session.discord_user_id

            user_totals[user_id] += duration

            user_game_totals[user_id][
                session.game_name
            ] += duration

        if not user_totals:
            await interaction.followup.send(
                "🎮 No gaming time found."
            )
            return

        # --------------------------------------
        # Ranking
        # --------------------------------------

        ranking = sorted(
            user_totals.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        medals = [
            "🥇",
            "🥈",
            "🥉",
        ]

        leaderboard_lines = []

        for index, (
            user_id,
            seconds,
        ) in enumerate(ranking[:10]):
            member = None

            if interaction.guild:
                member = interaction.guild.get_member(
                    user_id
                )

            if member:
                display_name = member.display_name
            else:
                display_name = f"<@{user_id}>"

            if index < len(medals):
                position = medals[index]
            else:
                position = f"`{index + 1}.`"

            leaderboard_lines.append(
                f"{position} **{display_name}** — "
                f"{format_duration(seconds)}"
            )

        # --------------------------------------
        # Winner
        # --------------------------------------

        winner_id, winner_seconds = ranking[0]

        winner_member = None

        if interaction.guild:
            winner_member = interaction.guild.get_member(
                winner_id
            )

        if winner_member:
            winner_name = winner_member.display_name
        else:
            winner_name = f"<@{winner_id}>"

        # --------------------------------------
        # Winner's most played game
        # --------------------------------------

        winner_games = user_game_totals[
            winner_id
        ]

        winner_top_game, winner_top_game_seconds = max(
            winner_games.items(),
            key=lambda item: item[1],
        )

        # --------------------------------------
        # Generate roast
        # --------------------------------------

        try:
            roast = generate_roast(
                username=winner_name,
                total_seconds=winner_seconds,
                top_game=winner_top_game,
            )

        except Exception as exc:
            print(
                f"Failed to generate roast: {exc}",
                flush=True,
            )

            roast = (
                "Bro put in a full gaming shift and somehow "
                "still forgot to clock in at a real job."
            )

        # --------------------------------------
        # Embed
        # --------------------------------------

        embed = discord.Embed(
            title=f"🏆 Gaming Top — {title}",
            colour=discord.Colour.orange(),
        )

        embed.description = "\n".join(
            leaderboard_lines
        )

        embed.add_field(
            name=award_title,
            value=(
                f"**{winner_name}**\n"
                f"🎮 {format_duration(winner_seconds)}\n"
                f"🏆 {winner_top_game} — "
                f"{format_duration(winner_top_game_seconds)}"
            ),
            inline=False,
        )

        embed.add_field(
            name="🍺 AI Verdict",
            value=roast,
            inline=False,
        )

        embed.set_footer(
            text="Go outside. The graphics are insane."
        )

        await interaction.followup.send(
            embed=embed,
        )


async def setup(
    bot: commands.Bot,
):
    await bot.add_cog(
        TopCommand(bot)
    )