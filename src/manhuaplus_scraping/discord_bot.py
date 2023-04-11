import asyncio
from datetime import datetime, timedelta

import arrow
import discord

from .scraper import Serie, fetch_last_chapter, next_checking_seconds

GUILD_IDS = [961618505017483374]


def make_discord_bot(discord_token: str, series: list[Serie]):
    _series = {item["store_key"]: item for item in series}
    bot = discord.Bot(intents=discord.Intents.all())

    @bot.slash_command(name="waitfor", guild_ids=GUILD_IDS)
    async def _(ctx: discord.ApplicationContext, t: int):
        await ctx.respond(f"waiting for {t} seconds")
        await asyncio.sleep(t)
        await ctx.respond("Done")

    @bot.slash_command(name="last-chapter", guild_ids=GUILD_IDS)
    @discord.option("serie_name", choices=[*_series.keys()])
    async def _(ctx: discord.ApplicationContext, serie_name: str):
        if not (serie := _series.get(serie_name, None)):
            await ctx.respond(f"Serie {serie_name} is not registered.")
            return

        await ctx.respond(
            f"**Wait while im fetching the last chapter from {serie_name} ...**"
        )
        last_chapter = await asyncio.to_thread(fetch_last_chapter, serie)
        message = (
            f">>> **[ {serie['title']} ] Last Chapter Available "
            f"=> [{last_chapter['chapter_number']}]**\n"
            f"{last_chapter['chapter_description']} \n"
            f"{last_chapter['chapter_url']}"
        )
        await ctx.respond(message)

    @bot.slash_command(name="list-series", guild_ids=GUILD_IDS)
    async def _(ctx: discord.ApplicationContext):
        message = "\n".join(_series.keys())
        await ctx.respond(message)

    @bot.slash_command(name="next-check", guild_ids=GUILD_IDS)
    async def _(ctx: discord.ApplicationContext):
        now = datetime.now()
        message = ""

        for _, serie in _series.items():
            next_checking_at = now + timedelta(
                seconds=next_checking_seconds(now, serie), minutes=1
            )
            human_time = arrow.get(next_checking_at).humanize(
                other=now, granularity=["hour", "minute"]
            )
            message += f"**[ {serie['title']} ]** Next checking **{human_time}.**\n"

        await ctx.respond(message.strip())

    return bot.start(discord_token)
