import asyncio

from services.steam_service import (
    get_recently_played_games,
)


async def main():
    games = await get_recently_played_games(
        "76561198391836662"
    )

    if not games:
        print("No games returned.")
        return

    for game in games:
        print(
            game.get("name"),
            "-",
            game.get("playtime_forever"),
            "minutes total",
        )


asyncio.run(main())