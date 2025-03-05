import discord
import os
import google.generativeai as genai
import asyncio
import pytz
import yt_dlp

from discord.ext import commands, tasks
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Bot Setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True  # Required for welcome messages
bot = commands.Bot(command_prefix="!", intents=intents)

# Global Data Storage
reminder_data = {}
reminder_id = 1
polls = {}
queues = {}


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    check_expired_reminders.start()  # Start auto-delete task


@bot.command()
async def chat(ctx, *, message):
    await ctx.send("🤖 Thinking...")
    model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
    response = model.generate_content(message)
    await ctx.send(response.text if response.text else "Sorry, I couldn't generate a response.")


@bot.command()
async def remind(ctx, date: str, time: str, *, message: str):
    global reminder_id
    user_tz = pytz.timezone("Asia/Kolkata")

    try:
        reminder_time = datetime.strptime(f"{date} {time}", "%d-%m-%Y %H:%M")
        reminder_time = user_tz.localize(reminder_time)
    except ValueError:
        await ctx.send("❌ Invalid date format! Use: `DD-MM-YYYY HH:MM`.")
        return

    now = datetime.now(user_tz)
    delay = (reminder_time - now).total_seconds()
    if delay <= 0:
        await ctx.send("❌ Time must be in the future!")
        return

    reminder_data[reminder_id] = {"user": ctx.author.id, "time": reminder_time, "message": message}
    await ctx.send(f"✅ Reminder set for {reminder_time.strftime('%Y-%m-%d %H:%M:%S %Z')}!")

    async def send_reminder(rid):
        await asyncio.sleep(delay)
        user = await bot.fetch_user(reminder_data[rid]["user"])
        await user.send(f"🔔 Reminder: {reminder_data[rid]['message']}")

    bot.loop.create_task(send_reminder(reminder_id))
    reminder_id += 1

@tasks.loop(seconds=30)
async def check_expired_reminders():
    """Background task to clean up expired reminders."""
    now = datetime.now(pytz.timezone("Asia/Kolkata"))
    expired = [rid for rid, reminder in reminder_data.items() if reminder["time"] < now]

    for rid in expired:
        del reminder_data[rid]

    if expired:
        print(f"✅ Deleted {len(expired)} expired reminders.")

@bot.command()
async def reminders(ctx):
    if not reminder_data:
        await ctx.send("📌 No active reminders.")
        return

    response = "**📅 Active Reminders:**\n"
    for rid, reminder in reminder_data.items():
        user = await bot.fetch_user(reminder["user"])
        time = reminder["time"].strftime('%Y-%m-%d %H:%M:%S %Z')
        response += f"🔹 ID: {rid} | {time} - {reminder['message']} (for {user.mention})\n"

    await ctx.send(response)

@bot.command()
async def delete_reminder(ctx, rid: int):
    if rid in reminder_data and reminder_data[rid]["user"] == ctx.author.id:
        del reminder_data[rid]
        await ctx.send(f"✅ Reminder {rid} deleted!")
    else:
        await ctx.send("❌ Reminder not found or you don't have permission to delete it.")


@bot.command()
async def poll(ctx, question: str, *options):
    if len(options) < 2 or len(options) > 10:
        await ctx.send("❌ You need between 2 and 10 options for a poll.")
        return

    reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    embed = discord.Embed(title="📊 Poll", description=question, color=discord.Color.blue())

    poll_message = ""
    for i, option in enumerate(options):
        poll_message += f"{reactions[i]} {option}\n"

    embed.add_field(name="Options:", value=poll_message, inline=False)
    poll_msg = await ctx.send(embed=embed)

    for i in range(len(options)):
        await poll_msg.add_reaction(reactions[i])

    polls[poll_msg.id] = {"question": question, "options": options, "author": ctx.author.id}

@bot.command()
async def close_poll(ctx, message_id: int):
    if message_id not in polls:
        await ctx.send("❌ Poll not found.")
        return

    poll = polls[message_id]
    poll_message = await ctx.channel.fetch_message(message_id)
    
    results = {}
    for reaction in poll_message.reactions:
        if reaction.emoji in ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]:
            results[reaction.emoji] = reaction.count - 1

    result_text = "**📊 Poll Results:**\n"
    for i, option in enumerate(poll["options"]):
        result_text += f"{option}: {results.get(['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'][i], 0)} votes\n"

    embed = discord.Embed(title="📊 Poll Closed", description=result_text, color=discord.Color.red())
    await ctx.send(embed=embed)

    del polls[message_id]


@bot.command()
async def play(ctx, url):
    guild_id = ctx.guild.id

    if guild_id not in queues:
        queues[guild_id] = []

    queues[guild_id].append(url)

    if not ctx.voice_client:
        channel = ctx.author.voice.channel
        await channel.connect()

    if len(queues[guild_id]) == 1:
        await play_next(ctx)

async def play_next(ctx):
    guild_id = ctx.guild.id
    if not queues[guild_id]:
        return

    url = queues[guild_id].pop(0)
    
    ffmpeg_options = {'options': '-vn'}
    ydl_options = {'format': 'bestaudio'}

    with yt_dlp.YoutubeDL(ydl_options) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info['url']

    ctx.voice_client.play(discord.FFmpegPCMAudio(audio_url, **ffmpeg_options), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))

@bot.command()
async def queue(ctx):
    guild_id = ctx.guild.id
    if guild_id in queues and queues[guild_id]:
        await ctx.send(f"🎶 Queue:\n" + "\n".join(queues[guild_id]))
    else:
        await ctx.send("❌ No songs in queue.")

@bot.command()
async def skip(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await play_next(ctx)

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()


@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="welcome")
    if channel:
        await channel.send(f"🎉 Welcome {member.mention} to {member.guild.name}! Enjoy your stay!")

bot.run(TOKEN)
