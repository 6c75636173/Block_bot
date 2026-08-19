import discord
import os
import sys

from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

load_dotenv()

@bot.event
async def setup_hook():

    try:
        # Chargement du module Ping
        await bot.load_extension("cogs.ping")

        print("\033[92m[OK]\033[0m Cog Ping chargé.")

    except Exception as error:
        print(
            f"\033[91m[ERROR]\033[0m "
            f"Impossible de charger le Cog Ping : {error}"
        )
        raise

    try:
        # Synchronisation globale des commandes slash
        synced_commands = await bot.tree.sync()

        print(
            f"\033[92m[OK]\033[0m "
            f"{len(synced_commands)} commande(s) slash synchronisée(s)."
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


TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError(
        os.error("TOKEN environment variable not set. Please set it in your .env file or system environment variables.")
    )
bot.run(TOKEN) 