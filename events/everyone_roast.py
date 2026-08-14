import asyncio
import os
import time

import discord
from discord.ext import commands

from services.roast_service import (
    generate_everyone_roast,
)


WATCH_CHANNEL_ID = int(
    os.getenv("ROAST_CHANNEL_ID", "0")
)

COOLDOWN_SECONDS = 60

cooldowns: dict[int, float] = {}


class EveryoneRoastListener(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
    ):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(
        self,
        message: discord.Message,
    ):
        # Ignore bots
        if message.author.bot:
            return

        # Only watch configured channel
        if (
            WATCH_CHANNEL_ID
            and message.channel.id
            != WATCH_CHANNEL_ID
        ):
            return

        # Only @everyone
        # Does not trigger for @here
        if "@everyone" not in message.content:
            return

        now = time.monotonic()

        last_roast = cooldowns.get(
            message.author.id,
            0,
        )

        if (
            now - last_roast
            < COOLDOWN_SECONDS
        ):
            return

        cooldowns[
            message.author.id
        ] = now

        try:
            roast = await asyncio.to_thread(
                generate_everyone_roast,
                username=message.author.display_name,
                message_content=message.content,
            )

        except Exception as exc:
            print(
                f"Failed to generate @everyone roast: {exc}",
                flush=True,
            )

            roast = (
                "Ai dat @everyone pentru asta? "
                "Fă ceva cu viața ta, șefule."
            )

        await message.reply(
            roast,
            mention_author=False,
        )


async def setup(
    bot: commands.Bot,
):
    await bot.add_cog(
        EveryoneRoastListener(bot)
    )