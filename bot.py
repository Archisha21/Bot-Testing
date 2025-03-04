import discord
import os
import google.generativeai as genai
import datetime
import asyncio
import pytz
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

# Detect user's timezone automatically
LOCAL_TIMEZONE = pytz.timezone("Asia/Kolkata")  # Change this to your timezone if needed

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def remind(ctx, date: str, time: str, *, reminder_text: str):
    """Set a reminder using specific date/time format: DD-MM-YYYY HH:MM Reminder Text (Your Local Time)"""
    try:
        # Convert input to local timezone
        reminder_time = datetime.datetime.strptime(f"{date} {time}", "%d-%m-%Y %H:%M")
        reminder_time = LOCAL_TIMEZONE.localize(reminder_time)  

        now = datetime.datetime.now(LOCAL_TIMEZONE)

        if reminder_time < now:
            await ctx.send("❌ The time is in the past! Try a future time.")
            return

        delay = (reminder_time - now).total_seconds()

        await ctx.send(f"✅ Reminder set for {reminder_time.strftime('%Y-%m-%d %H:%M:%S %Z')}!")

        await asyncio.sleep(delay)
        await ctx.send(f"🔔 **Reminder:** {ctx.author.mention} {reminder_text}")

    except ValueError:
        await ctx.send("❌ Invalid format! Use: `!remind DD-MM-YYYY HH:MM Your reminder text`")

@bot.command()
async def chat(ctx, *, message):
    """Handles user messages and replies using Gemini AI."""
    await ctx.send("🤖 Thinking...")

    model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
    response = model.generate_content(message)

    await ctx.send(response.text if response.text else "Sorry, I couldn't generate a response.")

bot.run(TOKEN)
