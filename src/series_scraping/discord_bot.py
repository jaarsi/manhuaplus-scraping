import asyncio
from datetime import datetime, timedelta

import arrow
import discord

from . import types, scraper

GUILD_IDS = [961618505017483374]


def start_discord_bot(discord_token: str, serie_list: list[types.Serie]):
    _series = {item["id"]: item for item in serie_list}
    bot = discord.Bot(intents=discord.Intents.all())

    @bot.slash_command(name="wait-for", guild_ids=GUILD_IDS)
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
        last_chapter = await scraper.fetch_last_chapter(serie)
        message = (
            f">>> **[ {serie['title']} ] Last Chapter Available "
            f"=> [{last_chapter['chapter_number']}]**\n"
            f"{last_chapter['chapter_description']} \n"
            f"{last_chapter['chapter_url']}"
        )
        await ctx.respond(message)

    @bot.slash_command(name="list-series", guild_ids=GUILD_IDS)
    async def _(ctx: discord.ApplicationContext):
        await ctx.respond("\n".join(_series.keys()))

    @bot.slash_command(name="next-check", guild_ids=GUILD_IDS)
    async def _(ctx: discord.ApplicationContext):
        now = datetime.now()
        message = ""

        for _, serie in _series.items():
            next_checking_at = now + timedelta(
                seconds=scraper.next_checking_seconds(serie, now), minutes=1
            )
            human_time = arrow.get(next_checking_at).humanize(
                other=now, granularity=["hour", "minute"]
            )
            message += f"**[ {serie['title']} ]** Next checking **{human_time}.**\n"

        await ctx.respond(message.strip())

    return bot.start(discord_token)
