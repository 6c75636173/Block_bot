"""
core/database.py — Chargement des données persistantes au démarrage (fichiers JSON dans
bot_data/), et migration automatique de l'ancien format ("coins" -> "pieces").
"""

from utils import load_data, save_data
from .config import USERS_FILE, SHOP_FILE, WARNINGS_FILE, DAILY_FILE, CHALLENGES_FILE, VERIFICATION_FILE

users_data = load_data(USERS_FILE)


def _migrate_coins_to_pieces(data):
    migrated = 0
    for uid, ud in data.items():
        if "coins" in ud:
            ud["pieces"] = ud.pop("coins")
            migrated += 1
    if migrated:
        print(f"🔄 Migration : {migrated} profil(s) converti(s) de 'coins' vers 'pieces'.")
        save_data(USERS_FILE, data)


_migrate_coins_to_pieces(users_data)

shop_items = load_data(SHOP_FILE, {
    "Rôle VIP": {"prix": 1000, "description": "Accède au salon VIP", "type": "role"},
    "Changement de pseudo": {"prix": 500, "description": "Change ton pseudo une fois", "type": "service"},
    "Badge Légende": {"prix": 2000, "description": "Un badge exclusif", "type": "badge"}
})
save_data(SHOP_FILE, shop_items)

warnings_data = load_data(WARNINGS_FILE)
daily_data = load_data(DAILY_FILE)
challenges_data = load_data(CHALLENGES_FILE)
verification_config = load_data(VERIFICATION_FILE)  # {guild_id: {"channel_id", "verified_role_id", "unverified_role_id", "log_channel_id"}}
