"""
core/config.py — Constantes de configuration : chemins des fichiers de données,
rangs de niveau, catalogue des défis quotidiens.
"""

import os

DATA_DIR = "bot_data"
os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE = f"{DATA_DIR}/users.json"
SHOP_FILE = f"{DATA_DIR}/shop.json"
WARNINGS_FILE = f"{DATA_DIR}/warnings.json"
DAILY_FILE = f"{DATA_DIR}/daily.json"
CHALLENGES_FILE = f"{DATA_DIR}/challenges.json"
VERIFICATION_FILE = f"{DATA_DIR}/verification.json"

RANKS = [
    {"niveau": 1, "xp_requis": 0, "nom": "Débutant"},
    {"niveau": 5, "xp_requis": 500, "nom": "Membre Actif"},
    {"niveau": 10, "xp_requis": 1500, "nom": "Vétéran"},
    {"niveau": 15, "xp_requis": 3000, "nom": "Expert"},
    {"niveau": 20, "xp_requis": 5000, "nom": "Légende"},
    {"niveau": 30, "xp_requis": 10000, "nom": "Maître"},
]

DAILY_CHALLENGES = [
    {"id": "messages_50", "nom": "Bavard", "description": "Envoie 50 messages", "objectif": 50, "recompense": 500, "type": "messages"},
    {"id": "coinflip_win_3", "nom": "Chanceux", "description": "Gagne 3 coinflips", "objectif": 3, "recompense": 300, "type": "coinflip_wins"},
    {"id": "casino_5", "nom": "Joueur", "description": "Joue 5 fois au casino", "objectif": 5, "recompense": 400, "type": "casino_plays"},
    {"id": "spend_500", "nom": "Dépensier", "description": "Dépense 500 pièces", "objectif": 500, "recompense": 600, "type": "spent"},
    {"id": "work_10", "nom": "Travailleur", "description": "Travaille 10 fois", "objectif": 10, "recompense": 200, "type": "work_count"},
    {"id": "level_up", "nom": "Progresser", "description": "Monte d'un niveau", "objectif": 1, "recompense": 1000, "type": "level_ups"},
]
