import discord
import os
import google.generativeai as genai
import asyncio
import pytz
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

reminder_data = {}
reminder_id = 1
polls = {}

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

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
        del reminder_data[rid]

    bot.loop.create_task(send_reminder(reminder_id))
    reminder_id += 1

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
async def modify_reminder(ctx, rid: int, new_date: str, new_time: str, *, new_message: str):
    user_tz = pytz.timezone("Asia/Kolkata")

    if rid not in reminder_data or reminder_data[rid]["user"] != ctx.author.id:
        await ctx.send("❌ Reminder not found or you don't have permission to modify it.")
        return

    try:
        new_reminder_time = datetime.strptime(f"{new_date} {new_time}", "%d-%m-%Y %H:%M")
        new_reminder_time = user_tz.localize(new_reminder_time)
    except ValueError:
        await ctx.send("❌ Invalid date format! Use: `DD-MM-YYYY HH:MM`.")
        return

    now = datetime.now(user_tz)
    if (new_reminder_time - now).total_seconds() <= 0:
        await ctx.send("❌ Time must be in the future!")
        return

    reminder_data[rid] = {"user": ctx.author.id, "time": new_reminder_time, "message": new_message}
    await ctx.send(f"✅ Reminder {rid} updated to {new_reminder_time.strftime('%Y-%m-%d %H:%M:%S %Z')}!")

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
async def summarize(ctx, *, message: str):
    """Summarizes a long message using AI."""
    if len(message) < 50:
        await ctx.send("📢 Message is too short to summarize.")
        return

    await ctx.send("🤖 Summarizing...")

    model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
    prompt = f"Summarize the following text concisely:\n\n{message}"
    response = model.generate_content(prompt)

    summary = response.text if response.text else "Sorry, I couldn't generate a summary."
    await ctx.send(f"📜 **Summary:** {summary}")
@bot.event
async def on_member_join(member):
    print(f"DEBUG: {member.name} joined!")  # Debugging

    # Get or create a welcome channel
    channel = discord.utils.get(member.guild.text_channels, name="welcome")
    if not channel:
        print("DEBUG: No welcome channel found.")
        return

    await channel.send(f"🎉 Welcome {member.mention} to {member.guild.name}! Enjoy your stay!")
bot.run(TOKEN)
