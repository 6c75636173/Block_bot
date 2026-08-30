import discord
from discord.ext import commands
import os
import sys
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COGS_DIR = os.path.join(BASE_DIR, "cogs")
for entry in sorted(os.listdir(COGS_DIR)):
    full_path = os.path.join(COGS_DIR, entry)
    if os.path.isdir(full_path):
        sys.path.insert(0, full_path)

import core

# Cogs — un dossier par domaine sous cogs/, chacun avec sa fonction setup_xxx(bot, ...)
import verification_system
import economy_extensions
import logs_system
import addictive_systems
import slots_and_time
import items_system
import birthday_system
import business_system
import horse_race
import poker_system
import jail_system
import temp_roles_system

import profil
import boutique
import moderation
import casino
import fun
import paris
import quotidien
import economie
import admin
import events


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
core.init_bot(bot)


async def setup_hook():
    """Appelé automatiquement par discord.py au démarrage : branche toutes les commandes."""
    await profil.setup_profil(bot)
    await boutique.setup_boutique(bot)
    await moderation.setup_moderation(bot)
    await casino.setup_casino(bot)
    fun_group = await fun.setup_fun(bot)
    await paris.setup_paris(bot)
    await quotidien.setup_quotidien(bot)
    await economie.setup_economie(bot)
    await admin.setup_admin(bot)

    await economy_extensions.setup_marriage_commands(bot, core.users_data, lambda: core.save_data(core.USERS_FILE, core.users_data))
    await economy_extensions.setup_gang_commands(bot, core.users_data, lambda: core.save_data(core.USERS_FILE, core.users_data))
    await economy_extensions.setup_achievement_commands(bot, core.users_data)
    await economy_extensions.setup_economy_commands(bot, core.users_data, lambda: core.save_data(core.USERS_FILE, core.users_data))
    await economy_extensions.setup_misc_commands(bot, core.users_data, lambda: core.save_data(core.USERS_FILE, core.users_data), fun_group)

    await logs_system.setup_logs_events(bot)
    await logs_system.setup_logs_commands(bot)

    await addictive_systems.setup_addictive_systems(bot, core.users_data, lambda: core.save_data(core.USERS_FILE, core.users_data))
    await slots_and_time.setup_slots_and_time(bot, core.users_data, lambda: core.save_data(core.USERS_FILE, core.users_data))
    await items_system.setup_items_system(bot, core.users_data, lambda: core.save_data(core.USERS_FILE, core.users_data))
    await birthday_system.setup_birthday_system(bot, core.users_data, lambda: core.save_data(core.USERS_FILE, core.users_data))
    verification_system.setup_verification_commands(bot, core.verification_config, lambda: core.save_data(core.VERIFICATION_FILE, core.verification_config))
    await business_system.setup_business_system(bot, core.users_data, lambda: core.save_data(core.USERS_FILE, core.users_data))
    await horse_race.setup_horse_race(bot, core.users_data, lambda: core.save_data(core.USERS_FILE, core.users_data))
    await poker_system.setup_poker(bot, core.users_data, lambda: core.save_data(core.USERS_FILE, core.users_data))
    await jail_system.setup_jail_system(bot)
    await temp_roles_system.setup_temp_roles_system(bot)

    events.setup_events(bot)


bot.setup_hook = setup_hook

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        raise RuntimeError(
            "❌ DISCORD_TOKEN introuvable. Crée un fichier .env à côté de block_bot.py "
            "avec la ligne : DISCORD_TOKEN=ton_token_ici (voir .env.example)."
        )
    bot.run(TOKEN)
