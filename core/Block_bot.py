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

    # Chargement des Cogs
    await bot.load_extension("cogs.ping")
    await bot.load_extension("cogs.items_system")
    await bot.load_extension("cogs.economy")
    await bot.load_extension("cogs.quotidient")

    print("\033[92m[OK]\033[0m Cogs chargés.")

    legacy_commands = {"fabriquer", "objet_fusionner", "marche"}
    application_id = bot.application_id or bot.user.id

    global_commands = await bot.tree.fetch_commands()
    for command in global_commands:
        if command.name in legacy_commands:
            await bot.http.delete_global_command(application_id, command.id)


    TEST_GUILD_ID = 1466475336073216216

    guild = discord.Object(id=TEST_GUILD_ID)

    guild_commands = await bot.tree.fetch_commands(guild=guild)
    for command in guild_commands:
        if command.name in legacy_commands:
            await bot.http.delete_guild_command(application_id, guild.id, command.id)

    bot.tree.clear_commands(guild=guild)

    await bot.tree.sync(guild=guild)

    print(
        "\033[93m[CLEAN]\033[0m "
        "Last command successfully removed from the server."
    )


    synced = await bot.tree.sync()

    print(
        f"\033[92m[OK]\033[0m "
        f"{len(synced)} commande(s) slash synchronised globaly."
    )


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