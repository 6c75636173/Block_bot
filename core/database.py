import json
import os
from datetime import datetime


DATA_DIR = "data"
COOLDOWNS_FILE = f"{DATA_DIR}/cooldowns.json"


def load_data(file_path, default=None):
    if default is None:
        default = {}
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default


def save_data(file_path, data):
    os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

#item generate by AI
SPECIAL_ITEMS = {
    "🎭 Masque Mystérieux":   {"description": "Un masque rare et élégant",           "value": 150},
    "👑 Couronne Dorée":      {"description": "Une couronne digne d'un roi",         "value": 500},
    "💎 Diamant Éternel":     {"description": "Un diamant d'une pureté incroyable",  "value": 1000},
    "🏆 Trophée du Champion": {"description": "Le trophée ultime",                   "value": 750},
    "🎨 Tableau Ancien":      {"description": "Une œuvre d'art précieuse",           "value": 300},
    "🔮 Orbe de Cristal":     {"description": "Un orbe mystique",                    "value": 400},
    "⚔️ Épée Légendaire":     {"description": "Une arme légendaire",                 "value": 600},
    "🎪 Ticket VIP":          {"description": "Accès VIP illimité",                  "value": 200},
    "🌟 Étoile Filante":      {"description": "Une étoile capturée",                 "value": 350},
    "🎁 Boîte Cadeau Géante": {"description": "Une énorme boîte cadeau",             "value": 250},
    "🌈 Épée Diamantée":      {"description": "Une épée forgée avec un diamant",     "value": 2000},
    "🔥 Orbe Enflammé":       {"description": "Un orbe d'une puissance incroyable",  "value": 1200},
    "👑 Masque Royal":        {"description": "Un masque de royauté absolue",        "value": 800},
}

_cooldowns = load_data(COOLDOWNS_FILE)


def _save_cooldowns():
    save_data(COOLDOWNS_FILE, _cooldowns)


def set_cooldown(user_id, key, end_time: datetime):
    uid = str(user_id)
    _cooldowns.setdefault(uid, {})[key] = end_time.isoformat()
    _save_cooldowns()


def check_cooldown(user_id, key):
    uid = str(user_id)
    ts = _cooldowns.get(uid, {}).get(key)
    if ts is None:
        return True, 0.0

    end_time = datetime.fromisoformat(ts)
    remaining = (end_time - datetime.now()).total_seconds()
    if remaining <= 0:
        return True, 0.0
    return False, remaining
