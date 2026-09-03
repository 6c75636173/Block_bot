"""
core/bot.py — Référence partagée vers l'instance du bot (remplie par block_bot.py au
démarrage), et fonctions utilitaires qui en dépendent : profil utilisateur, XP, défis
quotidiens.
"""

import discord
import random
from datetime import datetime

from utils import save_data
from .config import USERS_FILE, CHALLENGES_FILE, RANKS, DAILY_CHALLENGES
from .database import users_data, challenges_data

bot = None


def init_bot(bot_instance):
    global bot
    bot = bot_instance


# ========== PROFIL UTILISATEUR ==========

def get_user_data(user_id):
    user_id = str(user_id)
    if user_id not in users_data:
        users_data[user_id] = {"xp": 0, "niveau": 1, "pieces": 100, "messages": 0, "inventaire": []}
        save_data(USERS_FILE, users_data)
    return users_data[user_id]


def get_rank_name(niveau):
    rank_name = "Débutant"
    for rank in RANKS:
        if niveau >= rank["niveau"]:
            rank_name = rank["nom"]
    return rank_name


async def get_display_user(interaction: discord.Interaction, user_id_int: int):
    """Cache (membre du serveur, puis cache global) avant fetch_user (appel API)."""
    if interaction.guild:
        member = interaction.guild.get_member(user_id_int)
        if member:
            return member
    cached = bot.get_user(user_id_int)
    if cached:
        return cached
    return await bot.fetch_user(user_id_int)


def add_xp(user_id, xp_amount=15):
    user_data = get_user_data(user_id)
    user_data["xp"] += xp_amount
    user_data["messages"] += 1

    next_level_xp = user_data["niveau"] * 100
    if user_data["xp"] >= next_level_xp:
        user_data["niveau"] += 1
        user_data["pieces"] += 50
        save_data(USERS_FILE, users_data)
        return True, user_data["niveau"]

    save_data(USERS_FILE, users_data)
    return False, user_data["niveau"]


# ========== DÉFIS QUOTIDIENS ==========

def assign_daily_challenge(user_id):
    user_id = str(user_id)
    if user_id not in challenges_data:
        challenges_data[user_id] = {"current": {}, "completed": [], "last_reset": None}

    today = datetime.now().date().isoformat()
    last_reset = challenges_data[user_id].get("last_reset")

    if last_reset != today:
        challenge = random.choice(DAILY_CHALLENGES)
        challenges_data[user_id]["current"] = {"challenge": challenge, "progress": 0, "assigned_date": today}
        challenges_data[user_id]["last_reset"] = today
        save_data(CHALLENGES_FILE, challenges_data)
        return True
    return False


def update_challenge_progress(user_id, challenge_type, amount=1):
    user_id = str(user_id)
    if user_id not in challenges_data or not challenges_data[user_id].get("current"):
        assign_daily_challenge(user_id)
        return None

    current = challenges_data[user_id]["current"]
    challenge = current["challenge"]

    if challenge["type"] == challenge_type:
        current["progress"] += amount
        save_data(CHALLENGES_FILE, challenges_data)
        if current["progress"] >= challenge["objectif"]:
            return challenge
    return None


async def complete_challenge(user_id, challenge, channel):
    user_id_int = int(user_id)
    user_data = get_user_data(user_id_int)
    user = await bot.fetch_user(user_id_int)

    user_data["pieces"] += challenge["recompense"]
    challenges_data[user_id]["completed"].append({"id": challenge["id"], "date": datetime.now().isoformat()})
    challenges_data[user_id]["current"] = {}

    save_data(USERS_FILE, users_data)
    save_data(CHALLENGES_FILE, challenges_data)

    embed = discord.Embed(
        title="🎉 DÉFI COMPLÉTÉ !",
        description=f"{user.mention} a terminé le défi **{challenge['nom']}** !",
        color=discord.Color.gold()
    )
    embed.add_field(name="Récompense", value=f"💰 +{challenge['recompense']} pièces")
    embed.add_field(name="Nouveau solde", value=f"💰 {user_data['pieces']} pièces")

    await channel.send(embed=embed)
    assign_daily_challenge(user_id)
