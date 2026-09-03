"""
utils/embeds.py — Réservé aux helpers de construction d'embeds génériques.

Pour l'instant, chaque commande construit ses embeds directement inline (couleurs,
champs propres à chaque contexte) — il n'y avait pas de logique de construction d'embed
dupliquée à extraire sans réécrire chaque commande. Ce fichier existe pour que l'endroit
soit prêt le jour où un vrai pattern commun émerge (ex: un embed d'erreur standardisé).

Exemple de ce qui pourrait y aller plus tard :

    def error_embed(message: str) -> discord.Embed:
        return discord.Embed(description=f"❌ {message}", color=discord.Color.red())

    def success_embed(title: str, description: str = None) -> discord.Embed:
        return discord.Embed(title=title, description=description, color=discord.Color.green())
"""

import discord
