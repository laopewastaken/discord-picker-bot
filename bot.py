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
ALLOWED_CHANNEL_ID = 1498464307195936858  # channel where !roll is allowed

# 🔵 COMMON THREADS (YOU MUST DEFINE THESE)
COMMON_THREAD_IDS = {
    1497297219328409673,
    1497297722947010591,
    1497298131971211304,
    1497299464048873692,
    1497300316910260314,
    1497301044873396374
}

# 🔴 SPECIAL THREADS
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
# THREAD + MESSAGE LOADING
# ─────────────────────────────

async def get_all_threads(channel):
    threads = []
    threads.extend(channel.threads)

    async for t in channel.archived_threads(limit=None):
        threads.append(t)

    return threads


async def collect_messages(channel):
    """
    Builds TWO pools:
    - common messages
    - special messages
    """

    threads = await get_all_threads(channel)

    common_msgs = []
    special_msgs = []

    for thread in threads:

        # ignore unrelated threads completely
        if thread.id not in COMMON_THREAD_IDS and thread.id not in SPECIAL_THREAD_IDS:
            continue

        is_special = thread.id in SPECIAL_THREAD_IDS

        async for msg in thread.history(limit=100):
            if msg.author.bot:
                continue

            if is_special:
                special_msgs.append(msg)
            else:
                common_msgs.append(msg)

    return common_msgs, special_msgs


# ─────────────────────────────
# MESSAGE HANDLING
# ─────────────────────────────

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


async def send_message(message, channel):
    content = extract_text(message)

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
# MAIN ROLL LOGIC
# ─────────────────────────────

@bot.command()
async def roll(ctx, amount: int):
    
    # 🚫 ADD THIS BLOCK
    if ctx.channel.id != ALLOWED_CHANNEL_ID:
        return
    
    global special_count, normal_count

    if amount <= 0:
        await ctx.send("Give me a number above 0.")
        return

    if amount > 100:
        await ctx.send("Max 100 rolls.")
        return

    source = bot.get_channel(SOURCE_CHANNEL_ID)
    target = bot.get_channel(TARGET_CHANNEL_ID)

    if not source or not target:
        await ctx.send("Channel not found.")
        return

    common_msgs, special_msgs = await collect_messages(source)

    if not common_msgs and not special_msgs:
        await ctx.send("No messages found.")
        return

    random.shuffle(common_msgs)
    random.shuffle(special_msgs)

    used = set()
    sent = 0
    attempts = 0
    max_attempts = amount * 10

    while sent < amount and attempts < max_attempts:
        attempts += 1

        # 🎯 10% special chance
        use_special = special_msgs and random.random() < 0.10

        if use_special:
            pool = special_msgs
            is_special = True
        else:
            pool = common_msgs if common_msgs else special_msgs
            is_special = False

        if not pool:
            continue

        msg = random.choice(pool)

        if msg.id in used:
            continue

        used.add(msg.id)

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
