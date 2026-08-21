import discord
import json
import os
import random

from discord import app_commands
from datetime import datetime, timedelta
from core.database import SPECIAL_ITEMS, CRAFTED_ITEMS, DROPPABLE_ITEMS, set_cooldown, check_cooldown

ITEMS_FILE = "data/items.json"
MARKET_FILE = "data/market.json"
BUFFS_FILE = "data/buffs.json"

# buff genareted by AI
ITEMS_BUFFS = { 
    "🔮 Orbe de Cristal":     {"type": "casino_multiplier", "value": 1.20, "duration": 60,  "label": "+20% gains casino"},
    "🌟 Étoile Filante":      {"type": "slots_luck",        "value": 1.15, "duration": 60,  "label": "+15% gains slots"},
    "⚔️ Épée Légendaire":     {"type": "crime_multiplier",  "value": 2.0,  "duration": 60,  "label": "x2 gains crime"},
    "👑 Couronne Dorée":      {"type": "cooldown_reducer",  "value": 0.5,  "duration": 120, "label": "Cooldowns -50%"},
    "🎪 Ticket VIP":          {"type": "work_multiplier",   "value": 1.50, "duration": 60,  "label": "+50% gains work"},
    "🏆 Trophée du Champion": {"type": "all_multiplier",    "value": 1.10, "duration": 30,  "label": "+10% tous les gains"},
    "🎭 Masque Mystérieux":   {"type": "crime_multiplier",  "value": 1.30, "duration": 60,  "label": "+30% gains crime"},
    "💎 Diamant Éternel":     {"type": "casino_multiplier", "value": 1.50, "duration": 30,  "label": "+50% gains casino"},
    "🌈 Épée Diamantée":      {"type": "all_multiplier",    "value": 1.25, "duration": 120, "label": "+25% tous les gains"},
    "🔥 Orbe Enflammé":       {"type": "casino_multiplier", "value": 2.0,  "duration": 60,  "label": "x2 gains casino"},
    "👑 Masque Royal":        {"type": "all_multiplier",    "value": 1.35, "duration": 90,  "label": "+35% tous les gains"},
}

CRAFT_RECIPES = {
    "🌈 Épée Diamantée": {
        "ingredients": ["💎 Diamant Éternel", "⚔️ Épée Légendaire"],
        "description": "Forge une épée avec un diamant → +25% tous les gains 2h"
    },
    "🔥 Orbe Enflammé": {
        "ingredients": ["🔮 Orbe de Cristal", "🌟 Étoile Filante"],
        "description": "Combine deux objets mystiques → x2 gains casino 1h"
    },
    "👑 Masque Royal": {
        "ingredients": ["🎭 Masque Mystérieux", "👑 Couronne Dorée"],
        "description": "Fusionne masque et couronne → +35% tous les gains 1h30"
    },
}

def load_data(filepath, defaut=None):
    if defaut is None:
        defaut = {}
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return defaut

def save_data_to(filepath, data):
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        