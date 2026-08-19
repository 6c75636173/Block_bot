import discord
import os
import sys

from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN environment variable not set. "
        "Please set it in your .env file."
    )

intents = discord.Intents.default()

intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

@bot.event
async def setup_hook():

    try:
        await bot.load_extension("cogs.ping")

        print(
            "\033[92m[OK]\033[0m "
            "Cog Ping chargé."
        )

    except Exception as error:
        print(
            f"\033[91m[ERROR]\033[0m "
            f"Impossible de charger le Cog Ping : {error}"
        )
        raise

    try:
        synced_commands = await bot.tree.sync()

        print(
            f"\033[92m[OK]\033[0m "
            f"{len(synced_commands)} commande(s) slash "
            f"synchronisée(s) globalement."
        )

    except Exception as error:
        print(
            f"\033[91m[ERROR]\033[0m "
            f"Impossible de synchroniser les commandes : {error}"
        )
        raise

@bot.event
async def on_ready():

    print(
        f"\033[92m[ONLINE]\033[0m "
        f"{bot.user} est connecté !"
    )

    print(
        f"\033[96m[INFO]\033[0m "
        f"ID du bot : {bot.user.id}"
    )

bot.run(TOKEN)