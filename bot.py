import discord
import random
from discord.ext import commands
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

SOURCE_CHANNEL_ID = 1497296815559544862
TARGET_CHANNEL_ID = 1498464307195936858

SPECIAL_THREAD_IDS = {
    1498027467280089261,
    1498070775452925952,
    1498076218069614625,
    1498077077306605658,
    1498084047690399895,
    1498086692341682256
}


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


async def get_all_threads(channel):
    threads = []
    threads.extend(channel.threads)

    async for t in channel.archived_threads(limit=None):
        threads.append(t)

    return threads


async def get_thread_starter_message(thread):
    try:
        return await thread.fetch_message(thread.id)
    except:
        async for msg in thread.history(limit=1, oldest_first=True):
            return msg
    return None


def extract_text(message):
    parts = []

    if message.content:
        parts.append(message.content)

    if message.embeds:
        e = message.embeds[0]
        if e.title:
            parts.append(e.title)
        if e.description:
            parts.append(e.description)

    return "\n".join(parts).strip()


async def send_message_with_files(message, target_channel):
    content = extract_text(message)

    files = []
    for attachment in message.attachments:
        try:
            files.append(await attachment.to_file())
        except:
            pass

    if files:
        await target_channel.send(content=content or None, files=files)
    else:
        await target_channel.send(content=content or "(No content)")


async def pick_one(source_channel, target_channel):
    threads = await get_all_threads(source_channel)

    if not threads:
        await target_channel.send("No threads found.")
        return

    special = [t for t in threads if t.id in SPECIAL_THREAD_IDS]
    normal = [t for t in threads if t.id not in SPECIAL_THREAD_IDS]

    roll = random.random()

    if roll < 0.10 and special:
        chosen = random.choice(special)
    else:
        chosen = random.choice(normal if normal else threads)

    msg = await get_thread_starter_message(chosen)

    if not msg:
        await target_channel.send("(Empty thread)")
        return

    await send_message_with_files(msg, target_channel)


@bot.command()
async def roll(ctx, amount: int):
    if amount <= 0:
        await ctx.send("Give me a number above 0.")
        return

    if amount > 50:
        await ctx.send("Calm down. Max 50 rolls.")
        return

    source_channel = bot.get_channel(SOURCE_CHANNEL_ID)
    target_channel = bot.get_channel(TARGET_CHANNEL_ID)

    if not source_channel or not target_channel:
        await ctx.send("Channel not found.")
        return

    for i in range(amount):
        await pick_one(source_channel, target_channel)


bot.run(TOKEN)
