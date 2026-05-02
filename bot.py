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

# 🔵 DEFINE YOUR THREAD GROUPS HERE (REQUIRED)
COMMON_THREAD_IDS = {
        1497297219328409673,
    1497297722947010591,
    1497298131971211304,
    1497299464048873692,
    1497300316910260314,
    1497301044873396374
}

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


# ─────────────────────────────
# THREAD FETCH
# ─────────────────────────────

async def get_all_threads(channel):
    threads = []
    threads.extend(channel.threads)

    async for t in channel.archived_threads(limit=None):
        threads.append(t)

    return threads


def extract_message_content(message):
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


async def get_first_message(thread):
    try:
        return await thread.fetch_message(thread.id)
    except:
        async for msg in thread.history(limit=1, oldest_first=True):
            return msg
    return None


async def send_message(message, channel):
    content = extract_message_content(message)

    files = []
    for att in message.attachments:
        try:
            files.append(await att.to_file())
        except:
            pass

    if files:
        await channel.send(content=content or None, files=files)
    else:
        await channel.send(content=content or "(No content)")


# ─────────────────────────────
# CORE PICK LOGIC (CLEAN)
# ─────────────────────────────

def pick_from_pool(pool, used):
    available = [t for t in pool if t.id not in used]
    if not available:
        return None
    return random.choice(available)


@bot.command()
async def roll(ctx, amount: int):
    global special_count, normal_count

    if amount <= 0:
        await ctx.send("Give me a number above 0.")
        return

    source = bot.get_channel(SOURCE_CHANNEL_ID)
    target = bot.get_channel(TARGET_CHANNEL_ID)

    if not source or not target:
        await ctx.send("Channel not found.")
        return

    threads = await get_all_threads(source)

    common = [t for t in threads if t.id in COMMON_THREAD_IDS]
    special = [t for t in threads if t.id in SPECIAL_THREAD_IDS]

    if not common and not special:
        await ctx.send("No threads configured.")
        return

    used = set()
    sent = 0

    while sent < amount:

        # 🎯 decide pool ONCE per pick
        if special and random.random() < 0.10:
            pool = special
            is_special = True
        else:
            pool = common if common else special
            is_special = False

        chosen = pick_from_pool(pool, used)

        if not chosen:
            # fallback: try opposite pool
            pool = common if pool == special else special
            chosen = pick_from_pool(pool, used)

        if not chosen:
            break  # nothing left

        msg = await get_first_message(chosen)

        if not msg:
            used.add(chosen.id)
            continue

        used.add(chosen.id)

        await send_message(msg, target)

        if is_special:
            special_count += 1
        else:
            normal_count += 1

        sent += 1


# ─────────────────────────────
# STATS
# ─────────────────────────────

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
