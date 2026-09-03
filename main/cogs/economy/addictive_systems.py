import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
from datetime import datetime, timedelta

from utils import SPECIAL_ITEMS, DROPPABLE_ITEMS  # source unique — voir utils.py

# Fichiers de données
SCRATCH_FILE = "bot_data/scratch_data.json"
BOXES_FILE = "bot_data/boxes_data.json"
MISSIONS_FILE = "bot_data/missions_data.json"
ITEMS_FILE = "bot_data/items_inventory.json"

# ========== DONNÉES ==========

def load_data(filepath, default=None):
    if default is None:
        default = {}
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_data(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ========== TICKETS À GRATTER ==========

TICKET_TYPES = {
    "triple_match": {
        "name": "💎 Triple Match",
        "price": 10,
        "description": "Grille 3x3 : trouve 3 symboles identiques pour gagner jusqu'à 200 pièces.",
        "emoji": "💎",
        "symbols": ["💎", "🍒", "🔔", "🍋", "⭐", "💰"],
        "grid": (3, 3),  # 3x3
        "win_condition": "3_match",
        "prizes": {
            "💎": 100,
            "🍒": 50,
            "🔔": 75,
            "🍋": 25,
            "⭐": 150,
            "💰": 200
        }
    },
    "lucky_7": {
        "name": "🍀 Lucky 7",
        "price": 25,
        "description": "Grille 2x3 : trouve des 7 pour gagner jusqu'à 500 pièces.",
        "emoji": "🍀",
        "symbols": ["7️⃣", "🍀", "💚", "🎰", "🎲", "🃏"],
        "grid": (2, 3),  # 2x3
        "win_condition": "find_7",
        "prizes": {
            "1x7️⃣": 50,
            "2x7️⃣": 150,
            "3x7️⃣": 500
        }
    },
    "jackpot": {
        "name": "💰 Jackpot",
        "price": 50,
        "description": "Grille 3x3 : aligne 3 montants identiques pour remporter ce montant.",
        "emoji": "💰",
        "symbols": ["10", "25", "50", "100", "250", "500"],
        "grid": (3, 3),
        "win_condition": "3_amounts",
        "prizes": {}  # Dynamic based on symbols
    },
    "royal": {
        "name": "👑 Royal Scratch",
        "price": 100,
        "description": "Grille 3x3 : aligne des symboles royaux pour gagner jusqu'à 2 000 pièces.",
        "emoji": "👑",
        "symbols": ["👑", "💎", "💍", "🏆", "⭐", "🌟"],
        "grid": (3, 3),
        "win_condition": "royal",
        "prizes": {
            "👑": 1000,
            "💎": 500,
            "💍": 750,
            "🏆": 600,
            "⭐": 400,
            "🌟": 300
        }
    },
    "mystery": {
        "name": "🎁 Mystery Box",
        "price": 5,
        "description": "Ticket 1x1 : 1 chance sur 3 de gagner entre 10 et 100 pièces.",
        "emoji": "🎁",
        "symbols": ["❓"],
        "grid": (1, 1),
        "win_condition": "mystery",
        "prizes": {}  # Random
    }
}

def generate_ticket(ticket_type):
    """Génère un ticket aléatoire"""
    config = TICKET_TYPES[ticket_type]
    rows, cols = config["grid"]
    symbols = config["symbols"]
    
    grid = []
    for _ in range(rows):
        row = [random.choice(symbols) for _ in range(cols)]
        grid.append(row)
    
    return {
        "type": ticket_type,
        "grid": grid,
        "scratched": [[False] * cols for _ in range(rows)],
        "revealed": False
    }

def check_win(ticket):
    """Vérifie si le ticket est gagnant"""
    ticket_type = ticket["type"]
    config = TICKET_TYPES[ticket_type]
    grid = ticket["grid"]
    
    if config["win_condition"] == "3_match":
        flat = [cell for row in grid for cell in row]
        for symbol in config["symbols"]:
            if flat.count(symbol) >= 3:
                return True, config["prizes"][symbol], symbol
        return False, 0, None
    
    elif config["win_condition"] == "find_7":
        flat = [cell for row in grid for cell in row]
        count_7 = flat.count("7️⃣")
        if count_7 >= 3:
            return True, 500, "3x7️⃣"
        elif count_7 == 2:
            return True, 150, "2x7️⃣"
        elif count_7 == 1:
            return True, 50, "1x7️⃣"
        return False, 0, None
    
    elif config["win_condition"] == "3_amounts":
        flat = [cell for row in grid for cell in row]
        for amount in config["symbols"]:
            if flat.count(amount) >= 3:
                return True, int(amount), amount
        return False, 0, None
    
    elif config["win_condition"] == "royal":
        flat = [cell for row in grid for cell in row]
        for symbol in config["symbols"]:
            if flat.count(symbol) >= 3:
                return True, config["prizes"][symbol], symbol
        
        for row in grid:
            if len(set(row)) == 1:
                symbol = row[0]
                return True, config["prizes"][symbol] * 2, symbol
        
        return False, 0, None
    
    elif config["win_condition"] == "mystery":
        win = random.choice([True, False, False])  # 33% chance
        if win:
            prize = random.randint(10, 100)
            return True, prize, "🎁"
        return False, 0, None
    
    return False, 0, None

def check_near_miss(ticket):
    """Vérifie si c'est un near-miss (presque gagné)"""
    ticket_type = ticket["type"]
    config = TICKET_TYPES[ticket_type]
    grid = ticket["grid"]
    
    if config["win_condition"] == "3_match":
        flat = [cell for row in grid for cell in row]
        for symbol in config["symbols"]:
            if flat.count(symbol) == 2:
                return True, symbol
    
    elif config["win_condition"] == "find_7":
        flat = [cell for row in grid for cell in row]
        if flat.count("7️⃣") == 2:
            return True, "7️⃣"
    
    elif config["win_condition"] == "3_amounts":
        flat = [cell for row in grid for cell in row]
        for amount in config["symbols"]:
            if flat.count(amount) == 2:
                return True, amount
    
    return False, None

class ScratchView(discord.ui.View):
    def __init__(self, ticket, user_id, users_data, save_callback):
        super().__init__(timeout=180)
        self.ticket = ticket
        self.user_id = str(user_id)
        self.users_data = users_data
        self.save_callback = save_callback
        self.update_buttons()
    
    def update_buttons(self):
        self.clear_items()
        
        reveal_all = discord.ui.Button(
            label="🎯 Tout gratter",
            style=discord.ButtonStyle.danger,
            custom_id="reveal_all"
        )
        reveal_all.callback = self.reveal_all_callback
        self.add_item(reveal_all)
        
        rows, cols = TICKET_TYPES[self.ticket["type"]]["grid"]
        for r in range(rows):
            for c in range(cols):
                if not self.ticket["scratched"][r][c]:
                    button = discord.ui.Button(
                        label=f"Case {r*cols + c + 1}",
                        style=discord.ButtonStyle.secondary,
                        custom_id=f"scratch_{r}_{c}"
                    )
                    button.callback = self.scratch_callback
                    self.add_item(button)
    
    async def scratch_callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Ce n'est pas ton ticket !", ephemeral=True)
            return
        
        custom_id = interaction.data["custom_id"]
        _, r, c = custom_id.split("_")
        r, c = int(r), int(c)
        
        self.ticket["scratched"][r][c] = True
        
        all_scratched = all(all(row) for row in self.ticket["scratched"])
        
        embed = self.create_ticket_embed()
        
        if all_scratched and not self.ticket["revealed"]:
            self.ticket["revealed"] = True
            await self.process_result(interaction)
            return
        
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def reveal_all_callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Ce n'est pas ton ticket !", ephemeral=True)
            return
        
        rows, cols = TICKET_TYPES[self.ticket["type"]]["grid"]
        for r in range(rows):
            for c in range(cols):
                self.ticket["scratched"][r][c] = True
        
        self.ticket["revealed"] = True
        await self.process_result(interaction)
    
    async def process_result(self, interaction):
        """Traiter le résultat final"""
        won, prize, symbol = check_win(self.ticket)
        near_miss, nm_symbol = check_near_miss(self.ticket)
        
        embed = self.create_ticket_embed(show_result=True)
        
        if won:
            self.users_data[self.user_id]["pieces"] += prize
            self.save_callback()
            
            embed.color = discord.Color.gold()
            embed.add_field(
                name="🎉 GAGNANT !",
                value=f"Tu gagnes **{prize} pièces** !",
                inline=False
            )
            
            if symbol:
                embed.add_field(name="🎯 Symbole gagnant", value=symbol, inline=True)
        
        elif near_miss:
            embed.color = discord.Color.orange()
            embed.add_field(
                name="😮 Presque !",
                value=f"Il te manquait juste 1 **{nm_symbol}** pour gagner ! Retente ta chance !",
                inline=False
            )
        
        else:
            embed.color = discord.Color.red()
            embed.add_field(
                name="❌ Perdu",
                value="Pas de chance cette fois... Réessaye !",
                inline=False
            )
        
        embed.add_field(
            name="💰 Solde",
            value=f"{self.users_data[self.user_id]['pieces']} pièces",
            inline=True
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    def create_ticket_embed(self, show_result=False):
        config = TICKET_TYPES[self.ticket["type"]]
        
        embed = discord.Embed(
            title=f"🎫 {config['name']} 🎫",
            color=discord.Color.blue()
        )
        
        grid_display = ""
        for r, row in enumerate(self.ticket["grid"]):
            for c, cell in enumerate(row):
                if self.ticket["scratched"][r][c] or show_result:
                    grid_display += f"{cell} "
                else:
                    grid_display += "🟫 "
            grid_display += "\n"
        
        embed.description = f"```\n{grid_display}```"
        
        if not show_result:
            embed.add_field(
                name="💡 Comment jouer",
                value="Gratte les cases une par une ou tout révéler !",
                inline=False
            )
        
        return embed

# ========== LOOT BOXES ==========

BOX_TYPES = {
    "bronze": {
        "name": "📦 Caisse Bronze",
        "price": 20,
        "emoji": "📦",
        "contents": {
            "pieces": (10, 50),
            "ticket_chance": 0.3,  # 30% chance ticket gratuit
            "item_chance": 0.1,    # 10% chance item
            "jackpot_contrib": 2   # Contribue 2 pièces au jackpot
        }
    },
    "silver": {
        "name": "🎁 Caisse Argent",
        "price": 50,
        "emoji": "🎁",
        "contents": {
            "pieces": (30, 150),
            "ticket_chance": 0.5,
            "item_chance": 0.2,
            "jackpot_contrib": 5
        }
    },
    "gold": {
        "name": "💎 Caisse Or",
        "price": 100,
        "emoji": "💎",
        "contents": {
            "pieces": (80, 300),
            "ticket_chance": 0.7,
            "item_chance": 0.4,
            "jackpot_contrib": 10
        }
    },
    "legendary": {
        "name": "👑 Caisse Légendaire",
        "price": 250,
        "emoji": "👑",
        "contents": {
            "pieces": (200, 1000),
            "ticket_chance": 0.9,
            "item_chance": 0.6,
            "jackpot_contrib": 25
        }
    }
}

def open_box(box_type, user_id, boxes_data):
    """Ouvre une caisse et retourne le contenu"""
    config = BOX_TYPES[box_type]
    rewards = []
    
    pièces = random.randint(*config["contents"]["pieces"])
    rewards.append(("pièces", pièces))
    
    if random.random() < config["contents"]["ticket_chance"]:
        ticket_type = random.choice(list(TICKET_TYPES.keys()))
        rewards.append(("ticket", ticket_type))
    
    if random.random() < config["contents"]["item_chance"]:
        item = random.choice(DROPPABLE_ITEMS)
        rewards.append(("item", item))
    
    if random.random() < 0.01:
        jackpot = boxes_data.get("jackpot", 0)
        rewards.append(("jackpot", jackpot))
        boxes_data["jackpot"] = 0  # Reset
    else:
        boxes_data["jackpot"] = boxes_data.get("jackpot", 0) + config["contents"]["jackpot_contrib"]
    
    # Pity system
    user_id_str = str(user_id)
    if user_id_str not in boxes_data:
        boxes_data[user_id_str] = {"pity": 0, "boxes_opened": 0}
    
    boxes_data[user_id_str]["pity"] += 1
    boxes_data[user_id_str]["boxes_opened"] += 1
    
    if boxes_data[user_id_str]["pity"] >= 10:
        if not any(r[0] == "item" for r in rewards):
            item = random.choice(DROPPABLE_ITEMS)
            rewards.append(("item", item))
        boxes_data[user_id_str]["pity"] = 0
    
    if any(r[0] == "item" for r in rewards):
        boxes_data[user_id_str]["pity"] = 0
    
    return rewards

class BoxOpenView(discord.ui.View):
    def __init__(self, box_type, rewards, user_id):
        super().__init__(timeout=60)
        self.box_type = box_type
        self.rewards = rewards
        self.user_id = str(user_id)
        self.revealed = False
    
    @discord.ui.button(label="🎁 Ouvrir la caisse", style=discord.ButtonStyle.success)
    async def open_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Ce n'est pas ta caisse !", ephemeral=True)
            return
        
        if self.revealed:
            await interaction.response.send_message("❌ Caisse déjà ouverte !", ephemeral=True)
            return
        
        self.revealed = True
        
        config = BOX_TYPES[self.box_type]
        
        embed = discord.Embed(
            title=f"🎉 {config['name']} - Ouverte !",
            description="**Récompenses obtenues :**",
            color=discord.Color.gold()
        )
        
        for reward_type, value in self.rewards:
            if reward_type == "pieces":
                embed.add_field(name="💰 Coins", value=f"+{value} pièces", inline=False)
            elif reward_type == "ticket":
                ticket_name = TICKET_TYPES[value]["name"]
                embed.add_field(name="🎫 Ticket Gratuit", value=ticket_name, inline=False)
            elif reward_type == "item":
                item_info = SPECIAL_ITEMS[value]
                embed.add_field(name="✨ Item Spécial", value=f"{value}\n*{item_info['description']}*", inline=False)
            elif reward_type == "jackpot":
                embed.add_field(name="💥 JACKPOT !!!", value=f"🎰 **{value} COINS** 🎰", inline=False)
        
        button.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

# ========== MISSIONS ==========

DAILY_MISSIONS = [
    {
        "id": "send_messages",
        "name": "💬 Bavard",
        "description": "Envoie 50 messages",
        "target": 50,
        "reward": {"pieces": 20, "ticket": "triple_match"}
    },
    {
        "id": "win_casino",
        "name": "🎰 Chanceux",
        "description": "Gagne 3 parties au casino",
        "target": 3,
        "reward": {"box": "silver"}
    },
    {
        "id": "scratch_tickets",
        "name": "🎫 Gratteur",
        "description": "Gratte 5 tickets",
        "target": 5,
        "reward": {"ticket": "lucky_7"}
    },
    {
        "id": "open_boxes",
        "name": "📦 Collectionneur",
        "description": "Ouvre 3 caisses",
        "target": 3,
        "reward": {"pieces": 50}
    }
]

WEEKLY_MISSIONS = [
    {
        "id": "casino_games",
        "name": "🎲 Joueur Assidu",
        "description": "Joue 50 parties au casino",
        "target": 50,
        "reward": {"box": "gold", "pieces": 100}
    },
    {
        "id": "earn_coins",
        "name": "💰 Riche",
        "description": "Gagne 500 pièces au casino (total)",
        "target": 500,
        "reward": {"item": "random", "pieces": 200}
    },
    {
        "id": "scratch_master",
        "name": "🎫 Maître Gratteur",
        "description": "Gratte 25 tickets",
        "target": 25,
        "reward": {"box": "legendary"}
    },
    {
        "id": "box_opener",
        "name": "📦 Dépensier",
        "description": "Ouvre 15 caisses",
        "target": 15,
        "reward": {"pieces": 300, "ticket": "royal"}
    }
]

def reset_daily_missions(missions_data, user_id):
    """Reset les missions quotidiennes"""
    user_id_str = str(user_id)
    today = datetime.now().date().isoformat()
    
    if user_id_str not in missions_data:
        missions_data[user_id_str] = {}
    
    if missions_data[user_id_str].get("last_daily_reset") != today:
        missions_data[user_id_str]["daily"] = {m["id"]: 0 for m in DAILY_MISSIONS}
        missions_data[user_id_str]["daily_claimed"] = []
        missions_data[user_id_str]["last_daily_reset"] = today

def reset_weekly_missions(missions_data, user_id):
    """Reset les missions hebdomadaires"""
    user_id_str = str(user_id)
    now = datetime.now()
    week_num = now.isocalendar()[1]
    
    if user_id_str not in missions_data:
        missions_data[user_id_str] = {}
    
    if missions_data[user_id_str].get("last_weekly_reset") != week_num:
        missions_data[user_id_str]["weekly"] = {m["id"]: 0 for m in WEEKLY_MISSIONS}
        missions_data[user_id_str]["weekly_claimed"] = []
        missions_data[user_id_str]["last_weekly_reset"] = week_num

def update_mission_progress(missions_data, user_id, mission_type, amount=1):
    """Met à jour la progression d'une mission"""
    user_id_str = str(user_id)
    reset_daily_missions(missions_data, user_id)
    reset_weekly_missions(missions_data, user_id)
    
    if mission_type in missions_data[user_id_str].get("daily", {}):
        missions_data[user_id_str]["daily"][mission_type] += amount
    
    if mission_type in missions_data[user_id_str].get("weekly", {}):
        missions_data[user_id_str]["weekly"][mission_type] += amount

# ========== COMMANDES ==========

async def setup_addictive_systems(bot, users_data, save_users_callback):
    
    scratch_data = load_data(SCRATCH_FILE, {"streak": {}})
    boxes_data = load_data(BOXES_FILE, {"jackpot": 0})
    missions_data = load_data(MISSIONS_FILE)
    items_inventory = load_data(ITEMS_FILE)
    
    def save_scratch():
        save_data(SCRATCH_FILE, scratch_data)
    
    def save_boxes():
        save_data(BOXES_FILE, boxes_data)
    
    def save_missions():
        save_data(MISSIONS_FILE, missions_data)
    
    def save_items():
        save_data(ITEMS_FILE, items_inventory)
    
    # ========== TICKETS ==========
    
    tickets_group = app_commands.Group(name="tickets", description="Tickets à gratter")
    bot.tree.add_command(tickets_group)

    @tickets_group.command(name="acheter", description="Acheter un ticket à gratter")
    @app_commands.describe(type="Type de ticket")
    @app_commands.choices(type=[
        app_commands.Choice(name="💎 Triple Match (10 pièces)", value="triple_match"),
        app_commands.Choice(name="🍀 Lucky 7 (25 pièces)", value="lucky_7"),
        app_commands.Choice(name="💰 Jackpot (50 pièces)", value="jackpot"),
        app_commands.Choice(name="👑 Royal Scratch (100 pièces)", value="royal"),
        app_commands.Choice(name="🎁 Mystery Box (5 pièces)", value="mystery")
    ])
    async def ticket_buy(interaction: discord.Interaction, type: str):
        user_id = str(interaction.user.id)
        config = TICKET_TYPES[type]
        
        if users_data[user_id]["pieces"] < config["price"]:
            await interaction.response.send_message(
                f"❌ Tu n'as pas assez de pièces ! Il te faut {config['price']} pièces.",
                ephemeral=True
            )
            return
        
        users_data[user_id]["pieces"] -= config["price"]
        save_users_callback()
        
        if user_id not in scratch_data["streak"]:
            scratch_data["streak"][user_id] = 0
        
        scratch_data["streak"][user_id] += 1
        is_free = scratch_data["streak"][user_id] >= 5
        
        if is_free:
            scratch_data["streak"][user_id] = 0
            users_data[user_id]["pieces"] += config["price"]
            save_users_callback()
        
        save_scratch()
        
        ticket = generate_ticket(type)
        
        update_mission_progress(missions_data, interaction.user.id, "scratch_tickets")
        save_missions()
        
        view = ScratchView(ticket, interaction.user.id, users_data, save_users_callback)
        embed = view.create_ticket_embed()
        embed.add_field(name="Description", value=config["description"], inline=False)
        
        if is_free:
            embed.add_field(
                name="🎉 STREAK BONUS !",
                value="Tu as acheté 5 tickets d'affilée, celui-ci est **GRATUIT** !",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, view=view)
    
    @tickets_group.command(name="voir", description="Voir les tickets disponibles et leurs descriptions")
    async def tickets_list(interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎫 Tickets à gratter disponibles",
            description="Choisis un ticket avec `/tickets acheter`.",
            color=discord.Color.blue()
        )
        
        for ticket_id, config in TICKET_TYPES.items():
            embed.add_field(
                name=f"{config['name']} - {config['price']} pièces",
                value=f"{config['description']}\nGrille {config['grid'][0]}x{config['grid'][1]}",
                inline=False
            )
        
        embed.add_field(
            name="🔥 Bonus Streak",
            value="Achète 5 tickets d'affilée → Le 6ème est **GRATUIT** !",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    # ========== LOOT BOXES ==========
    
    caisses_group = app_commands.Group(name="caisses", description="Caisses et récompenses")
    bot.tree.add_command(caisses_group)

    @caisses_group.command(name="acheter", description="Acheter une caisse")
    @app_commands.describe(type="Type de caisse")
    @app_commands.choices(type=[
        app_commands.Choice(name="📦 Caisse Bronze (20 pièces)", value="bronze"),
        app_commands.Choice(name="🎁 Caisse Argent (50 pièces)", value="silver"),
        app_commands.Choice(name="💎 Caisse Or (100 pièces)", value="gold"),
        app_commands.Choice(name="👑 Caisse Légendaire (250 pièces)", value="legendary")
    ])
    async def box_buy(interaction: discord.Interaction, type: str):
        user_id = str(interaction.user.id)
        config = BOX_TYPES[type]
        
        if users_data[user_id]["pieces"] < config["price"]:
            await interaction.response.send_message(
                f"❌ Tu n'as pas assez de pièces ! Il te faut {config['price']} pièces.",
                ephemeral=True
            )
            return
        
        users_data[user_id]["pieces"] -= config["price"]
        save_users_callback()
        
        rewards = open_box(type, interaction.user.id, boxes_data)
        save_boxes()
        
        for reward_type, value in rewards:
            if reward_type == "pieces":
                users_data[user_id]["pieces"] += value
            elif reward_type == "ticket":
                if "free_tickets" not in users_data[user_id]:
                    users_data[user_id]["free_tickets"] = []
                users_data[user_id]["free_tickets"].append(value)
            elif reward_type == "item":
                if user_id not in items_inventory:
                    items_inventory[user_id] = []
                items_inventory[user_id].append(value)
                save_items()
            elif reward_type == "jackpot":
                users_data[user_id]["pieces"] += value
        
        save_users_callback()
        
        update_mission_progress(missions_data, interaction.user.id, "open_boxes")
        save_missions()
        
        view = BoxOpenView(type, rewards, interaction.user.id)
        
        embed = discord.Embed(
            title=f"🎁 {config['name']}",
            description=(
                f"Prix : **{config['price']} pièces**\n"
                "Clique sur le bouton pour ouvrir ta caisse !"
            ),
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Contenu possible",
            value=(
                f"💰 {config['contents']['pieces'][0]}-{config['contents']['pieces'][1]} pièces\n"
                f"🎫 {int(config['contents']['ticket_chance'] * 100)}% ticket\n"
                f"✨ {int(config['contents']['item_chance'] * 100)}% item\n"
                "🎰 1% jackpot"
            ),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, view=view)
    
    @caisses_group.command(name="voir", description="Voir les caisses disponibles et leurs contenus")
    async def boxes_list(interaction: discord.Interaction):
        embed = discord.Embed(
            title="📦 Caisses disponibles",
            description="Choisis une caisse avec `/caisses acheter`.\n\n**Contenu possible :** pièces, tickets gratuits, objets spéciaux et jackpot progressif.",
            color=discord.Color.purple()
        )
        
        for box_id, config in BOX_TYPES.items():
            coins_range = config["contents"]["pieces"]
            embed.add_field(
                name=f"{config['name']} - {config['price']} pièces",
                value=f"💰 {coins_range[0]}-{coins_range[1]} pièces\n🎫 {int(config['contents']['ticket_chance']*100)}% ticket\n✨ {int(config['contents']['item_chance']*100)}% item",
                inline=True
            )
        
        jackpot = boxes_data.get("jackpot", 0)
        embed.add_field(
            name="🎰 Jackpot Progressif",
            value=f"**{jackpot} pièces** (1% chance de gagner)",
            inline=False
        )
        
        user_id_str = str(interaction.user.id)
        if user_id_str in boxes_data:
            pity = boxes_data[user_id_str].get("pity", 0)
            embed.add_field(
                name="🍀 Ton Pity System",
                value=f"{pity}/10 caisses sans item (item garanti à 10)",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    # ========== MISSIONS ==========
    
    @bot.tree.command(name="missions", description="Voir tes missions quotidiennes et hebdomadaires")
    async def missions_cmd(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        reset_daily_missions(missions_data, user_id)
        reset_weekly_missions(missions_data, user_id)
        
        embed = discord.Embed(
            title="📋 Missions",
            color=discord.Color.green()
        )
        
        daily_text = ""
        for mission in DAILY_MISSIONS:
            progress = missions_data[user_id]["daily"].get(mission["id"], 0)
            claimed = mission["id"] in missions_data[user_id].get("daily_claimed", [])
            
            if claimed:
                status = "✅"
            elif progress >= mission["target"]:
                status = "🎁"
            else:
                status = f"{progress}/{mission['target']}"
            
            daily_text += f"{status} **{mission['name']}**\n{mission['description']}\n\n"
        
        embed.add_field(name="🌅 Quotidiennes (reset 00h)", value=daily_text, inline=False)
        
        weekly_text = ""
        for mission in WEEKLY_MISSIONS:
            progress = missions_data[user_id]["weekly"].get(mission["id"], 0)
            claimed = mission["id"] in missions_data[user_id].get("weekly_claimed", [])
            
            if claimed:
                status = "✅"
            elif progress >= mission["target"]:
                status = "🎁"
            else:
                status = f"{progress}/{mission['target']}"
            
            weekly_text += f"{status} **{mission['name']}**\n{mission['description']}\n\n"
        
        embed.add_field(name="📅 Hebdomadaires (reset lundi)", value=weekly_text, inline=False)
        
        embed.set_footer(text="Utilise /claim_mission pour récupérer tes récompenses !")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="recuperer_mission", description="Récupérer la récompense d'une mission complétée")
    @app_commands.describe(mission_id="ID de la mission", type="Daily ou Weekly")
    @app_commands.choices(type=[
        app_commands.Choice(name="Quotidienne", value="daily"),
        app_commands.Choice(name="Hebdomadaire", value="weekly")
    ])
    async def claim_mission(interaction: discord.Interaction, mission_id: str, type: str):
        user_id = str(interaction.user.id)
        
        reset_daily_missions(missions_data, user_id)
        reset_weekly_missions(missions_data, user_id)
        
        missions_list = DAILY_MISSIONS if type == "daily" else WEEKLY_MISSIONS
        mission = next((m for m in missions_list if m["id"] == mission_id), None)
        
        if not mission:
            await interaction.response.send_message("❌ Mission introuvable !", ephemeral=True)
            return
        
        progress = missions_data[user_id][type].get(mission_id, 0)
        claimed_list = f"{type}_claimed"
        
        if mission_id in missions_data[user_id].get(claimed_list, []):
            await interaction.response.send_message("❌ Tu as déjà récupéré cette récompense !", ephemeral=True)
            return
        
        if progress < mission["target"]:
            await interaction.response.send_message(
                f"❌ Mission non complétée ! ({progress}/{mission['target']})",
                ephemeral=True
            )
            return
        
        reward_text = []
        
        if "pièces" in mission["reward"]:
            users_data[user_id]["pieces"] += mission["reward"]["pieces"]
            reward_text.append(f"💰 {mission['reward']['pieces']} pièces")
        
        if "ticket" in mission["reward"]:
            if "free_tickets" not in users_data[user_id]:
                users_data[user_id]["free_tickets"] = []
            users_data[user_id]["free_tickets"].append(mission["reward"]["ticket"])
            ticket_name = TICKET_TYPES[mission["reward"]["ticket"]]["name"]
            reward_text.append(f"🎫 {ticket_name}")
        
        if "box" in mission["reward"]:
            rewards = open_box(mission["reward"]["box"], interaction.user.id, boxes_data)
            for reward_type, value in rewards:
                if reward_type == "pieces":
                    users_data[user_id]["pieces"] += value
                    reward_text.append(f"💰 {value} pièces (caisse)")
                elif reward_type == "item":
                    if user_id not in items_inventory:
                        items_inventory[user_id] = []
                    items_inventory[user_id].append(value)
                    reward_text.append(f"✨ {value}")
            save_boxes()
            save_items()
        
        if "item" in mission["reward"]:
            if mission["reward"]["item"] == "random":
                item = random.choice(DROPPABLE_ITEMS)
            else:
                item = mission["reward"]["item"]
            
            if user_id not in items_inventory:
                items_inventory[user_id] = []
            items_inventory[user_id].append(item)
            reward_text.append(f"✨ {item}")
            save_items()
        
        save_users_callback()
        
        if claimed_list not in missions_data[user_id]:
            missions_data[user_id][claimed_list] = []
        missions_data[user_id][claimed_list].append(mission_id)
        save_missions()
        
        embed = discord.Embed(
            title="🎉 Mission complétée !",
            description=f"**{mission['name']}**\n\n**Récompenses obtenues :**\n" + "\n".join(reward_text),
            color=discord.Color.gold()
        )
        
        await interaction.response.send_message(embed=embed)