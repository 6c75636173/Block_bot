import discord
import os

from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError(
        os.error("TOKEN environment variable not set. Please set it in your .env file or system environment variables.")
    )
os.success("TOKEN environment variable loaded successfully.")
bot.run(TOKEN) 