import discord
import os
import google.generativeai as genai
import datetime
import pytz
import asyncio
import dateparser
import re
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

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
async def remind(ctx, *, message):
    now = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))  # Localized to IST
    reminder_time = parse_reminder_time(message, now)

    if not reminder_time:
        await ctx.send("❌ I couldn't understand the date/time. Try: `Remind me to submit my assignment tomorrow at 6 PM`")
        return

    if reminder_time.tzinfo is None:
        reminder_time = pytz.timezone("Asia/Kolkata").localize(reminder_time)

    delay = (reminder_time - now).total_seconds()
    if delay <= 0:
        await ctx.send("❌ The time must be in the future!")
        return

    await ctx.send(f"✅ Reminder set for {reminder_time}!")
    await asyncio.sleep(delay)
    await ctx.send(f"⏰ {ctx.author.mention} Reminder: {message}")

def parse_reminder_time(message, now):
    settings = {
        'TIMEZONE': 'Asia/Kolkata',
        'RETURN_AS_TIMEZONE_AWARE': True,
        'PREFER_DATES_FROM': 'future'
    }
    
    parsed_time = dateparser.parse(message, settings=settings)

    if not parsed_time:
        match = re.search(r"(\d{1,2}:\d{2}\s*(AM|PM)?)", message, re.IGNORECASE)
        if match:
            time_str = match.group(1)
            if "today" in message.lower():
                parsed_time = dateparser.parse(f"{now.strftime('%Y-%m-%d')} {time_str}", settings=settings)

    return parsed_time

bot.run(TOKEN)
