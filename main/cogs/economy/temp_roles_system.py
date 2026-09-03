"""
temp_roles_system.py — Rôles temporaires achetables dans /shop (items de type "role_temp").

Achat -> le bot crée le rôle Discord s'il n'existe pas encore, l'attribue à l'acheteur,
et programme son retrait après la durée définie par l'admin à la création de l'item
(voir /admin_shop_add_role dans block_bot.py).

Si l'acheteur rachète le même rôle avant expiration, la durée s'ADDITIONNE à celle
restante (prolongation, pas de reset) — comportement choisi explicitement.

Quand un rôle temporaire n'a plus aucun titulaire actif, il est supprimé du serveur.
"""

import discord
import json
import os
import asyncio
from datetime import datetime, timedelta

TEMP_ROLES_FILE = "bot_data/temp_roles.json"


def load_data(filepath, default=None):
    if default is None:
        default = {}
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default


def save_data_to(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# Format : {guild_id: {role_name: {user_id: "2026-08-15T12:00:00.000000"}}}
temp_roles_data = load_data(TEMP_ROLES_FILE)


def save_temp_roles():
    save_data_to(TEMP_ROLES_FILE, temp_roles_data)


def get_expiry(guild_id, role_name, user_id):
    """Retourne le datetime d'expiration actuel pour ce membre sur ce rôle, ou None."""
    ts = temp_roles_data.get(str(guild_id), {}).get(role_name, {}).get(str(user_id))
    return datetime.fromisoformat(ts) if ts else None


async def grant_temp_role(guild: discord.Guild, member: discord.Member, role_name: str, duree_heures: float):
    """
    Crée le rôle Discord `role_name` s'il n'existe pas, l'attribue à `member`,
    et programme/prolonge son expiration. Retourne le nouveau datetime d'expiration.
    """
    guild_id = str(guild.id)
    uid = str(member.id)

    role = discord.utils.get(guild.roles, name=role_name)
    if role is None:
        role = await guild.create_role(
            name=role_name,
            reason="Rôle temporaire créé automatiquement (achat en boutique)"
        )

    if role not in member.roles:
        await member.add_roles(role, reason="Achat en boutique — rôle temporaire")

    temp_roles_data.setdefault(guild_id, {}).setdefault(role_name, {})

    now = datetime.now()
    current_expiry = get_expiry(guild_id, role_name, uid)
    # Prolongation : si un temps restant existe déjà, on part de là plutôt que de "maintenant"
    base = max(current_expiry, now) if current_expiry else now

    new_expiry = base + timedelta(hours=duree_heures)
    temp_roles_data[guild_id][role_name][uid] = new_expiry.isoformat()
    save_temp_roles()

    return new_expiry


async def setup_temp_roles_system(bot):
    async def expiration_check_task():
        await bot.wait_until_ready()
        while not bot.is_closed():
            try:
                now = datetime.now()
                changed = False

                for guild_id in list(temp_roles_data.keys()):
                    guild = bot.get_guild(int(guild_id))
                    if not guild:
                        continue

                    for role_name in list(temp_roles_data[guild_id].keys()):
                        holders = temp_roles_data[guild_id][role_name]
                        expired_uids = [
                            uid for uid, exp in holders.items()
                            if datetime.fromisoformat(exp) <= now
                        ]

                        role = discord.utils.get(guild.roles, name=role_name)

                        for uid in expired_uids:
                            member = guild.get_member(int(uid))
                            if member and role and role in member.roles:
                                try:
                                    await member.remove_roles(role, reason="Rôle temporaire expiré")
                                except discord.HTTPException:
                                    pass
                            del holders[uid]
                            changed = True

                        # Plus aucun titulaire actif -> on supprime le rôle du serveur
                        if not holders and role is not None:
                            try:
                                await role.delete(reason="Rôle temporaire — plus aucun titulaire")
                            except discord.HTTPException:
                                pass
                            del temp_roles_data[guild_id][role_name]
                            changed = True

                    if not temp_roles_data[guild_id]:
                        del temp_roles_data[guild_id]
                        changed = True

                if changed:
                    save_temp_roles()
            except Exception as e:
                print(f"Erreur temp_roles_system auto-release: {e}")

            await asyncio.sleep(300)  # vérification toutes les 5 minutes

    bot.loop.create_task(expiration_check_task())
