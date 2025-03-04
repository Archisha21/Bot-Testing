import discord
import os
import google.generativeai as genai  
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
    """Handles user messages and replies using Gemini AI."""
    await ctx.send("🤖 Thinking...")

    model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
    response = model.generate_content(message)

    await ctx.send(response.text if response.text else "Sorry, I couldn't generate a response.")


bot.run(TOKEN)
