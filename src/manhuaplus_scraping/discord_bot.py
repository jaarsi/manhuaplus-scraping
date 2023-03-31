import discord
from discord.ext.commands import Bot, Context

from .scraper import Serie, check_new_chapter


def make_discord_bot(discord_token: str, series: list[Serie]):
    _series = {item["store_key"]: item for item in series}
    intents = discord.Intents.default()
    intents.message_content = True
    bot = Bot("/", intents=intents)

    @bot.command("check-serie")
    async def _(ctx: Context, serie_name: str):
        if not (serie := _series.get(serie_name, None)):
            await ctx.send(f"Serie {serie_name} is not registered.")
            return

        last_chapter = check_new_chapter(serie)
        message = (
            f">>> **[ {serie['title']} ] Last Chapter Available "
            f"=> [{last_chapter['chapter_number']}]**\n"
            f"{last_chapter['chapter_description']} \n"
            f"{last_chapter['chapter_url']}"
        )
        await ctx.send(message)

    @bot.command("list-series")
    async def _(ctx: Context):
        message = "\n".join(_series.keys())
        await ctx.send(message)

    return bot.run(discord_token)
