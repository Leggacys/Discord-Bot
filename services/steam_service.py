import os
from dataclasses import dataclass

import aiohttp
from discord.ext import tasks
from dotenv import load_dotenv

from database.repositories.steam_repository import create_steam_session, get_tracking_playtime, get_users_with_steam_id, upsert_tracking_state


load_dotenv()


BASE_URL = "https://api.steampowered.com"


@dataclass
class SteamConfig:
    api_key: str


def get_steam_config() -> SteamConfig | None:
    api_key = os.getenv("STEAM_API_KEY")

    if not api_key:
        return None

    return SteamConfig(
        api_key=api_key,
    )


async def get_recently_played_games(
    steam_id: str,
    config: SteamConfig | None = None,
) -> list[dict]:
    if config is None:
        config = get_steam_config()

    if config is None:
        raise RuntimeError(
            "STEAM_API_KEY is missing"
        )

    url = (
        f"{BASE_URL}/"
        "IPlayerService/"
        "GetRecentlyPlayedGames/v0001/"
    )

    params = {
        "key": config.api_key,
        "steamid": steam_id,
        "format": "json",
    }

    timeout = aiohttp.ClientTimeout(
        total=10,
    )

    async with aiohttp.ClientSession(
        timeout=timeout,
    ) as session:
        async with session.get(
            url,
            params=params,
        ) as response:
            response.raise_for_status()

            data = await response.json()

    games = (
        data
        .get("response", {})
        .get("games", [])
    )

    return [
        {
            "app_id": game["appid"],
            "game_name": game.get(
                "name",
                f"App {game['appid']}",
            ),
            "playtime_forever": game.get(
                "playtime_forever",
                0,
            ),
            "playtime_2weeks": game.get(
                "playtime_2weeks",
                0,
            ),
        }
        for game in games
    ]


class SteamPlaytimePoller:
    def __init__(
        self,
        bot,
        config: SteamConfig,
    ):
        self.bot = bot
        self.config = config

    def start(self):
        if not self.poll.is_running():
            self.poll.start()

    def stop(self):
        if self.poll.is_running():
            self.poll.cancel()

    @tasks.loop(
    minutes=5,
    )
    async def poll(self):
        print(
            "Checking Steam playtime...",
            flush=True,
        )

        users = get_users_with_steam_id()

        if not users:
            print(
                "No Steam-linked users.",
                flush=True,
            )
            return

        for user in users:
            discord_user_id = user[
                "discord_user_id"
            ]

            username = user[
                "username"
            ]

            steam_id = user[
                "steam_id"
            ]

            try:
                games = await get_recently_played_games(
                    steam_id=steam_id,
                    config=self.config,
                )

            except Exception as exc:
                print(
                    f"Steam API failed for "
                    f"{username}: {exc}",
                    flush=True,
                )
                continue

            print(
                f"Steam returned {len(games)} games "
                f"for {username}.",
                flush=True,
            )

            for game in games:
                app_id = game[
                    "app_id"
                ]

                game_name = game[
                    "game_name"
                ]

                current_playtime = game[
                    "playtime_forever"
                ]

                previous_playtime = (
                    get_tracking_playtime(
                        discord_user_id=discord_user_id,
                        steam_app_id=app_id,
                    )
                )

                # First poll:
                # establish baseline only
                if previous_playtime is None:
                    upsert_tracking_state(
                        discord_user_id=discord_user_id,
                        steam_app_id=app_id,
                        game_name=game_name,
                        playtime_minutes=current_playtime,
                    )

                    print(
                        f"Steam baseline created: "
                        f"{username} / "
                        f"{game_name} = "
                        f"{current_playtime}m",
                        flush=True,
                    )

                    continue

                delta_minutes = (
                    current_playtime
                    - previous_playtime
                )

                # Always update baseline
                upsert_tracking_state(
                    discord_user_id=discord_user_id,
                    steam_app_id=app_id,
                    game_name=game_name,
                    playtime_minutes=current_playtime,
                )

                if delta_minutes <= 0:
                    continue

                # Safety protection
                if delta_minutes > 30:
                    print(
                        f"Suspicious Steam delta ignored: "
                        f"{username} / "
                        f"{game_name} / "
                        f"+{delta_minutes}m",
                        flush=True,
                    )
                    continue

                duration_seconds = (
                    delta_minutes * 60
                )

                create_steam_session(
                    discord_user_id=discord_user_id,
                    game_name=game_name,
                    duration_seconds=duration_seconds,
                )

                print(
                    f"Steam tracked: "
                    f"{username} played "
                    f"{game_name} for "
                    f"{delta_minutes}m",
                    flush=True,
                )


    @poll.before_loop
    async def before_poll(self):
        await self.bot.wait_until_ready()