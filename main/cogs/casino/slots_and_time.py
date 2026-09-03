import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
import asyncio
from datetime import datetime, timedelta

from utils import check_cooldown, set_cooldown  # cooldown persistant — voir utils.py

# Fichier de données
SLOTS_FILE = "bot_data/slots_data.json"

# ========== MACHINE À SOUS ==========

SLOT_SYMBOLS = {
    "🍒": {"name": "Cerise", "value": 2, "weight": 30},
    "🍋": {"name": "Citron", "value": 3, "weight": 25},
    "🔔": {"name": "Cloche", "value": 5, "weight": 20},
    "💎": {"name": "Diamant", "value": 10, "weight": 15},
    "7️⃣": {"name": "Sept", "value": 50, "weight": 8},
    "👑": {"name": "Couronne", "value": 100, "weight": 5},
    "🎰": {"name": "Casino", "value": 25, "weight": 12}
}

MULTIPLIERS = [
    {"symbol": "⭐", "value": 2, "chance": 0.15},   # 15% chance x2
    {"symbol": "💫", "value": 5, "chance": 0.05},   # 5% chance x5
    {"symbol": "✨", "value": 10, "chance": 0.02}   # 2% chance x10
]

def get_weighted_symbol():
    """Tire un symbole selon les poids"""
    symbols = list(SLOT_SYMBOLS.keys())
    weights = [SLOT_SYMBOLS[s]["weight"] for s in symbols]
    return random.choices(symbols, weights=weights)[0]

def check_multiplier():
    """Vérifie si un multiplicateur apparaît"""
    for mult in MULTIPLIERS:
        if random.random() < mult["chance"]:
            return mult["symbol"], mult["value"]
    return None, 1

def calculate_win(reels, bet, multiplier):
    """Calcule le gain"""
    if reels[0] == reels[1] == reels[2]:
        base_win = SLOT_SYMBOLS[reels[0]]["value"] * bet
        return base_win * multiplier, "triple"
    
    elif reels[0] == reels[1] or reels[1] == reels[2]:
        symbol = reels[0] if reels[0] == reels[1] else reels[1]
        base_win = SLOT_SYMBOLS[symbol]["value"] * bet * 0.5
        return int(base_win * multiplier), "double"
    
    return 0, None

def is_near_win(reels):
    """Détecte un near-win pour créer du suspense"""
    high_value = ["7️⃣", "👑", "💎"]
    
    if reels[0] == reels[1] and reels[0] in high_value:
        return True, reels[0]
    
    if reels[1] == reels[2] and reels[1] in high_value:
        return True, reels[1]
    
    if reels.count("7️⃣") == 2 or reels.count("👑") == 2:
        symbol = "7️⃣" if reels.count("7️⃣") == 2 else "👑"
        return True, symbol
    
    return False, None

# ========== CYCLE JOUR/NUIT ==========

def get_time_period():
    """Retourne la période actuelle (jour/nuit/aube/crépuscule)"""
    hour = datetime.now().hour
    
    if 6 <= hour < 8:
        return "aube", "🌅"
    elif 8 <= hour < 18:
        return "jour", "☀️"
    elif 18 <= hour < 20:
        return "crepuscule", "🌆"
    else:
        return "nuit", "🌙"

def get_time_bonus(period):
    """Retourne les bonus selon la période"""
    bonuses = {
        "aube": {
            "name": "Aube Dorée",
            "slots_multiplier": 1.25,
            "work_bonus": 1.15,
            "crime_bonus": 1.0,
            "ticket_discount": 0.9,  # -10%
            "description": "Les machines à sous rapportent +25% !\nLes tickets coûtent -10% !"
        },
        "jour": {
            "name": "Journée Productive",
            "slots_multiplier": 1.0,
            "work_bonus": 1.3,
            "crime_bonus": 0.8,
            "ticket_discount": 1.0,
            "description": "Le travail paie +30% !\nLes crimes sont plus risqués."
        },
        "crepuscule": {
            "name": "Heure Magique",
            "slots_multiplier": 1.5,
            "work_bonus": 1.0,
            "crime_bonus": 1.2,
            "ticket_discount": 0.85,  # -15%
            "description": "✨ HAPPY HOUR ✨\nMachines à sous : +50% gains !\nTickets : -15% !"
        },
        "nuit": {
            "name": "Nuit Mystérieuse",
            "slots_multiplier": 1.1,
            "work_bonus": 0.7,
            "crime_bonus": 1.5,
            "ticket_discount": 1.0,
            "description": "Les crimes rapportent +50% !\nLes caisses peuvent drop double !"
        }
    }
    
    return bonuses.get(period, bonuses["jour"])

class SlotsView(discord.ui.View):
    def __init__(self, bet, user_id, users_data, slots_data, save_users_callback, save_slots_callback):
        super().__init__(timeout=60)
        self.bet = bet
        self.user_id = str(user_id)
        self.users_data = users_data
        self.slots_data = slots_data
        self.save_users = save_users_callback
        self.save_slots = save_slots_callback
        self.reels = [None, None, None]
        self.spinning = False
        self.multiplier_symbol = None
        self.multiplier_value = 1
    
    @discord.ui.button(label="🎰 SPIN", style=discord.ButtonStyle.success, custom_id="spin")
    async def spin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Ce n'est pas ta machine !", ephemeral=True)
            return
        
        if self.spinning:
            await interaction.response.send_message("❌ La machine tourne déjà !", ephemeral=True)
            return
        
        self.spinning = True
        button.disabled = True
        
        self.multiplier_symbol, self.multiplier_value = check_multiplier()
        
        await self.animate_spin(interaction)
        
        win_amount, win_type = calculate_win(self.reels, self.bet, self.multiplier_value)
        
        jackpot_won = False
        if self.reels[0] == self.reels[1] == self.reels[2] == "7️⃣":
            jackpot_won = True
            jackpot_amount = self.slots_data.get("jackpot", 0)
            win_amount += jackpot_amount
            self.slots_data["jackpot"] = 0
        else:
            self.slots_data["jackpot"] = self.slots_data.get("jackpot", 0) + max(1, self.bet // 10)
        
        near_win, near_symbol = is_near_win(self.reels)
        
        if win_amount > 0:
            self.users_data[self.user_id]["pieces"] += win_amount
        
        self.save_users()
        self.save_slots()
        
        # Cooldown de 10s — démarre ici, une fois l'action précédente (le spin) totalement terminée
        set_cooldown(self.user_id, "slots", datetime.now() + timedelta(seconds=10))
        
        embed = self.create_result_embed(win_amount, win_type, jackpot_won, near_win, near_symbol)
        
        await interaction.edit_original_response(embed=embed, view=None)
    
    async def animate_spin(self, interaction):
        """Animation de rotation des rouleaux"""
        period, emoji = get_time_period()
        bonus = get_time_bonus(period)
        
        # Phase 1 : Démarrage
        embed = discord.Embed(
            title="🎰 MACHINE À SOUS 🎰",
            description="```\n🎲 🎲 🎲\n```\n*CLING CLING CLING*",
            color=discord.Color.blue()
        )
        embed.add_field(name=f"{emoji} {bonus['name']}", value=f"Multiplicateur: x{bonus['slots_multiplier']}", inline=False)
        await interaction.response.edit_message(embed=embed)
        await asyncio.sleep(0.8)
        
        # Phase 2-4 : Rotation des rouleaux
        for i in range(3):
            self.reels[i] = get_weighted_symbol()
            
            display = ["❓", "❓", "❓"]
            for j in range(i + 1):
                display[j] = self.reels[j]
            
            mult_text = f"\n{self.multiplier_symbol} **MULTIPLICATEUR x{self.multiplier_value}** {self.multiplier_symbol}" if self.multiplier_symbol and i == 0 else ""
            
            embed = discord.Embed(
                title="🎰 MACHINE À SOUS 🎰",
                description=f"```\n{display[0]} {display[1]} {display[2]}\n```\n*{'DING! ' * (i+1)}*{mult_text}",
                color=discord.Color.gold()
            )
            embed.add_field(name=f"{emoji} {bonus['name']}", value=f"Multiplicateur: x{bonus['slots_multiplier']}", inline=False)
            
            await interaction.edit_original_response(embed=embed)
            await asyncio.sleep(1.0)
        
        period_mult = bonus["slots_multiplier"]
        if period_mult != 1.0:
            self.multiplier_value *= period_mult
    
    def create_result_embed(self, win_amount, win_type, jackpot_won, near_win, near_symbol):
        """Crée l'embed du résultat final"""
        period, emoji = get_time_period()
        bonus = get_time_bonus(period)
        
        if jackpot_won:
            embed = discord.Embed(
                title="🎰 ✨ JACKPOT PROGRESSIF ✨ 🎰",
                description=f"```\n{self.reels[0]} {self.reels[1]} {self.reels[2]}\n```\n***💥 TRIPLE 7️⃣ JACKPOT 💥***",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="🎊 ÉNORME VICTOIRE 🎊",
                value=f"**+{win_amount} pièces** !\n\n*Le jackpot progressif a été remporté !*",
                inline=False
            )
        
        elif win_amount > 0:
            if win_type == "triple":
                title_emoji = "🎉"
                status = "TRIPLE GAGNANT"
            else:
                title_emoji = "✅"
                status = "PAIRE GAGNANTE"
            
            mult_text = f"\n{self.multiplier_symbol} Multiplicateur x{self.multiplier_value:.1f} appliqué !" if self.multiplier_value > 1 else ""
            
            embed = discord.Embed(
                title=f"🎰 {title_emoji} {status} {title_emoji} 🎰",
                description=f"```\n{self.reels[0]} {self.reels[1]} {self.reels[2]}\n```",
                color=discord.Color.green()
            )
            embed.add_field(
                name="💰 Gains",
                value=f"**+{win_amount} pièces**{mult_text}",
                inline=False
            )
        
        elif near_win:
            embed = discord.Embed(
                title="🎰 Presque gagné ! 🎰",
                description=f"```\n{self.reels[0]} {self.reels[1]} {self.reels[2]}\n```",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="😮 Si proche !",
                value=f"Il te manquait juste un **{near_symbol}** pour le jackpot !\nRetente ta chance !",
                inline=False
            )
        
        else:
            embed = discord.Embed(
                title="🎰 Machine à sous 🎰",
                description=f"```\n{self.reels[0]} {self.reels[1]} {self.reels[2]}\n```",
                color=discord.Color.red()
            )
            embed.add_field(
                name="❌ Perdu",
                value=f"Pas de chance cette fois...\nMise perdue : -{self.bet} pièces",
                inline=False
            )
        
        embed.add_field(
            name="💵 Solde",
            value=f"{self.users_data[self.user_id]['pieces']} pièces",
            inline=True
        )
        
        current_jackpot = self.slots_data.get("jackpot", 0)
        embed.add_field(
            name="🎰 Jackpot progressif",
            value=f"{current_jackpot} pièces\n*(Triple 7️⃣ pour gagner)*",
            inline=True
        )
        
        embed.add_field(
            name=f"{emoji} Période actuelle",
            value=f"{bonus['name']}\n{bonus['description'].split(chr(10))[0]}",
            inline=False
        )
        
        return embed

# ========== COMMANDES ==========

async def setup_slots_and_time(bot, users_data, save_users_callback):
    
    slots_data = {}
    if os.path.exists(SLOTS_FILE):
        with open(SLOTS_FILE, 'r', encoding='utf-8') as f:
            slots_data = json.load(f)
    
    if "jackpot" not in slots_data:
        slots_data["jackpot"] = 100  # Jackpot de départ
    
    def save_slots():
        os.makedirs(os.path.dirname(SLOTS_FILE), exist_ok=True)
        with open(SLOTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(slots_data, f, indent=4)
    
    @bot.tree.command(name="machine_a_sous", description="Jouer à la machine à sous (avec jackpot progressif)")
    @app_commands.describe(mise="Montant de ta mise")
    async def slots_cmd(interaction: discord.Interaction, mise: int):
        user_id = str(interaction.user.id)
        
        # Cooldown 5s — démarre uniquement quand le spin précédent est totalement terminé (voir spin_button)
        dispo, time_left_s = check_cooldown(user_id, "slots")
        if not dispo:
            await interaction.response.send_message(
                f"⏰ La machine refroidit ! Attends encore {time_left_s:.1f}s.",
                ephemeral=True
            )
            return
        
        if mise < 1:
            await interaction.response.send_message("❌ La mise minimum est de 1 pièce !", ephemeral=True)
            return
        
        if mise > 1000:
            await interaction.response.send_message("❌ La mise maximum est de 1000 pièces !", ephemeral=True)
            return
        
        if users_data[user_id]["pieces"] < mise:
            await interaction.response.send_message(
                f"❌ Tu n'as pas assez de pièces ! (Tu as {users_data[user_id]['pieces']} pièces)",
                ephemeral=True
            )
            return
        
        users_data[user_id]["pieces"] -= mise
        save_users_callback()
        
        view = SlotsView(mise, interaction.user.id, users_data, slots_data, save_users_callback, save_slots)
        
        period, emoji = get_time_period()
        bonus = get_time_bonus(period)
        
        embed = discord.Embed(
            title="🎰 MACHINE À SOUS 🎰",
            description=f"Mise : **{mise} pièces**\n\nClique sur **SPIN** pour lancer !",
            color=discord.Color.blue()
        )
        embed.add_field(
            name=f"{emoji} {bonus['name']}",
            value=bonus['description'],
            inline=False
        )
        embed.add_field(
            name="🎰 Jackpot progressif",
            value=f"**{slots_data.get('jackpot', 0)} pièces**\n*(Triple 7️⃣ pour gagner !)*",
            inline=False
        )
        embed.add_field(
            name="💡 Symboles",
            value="🍒 x2 | 🍋 x3 | 🔔 x5 | 💎 x10\n🎰 x25 | 7️⃣ x50 | 👑 x100",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, view=view)
    
    @bot.tree.command(name="periode", description="Voir la période actuelle et les bonus")
    async def time_cmd(interaction: discord.Interaction):
        period, emoji = get_time_period()
        bonus = get_time_bonus(period)
        
        hour = datetime.now().hour
        if hour < 6:
            next_period = "🌅 Aube (6h)"
        elif hour < 8:
            next_period = "☀️ Jour (8h)"
        elif hour < 18:
            next_period = "🌆 Crépuscule (18h)"
        elif hour < 20:
            next_period = "🌙 Nuit (20h)"
        else:
            next_period = "🌅 Aube (6h demain)"
        
        embed = discord.Embed(
            title=f"{emoji} {bonus['name']}",
            description=bonus['description'],
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🎰 Machines à sous",
            value=f"x{bonus['slots_multiplier']} gains",
            inline=True
        )
        embed.add_field(
            name="💼 Travail (/work)",
            value=f"x{bonus['work_bonus']} salaire",
            inline=True
        )
        embed.add_field(
            name="🔫 Crime (/crime)",
            value=f"x{bonus['crime_bonus']} butin",
            inline=True
        )
        
        if bonus['ticket_discount'] != 1.0:
            discount = int((1 - bonus['ticket_discount']) * 100)
            embed.add_field(
                name="🎫 Tickets",
                value=f"-{discount}% de réduction !",
                inline=True
            )
        
        embed.add_field(
            name="⏰ Prochaine période",
            value=next_period,
            inline=False
        )
        
        embed.add_field(
            name="📅 Cycle complet",
            value="🌅 **Aube** (6h-8h) : Slots +25%, Tickets -10%\n"
                  "☀️ **Jour** (8h-18h) : Work +30%\n"
                  "🌆 **Crépuscule** (18h-20h) : HAPPY HOUR ! Slots +50%, Tickets -15%\n"
                  "🌙 **Nuit** (20h-6h) : Crime +50%",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    save_slots()
