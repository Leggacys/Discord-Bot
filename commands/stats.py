from collections import defaultdict
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands

from commands.today import format_duration
from database.game_session_repository import get_sessions_between


class StatsCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="stats",
        description="Show your gaming statistics.",
    )
    @app_commands.describe(
        period="Statistics period",
    )
    @app_commands.choices(
        period=[
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
        await interaction.response.defer()

        now = datetime.now(timezone.utc)

        if period.value == "week":
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

        rows = get_sessions_between(
            interaction.user.id,
            start,
            end,
        )

        if not rows:
            await interaction.followup.send(
                f"🎮 No gaming sessions recorded for {title.lower()}."
            )
            return

        game_totals = defaultdict(float)
        day_totals = defaultdict(float)
        hour_totals = defaultdict(float)

        total_seconds = 0
        longest_session = None
        longest_seconds = 0

        for session in rows:
            session_start = session.started_at
            session_end = session.ended_at or now

            duration = (
                session_end - session_start
            ).total_seconds()

            if duration <= 0:
                continue

            total_seconds += duration

            game_totals[session.game_name] += duration

            day_key = session_start.date()
            day_totals[day_key] += duration

            # Basic version:
            # attributes the session to the hour it started.
            hour_totals[session_start.hour] += duration

            if duration > longest_seconds:
                longest_seconds = duration
                longest_session = session

        if total_seconds <= 0:
            await interaction.followup.send(
                "🎮 No completed gaming time found."
            )
            return

        # --------------------------------------
        # Most played game
        # --------------------------------------

        most_played_game, most_played_seconds = max(
            game_totals.items(),
            key=lambda item: item[1],
        )

        # --------------------------------------
        # Most active day
        # --------------------------------------

        most_active_date, most_active_seconds = max(
            day_totals.items(),
            key=lambda item: item[1],
        )

        # --------------------------------------
        # Most active hour
        # --------------------------------------

        most_active_hour, _ = max(
            hour_totals.items(),
            key=lambda item: item[1],
        )

        next_hour = (most_active_hour + 1) % 24

        # --------------------------------------
        # Average
        # --------------------------------------

        active_days = len(day_totals)

        average_seconds = (
            total_seconds / active_days
            if active_days
            else 0
        )

        # --------------------------------------
        # Games list
        # --------------------------------------

        sorted_games = sorted(
            game_totals.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        game_lines = []

        for game, seconds in sorted_games[:5]:
            game_lines.append(
                f"**{game}** — {format_duration(seconds)}"
            )

        # --------------------------------------
        # Build embed
        # --------------------------------------

        embed = discord.Embed(
            title=f"📊 Gaming Statistics — {title}",
            colour=discord.Colour.blurple(),
        )

        embed.add_field(
            name="🎮 Total played",
            value=format_duration(total_seconds),
            inline=True,
        )

        embed.add_field(
            name="📅 Active days",
            value=str(active_days),
            inline=True,
        )

        embed.add_field(
            name="📈 Average / active day",
            value=format_duration(average_seconds),
            inline=True,
        )

        embed.add_field(
            name="🏆 Most played",
            value=(
                f"{most_played_game}\n"
                f"{format_duration(most_played_seconds)}"
            ),
            inline=True,
        )

        embed.add_field(
            name="🔥 Most active day",
            value=(
                f"{most_active_date.strftime('%A')}\n"
                f"{format_duration(most_active_seconds)}"
            ),
            inline=True,
        )

        embed.add_field(
            name="🕒 Most active time",
            value=(
                f"{most_active_hour:02d}:00–"
                f"{next_hour:02d}:00"
            ),
            inline=True,
        )

        if longest_session:
            embed.add_field(
                name="⏱️ Longest session",
                value=(
                    f"{longest_session.game_name}\n"
                    f"{format_duration(longest_seconds)}"
                ),
                inline=False,
            )

        embed.add_field(
            name="🎯 Games",
            value="\n".join(game_lines),
            inline=False,
        )

        await interaction.followup.send(
            embed=embed,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(
        StatsCommand(bot)
    )