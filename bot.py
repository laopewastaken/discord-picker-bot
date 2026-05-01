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
TARGET_CHANNEL_ID = 1499835814832504893

SPECIAL_THREAD_IDS = {
    1498027467280089261,
    1498070775452925952,
    1498076218069614625,
    1498077077306605658,
    1498084047690399895,
    1498086692341682256
}

special_count = 0
normal_count = 0


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


# 🔥 FIXED: proper probability picker (NO FAKE DECK)
def pick_thread(threads):
    special = [t for t in threads if t.id in SPECIAL_THREAD_IDS]
    normal = [t for t in threads if t.id not in SPECIAL_THREAD_IDS]

    roll = random.random()

    if roll < 0.10 and special:
        return random.choice(special), True
    else:
        return random.choice(normal if normal else threads), False


@bot.command()
async def roll(ctx, amount: int):
    if amount <= 0:
        await ctx.send("Give me a number above 0.")
        return

    if amount > 100:
        await ctx.send("Max 100 rolls.")
        return

    source_channel = bot.get_channel(SOURCE_CHANNEL_ID)
    target_channel = bot.get_channel(TARGET_CHANNEL_ID)

    if not source_channel or not target_channel:
        await ctx.send("Channel not found.")
        return

    threads = await get_all_threads(source_channel)

    if not threads:
        await ctx.send("No threads found.")
        return

    global special_count, normal_count

    used = set()
    sent = 0
    attempts = 0
    max_attempts = amount * 10  # safety buffer

    while sent < amount and attempts < max_attempts:
        attempts += 1

        chosen, is_special = pick_thread(threads)

        # 🚫 no repeats per roll
        if chosen.id in used:
            continue

        msg = await get_thread_starter_message(chosen)

        if not msg:
            continue  # do NOT consume slot

        used.add(chosen.id)

        await send_message_with_files(msg, target_channel)

        if is_special:
            special_count += 1
        else:
            normal_count += 1

        sent += 1


@bot.command()
async def stats(ctx):
    total = special_count + normal_count

    if total == 0:
        await ctx.send("No rolls yet.")
        return

    await ctx.send(
        f"📊 **Roll Stats**\n"
        f"Special: {special_count} ({(special_count/total)*100:.1f}%)\n"
        f"Normal: {normal_count} ({(normal_count/total)*100:.1f}%)\n"
        f"Total: {total}"
    )


@bot.command()
async def resetstats(ctx):
    global special_count, normal_count
    special_count = 0
    normal_count = 0
    await ctx.send("📊 Stats reset.")


bot.run(TOKEN)
