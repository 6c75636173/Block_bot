import discord
import os
import sys

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

import core
import cogs
import data

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

async def setup_hook_func():
    await cogs.ping.setup(bot)

bot.setup_hook = setup_hook_func

@bot.event
async def on_ready():

    print(
        f"\033[92m[ONLINE]\033[0m "
        f"{bot.user} is connected !"
    )

    print(
        f"\033[96m[INFO]\033[0m "
        f"bot ID : {bot.user.id}"
    )

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN environment variable not set. "
        "Please set it in your .env file."
    )

bot.run(TOKEN)