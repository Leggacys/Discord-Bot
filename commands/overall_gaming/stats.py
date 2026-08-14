from collections import defaultdict
from datetime import datetime, timedelta, timezone

import discord

from commands.overall_gaming.today import format_duration
from database.repositories.game_session_repository import (
    get_sessions_between,
)


def add_session_to_hours(
    hour_totals: dict[int, float],
    session_start: datetime,
    session_end: datetime,
) -> None:
    current = session_start

    while current < session_end:
        next_hour = current.replace(
            minute=0,
            second=0,
            microsecond=0,
        ) + timedelta(hours=1)

        chunk_end = min(
            next_hour,
            session_end,
        )

        seconds = (
            chunk_end - current
        ).total_seconds()

        hour_totals[current.hour] += seconds

        current = chunk_end


def add_session_to_days(
    day_totals: dict,
    session_start: datetime,
    session_end: datetime,
) -> None:
    current = session_start

    while current < session_end:
        next_day = (
            current.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
            + timedelta(days=1)
        )

        chunk_end = min(
            next_day,
            session_end,
        )

        seconds = (
            chunk_end - current
        ).total_seconds()

        day_totals[
            current.date()
        ] += seconds

        current = chunk_end



def calculate_late_night_seconds(
    session_start: datetime,
    session_end: datetime,
) -> float:
    total = 0.0
    current = session_start

    while current < session_end:
        next_hour = (
            current.replace(
                minute=0,
                second=0,
                microsecond=0,
            )
            + timedelta(hours=1)
        )

        chunk_end = min(
            next_hour,
            session_end,
        )

        if (
            current.hour >= 22
            or current.hour < 5
        ):
            total += (
                chunk_end - current
            ).total_seconds()

        current = chunk_end

    return total



def merge_session_intervals(
    intervals: list[dict],
    max_gap_minutes: int = 10,
) -> list[dict]:
    """
    Reconstruct real gaming sessions.

    Discord rows already represent real start/stop sessions, so they are
    kept separate.

    Steam rows are polling chunks. Consecutive Steam chunks for the same
    game are merged when the gap between them is small.
    """
    if not intervals:
        return []

    sorted_intervals = sorted(
        intervals,
        key=lambda item: item["start"],
    )

    merged = []

    max_gap = timedelta(
        minutes=max_gap_minutes,
    )

    for interval in sorted_intervals:
        current = interval.copy()

        if not merged:
            merged.append(current)
            continue

        previous = merged[-1]

        both_steam = (
            previous["source"] == "steam"
            and current["source"] == "steam"
        )

        same_game = (
            previous["game_name"]
            == current["game_name"]
        )

        close_enough = (
            current["start"]
            <= previous["end"] + max_gap
        )

        if (
            both_steam
            and same_game
            and close_enough
        ):
            previous["end"] = max(
                previous["end"],
                current["end"],
            )
        else:
            merged.append(current)

    return merged



def build_insight(
    *,
    total_seconds: float,
    active_days: int,
    session_count: int,
    average_session_seconds: float,
    late_night_percentage: float,
    most_played_game: str,
    most_played_percentage: float,
) -> str:
    total_hours = (
        total_seconds / 3600
    )

    if (
        late_night_percentage >= 40
        and total_seconds >= 2 * 3600
    ):
        return (
            f"{late_night_percentage:.0f}% of your gaming "
            "happened between 22:00 and 05:00. "
            "A large part of your gaming is happening late at night."
        )

    if (
        average_session_seconds
        >= 3 * 3600
    ):
        return (
            "Your sessions are quite long — "
            f"you averaged "
            f"{format_duration(average_session_seconds)} "
            "each time you played."
        )

    if (
        active_days <= 2
        and total_hours >= 6
    ):
        return (
            f"You accumulated {format_duration(total_seconds)} "
            f"across only {active_days} active days. "
            "Your gaming is concentrated into a few heavy days."
        )

    if most_played_percentage >= 80:
        return (
            f"{most_played_game} accounted for "
            f"{most_played_percentage:.0f}% of your gaming time. "
            "Most of your gaming is currently concentrated "
            "in one game."
        )

    if session_count >= 10:
        return (
            f"You had about {session_count} gaming sessions "
            "during this period. Your gaming is spread across "
            "many separate sessions."
        )

    return (
        "Your gaming was relatively spread out during "
        "this period, without one particularly strong pattern."
    )


async def handle_stats(
    interaction: discord.Interaction,
    period: str,
):
    await interaction.response.defer()

    now = datetime.now(
        timezone.utc
    )


    if period == "today":
        start = now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        end = now
        title = "Today"

    elif period == "week":
        start = (
            now
            - timedelta(
                days=now.weekday()
            )
        ).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        end = (
            start
            + timedelta(days=7)
        )

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
            f"🎮 No gaming sessions recorded "
            f"for {title.lower()}."
        )
        return


    game_totals = defaultdict(float)
    day_totals = defaultdict(float)
    hour_totals = defaultdict(float)
    session_intervals = []

    total_seconds = 0.0
    late_night_seconds = 0.0

    longest_game = None
    longest_seconds = 0.0


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
            session_end
            - session_start
        ).total_seconds()

        if duration <= 0:
            continue

        total_seconds += duration

        game_totals[
            session.game_name
        ] += duration

    
        add_session_to_days(
            day_totals,
            session_start,
            session_end,
        )

   
        add_session_to_hours(
            hour_totals,
            session_start,
            session_end,
        )

  
        late_night_seconds += (
            calculate_late_night_seconds(
                session_start,
                session_end,
            )
        )

        source = (
            getattr(
                session,
                "source",
                None,
            )
            or "discord"
        )

        session_intervals.append(
            {
                "game_name": session.game_name,
                "start": session_start,
                "end": session_end,
                "source": source,
            }
        )

      
        if duration > longest_seconds:
            longest_seconds = duration
            longest_game = (
                session.game_name
            )

    if total_seconds <= 0:
        await interaction.followup.send(
            "🎮 No gaming time found."
        )
        return

    merged_sessions = (
        merge_session_intervals(
            session_intervals
        )
    )

    session_count = len(
        merged_sessions
    )

    reconstructed_session_seconds = sum(
        (
            item["end"]
            - item["start"]
        ).total_seconds()
        for item in merged_sessions
    )

    if merged_sessions:
        longest_merged = max(
            merged_sessions,
            key=lambda item: (
                item["end"]
                - item["start"]
            ).total_seconds(),
        )

        longest_seconds = (
            longest_merged["end"]
            - longest_merged["start"]
        ).total_seconds()

        longest_game = (
            longest_merged[
                "game_name"
            ]
        )


    (
        most_played_game,
        most_played_seconds,
    ) = max(
        game_totals.items(),
        key=lambda item: item[1],
    )

    (
        most_active_date,
        most_active_seconds,
    ) = max(
        day_totals.items(),
        key=lambda item: item[1],
    )

    (
        most_active_hour,
        _,
    ) = max(
        hour_totals.items(),
        key=lambda item: item[1],
    )

    next_hour = (
        most_active_hour + 1
    ) % 24

    active_days = len(
        day_totals
    )

    average_day_seconds = (
        total_seconds
        / active_days
        if active_days
        else 0
    )

    average_session_seconds = (
        reconstructed_session_seconds
        / session_count
        if session_count
        else 0
    )

    late_night_percentage = (
        late_night_seconds
        / total_seconds
        * 100
        if total_seconds
        else 0
    )

    most_played_percentage = (
        most_played_seconds
        / total_seconds
        * 100
        if total_seconds
        else 0
    )


    sorted_games = sorted(
        game_totals.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    game_lines = []

    for game, seconds in sorted_games[:5]:
        percentage = (
            seconds
            / total_seconds
            * 100
        )

        game_lines.append(
            f"• **{game}**\n"
            f"  {format_duration(seconds)} "
            f"• {percentage:.0f}%"
        )


    insight = build_insight(
        total_seconds=total_seconds,
        active_days=active_days,
        session_count=session_count,
        average_session_seconds=(
            average_session_seconds
        ),
        late_night_percentage=(
            late_night_percentage
        ),
        most_played_game=(
            most_played_game
        ),
        most_played_percentage=(
            most_played_percentage
        ),
    )


    embed = discord.Embed(
        title=f"📊 Gaming Statistics — {title}",
        description=(
            f"🎮 **{format_duration(total_seconds)} played** "
            f"across **{active_days} active days**\n"
            f"📈 **{format_duration(average_day_seconds)} "
            f"per active day**"
        ),
        colour=discord.Colour.blurple(),
    )

    embed.add_field(
        name="🏆 Main game",
        value=(
            f"**{most_played_game}**\n"
            f"{format_duration(most_played_seconds)} "
            f"• {most_played_percentage:.0f}% of total"
        ),
        inline=False,
    )

    embed.add_field(
        name="🔥 Peak activity",
        value=(
            f"**{most_active_date.strftime('%A')}** "
            f"• {format_duration(most_active_seconds)}\n"
            f"Peak hour: "
            f"**{most_active_hour:02d}:00–"
            f"{next_hour:02d}:00**"
        ),
        inline=True,
    )

    embed.add_field(
        name="⏱️ Sessions",
        value=(
            f"**{session_count} sessions**\n"
            f"Avg: "
            f"{format_duration(average_session_seconds)}\n"
            f"Longest: "
            f"{format_duration(longest_seconds)}"
        ),
        inline=True,
    )

    embed.add_field(
        name="🌙 Late night",
        value=(
            f"**{format_duration(late_night_seconds)}**\n"
            f"{late_night_percentage:.0f}% of total"
        ),
        inline=True,
    )

    embed.add_field(
        name="🎯 Games",
        value="\n".join(
            game_lines
        ),
        inline=False,
    )

    embed.add_field(
        name="🧠 Your pattern",
        value=insight,
        inline=False,
    )

    embed.set_footer(
        text=(
            "Steam polling chunks are merged into estimated sessions; "
            "Discord sessions keep their original boundaries."
        )
    )

    await interaction.followup.send(
        embed=embed,
    )