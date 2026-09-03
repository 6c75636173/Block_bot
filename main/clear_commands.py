"""
clear_commands.py — À LANCER UNE SEULE FOIS pour nettoyer les anciennes commandes Discord.

Contexte : après un renommage de commandes, Discord garde en mémoire les anciennes tant
qu'elles n'ont pas été explicitement effacées — un simple bot.tree.sync() (déjà présent
dans block_bot.py) ne remplace que la liste GLOBALE, pas les commandes enregistrées
spécifiquement sur un serveur (si un /sync par serveur a déjà été fait un jour).

Usage :
1. Place ce fichier à côté de block_bot.py (dans main/)
2. Lance-le une fois : python clear_commands.py
3. Attends le message "Nettoyage terminé"
4. Relance ton bot normalement (block_bot.py) — il resynchronisera les commandes actuelles
5. Supprime ce fichier, il ne sert qu'une fois
"""

import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")

    # 1. Vider et resynchroniser les commandes GLOBALES
    bot.tree.clear_commands(guild=None)
    await bot.tree.sync()
    print("✅ Commandes globales vidées.")

    # 2. Vider et resynchroniser les commandes propres à CHAQUE serveur où le bot est présent
    #    (au cas où un /sync par serveur aurait été fait un jour, laissant des doublons)
    for guild in bot.guilds:
        bot.tree.clear_commands(guild=guild)
        await bot.tree.sync(guild=guild)
        print(f"✅ Commandes vidées pour le serveur : {guild.name}")

    print("\n🎉 Nettoyage terminé ! Relance maintenant ton bot normal (block_bot.py).")
    print("   Les commandes globales peuvent prendre jusqu'à 1h pour réapparaître partout,")
    print("   mais généralement c'est immédiat ou en quelques minutes.")

    await bot.close()


if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        raise RuntimeError("❌ DISCORD_TOKEN introuvable dans .env")
    bot.run(TOKEN)
