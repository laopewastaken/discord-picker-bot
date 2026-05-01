import discord
import random
from discord.ext import commands

import os
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True  # REQUIRED

bot = commands.Bot(command_prefix="!", intents=intents)

SOURCE_CHANNEL_ID = 1234567890
TARGET_CHANNEL_ID = 9876543210

SPECIAL_THREAD_IDS = {1111, 2222, 3333}


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


async def get_all_threads(channel):
    threads = []

    # active threads
    threads.extend(channel.threads)

    # archived threads
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


def extract_content(message):
    # 1. plain text
    if message.content:
        return message.content.strip()

    # 2. embeds
    if message.embeds:
        embed = message.embeds[0]
        if embed.title and embed.description:
            return f"{embed.title}\n{embed.description}"
        elif embed.title:
            return embed.title
        elif embed.description:
            return embed.description

    # 3. attachments
    if message.attachments:
        return message.attachments[0].url

    return "(No usable content)"


async def pick_one(source_channel):
    threads = await get_all_threads(source_channel)

    if not threads:
        return None

    special = [t for t in threads if t.id in SPECIAL_THREAD_IDS]
    normal = [t for t in threads if t.id not in SPECIAL_THREAD_IDS]

    if random.random() < 0.10 and special:
        chosen = random.choice(special)
    else:
        chosen = random.choice(normal if normal else threads)

    msg = await get_thread_starter_message(chosen)

    if not msg:
        return "(Thread empty)"

    return extract_content(msg)


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

    results = []

    for _ in range(amount):
        result = await pick_one(source_channel)
        if result:
            results.append(f"🎯 {result}")

    # Send in chunks (Discord has message length limits)
    chunk = ""
    for r in results:
        if len(chunk) + len(r) > 1900:
            await target_channel.send(chunk)
            chunk = ""
        chunk += r + "\n"

    if chunk:
        await target_channel.send(chunk)


bot.run(TOKEN)