"""
Extensions avancées pour le bot Discord
Mariage, Gangs, Classements, Achievements, Work, Crime, Heist, Trade, Duel
"""

import discord
from discord import app_commands
import random
from datetime import datetime, timedelta
import json
import os

from utils import check_cooldown, set_cooldown  # cooldowns persistants — voir utils.py

# ========== FICHIERS DE DONNÉES ==========
DATA_DIR = "bot_data"
MARRIAGES_FILE = f"{DATA_DIR}/marriages.json"
GANGS_FILE = f"{DATA_DIR}/gangs.json"
STATS_FILE = f"{DATA_DIR}/game_stats.json"
ACHIEVEMENTS_FILE = f"{DATA_DIR}/achievements.json"
COOLDOWNS_FILE = f"{DATA_DIR}/cooldowns.json"

def load_data(file_path, default=None):
    if default is None:
        default = {}
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

marriages = load_data(MARRIAGES_FILE)  # {user_id: partner_id}
gangs = load_data(GANGS_FILE)  # {gang_id: {"name": str, "leader": user_id, "members": [], "bank": int}}
game_stats = load_data(STATS_FILE)  # {user_id: {"casino_wins": int, "casino_losses": int, "total_bet": int, "total_won": int, "total_lost": int}}
achievements = load_data(ACHIEVEMENTS_FILE)  # {user_id: [achievement_ids]}
cooldowns = load_data(COOLDOWNS_FILE)  # {user_id: {"work": timestamp, "crime": timestamp, "heist": timestamp}}

# ========== DÉFINITION DES ACHIEVEMENTS ==========
ACHIEVEMENT_LIST = {
    "first_blood": {"name": "🩸 First Blood", "description": "Perds tes premiers 100 pièces au casino", "reward": 50},
    "gambler": {"name": "🎰 Gambler", "description": "Joue 100 parties au casino", "reward": 500},
    "high_roller": {"name": "💎 High Roller", "description": "Mise 10000 pièces en une seule partie", "reward": 1000},
    "lucky_streak": {"name": "🍀 Lucky Streak", "description": "Gagne 10 parties de casino d'affilée", "reward": 2000},
    "broke": {"name": "💸 Broke", "description": "Tombe à 0 pièces", "reward": 100},
    "millionaire": {"name": "💰 Millionaire", "description": "Atteins 10000 pièces", "reward": 500},
    "married": {"name": "💑 Married", "description": "Marie-toi avec quelqu'un", "reward": 300},
    "divorced": {"name": "💔 Divorced", "description": "Divorce (triste...)", "reward": 100},
    "gang_leader": {"name": "👑 Gang Leader", "description": "Crée un gang", "reward": 500},
    "worker": {"name": "👷 Worker", "description": "Travaille 50 fois", "reward": 1000},
    "criminal": {"name": "🔫 Criminal", "description": "Commets 20 crimes", "reward": 800},
    "heist_master": {"name": "🏦 Heist Master", "description": "Réussis 10 braquages", "reward": 1500},
}

def check_achievement(user_id, achievement_id, users_data):
    """Vérifie et débloque un achievement"""
    user_id = str(user_id)
    if user_id not in achievements:
        achievements[user_id] = []
    
    if achievement_id not in achievements[user_id]:
        achievements[user_id].append(achievement_id)
        save_data(ACHIEVEMENTS_FILE, achievements)
        
        achievement = ACHIEVEMENT_LIST[achievement_id]
        users_data[user_id]["pieces"] += achievement["reward"]
        
        return True, achievement
    return False, None

def update_game_stats(user_id, stat_type, amount=1):
    """Met à jour les statistiques de jeu"""
    user_id = str(user_id)
    if user_id not in game_stats:
        game_stats[user_id] = {
            "casino_wins": 0,
            "casino_losses": 0,
            "total_bet": 0,
            "total_won": 0,
            "total_lost": 0,
            "casino_plays": 0,
            "work_count": 0,
            "crime_count": 0,
            "heist_count": 0,
            "current_streak": 0
        }
    
    game_stats[user_id][stat_type] += amount
    save_data(STATS_FILE, game_stats)

# ========== SYSTÈME DE MARIAGE ==========

async def setup_marriage_commands(bot, users_data, save_users_data):
    @bot.tree.command(name="epouser", description="Demande quelqu'un en mariage")
    @app_commands.describe(personne="La personne à demander en mariage")
    async def marry(interaction: discord.Interaction, personne: discord.Member):
        user_id = str(interaction.user.id)
        partner_id = str(personne.id)
        
        if personne.bot:
            await interaction.response.send_message("❌ Tu ne peux pas épouser un bot !", ephemeral=True)
            return
        
        if user_id == partner_id:
            await interaction.response.send_message("❌ Tu ne peux pas t'épouser toi-même !", ephemeral=True)
            return
        
        if user_id in marriages:
            current_partner = await bot.fetch_user(int(marriages[user_id]))
            await interaction.response.send_message(f"❌ Tu es déjà marié(e) avec {current_partner.mention} !", ephemeral=True)
            return
        
        if partner_id in marriages:
            await interaction.response.send_message(f"❌ {personne.mention} est déjà marié(e) !", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="💍 Demande en mariage",
            description=f"{interaction.user.mention} demande {personne.mention} en mariage !\n\n💕 Acceptes-tu de partager tes gains et pertes ?",
            color=discord.Color.pink()
        )
        
        class MarriageView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
            
            @discord.ui.button(label="💕 Accepter", style=discord.ButtonStyle.success)
            async def accept(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id != personne.id:
                    await button_interaction.response.send_message("❌ Ce n'est pas ta demande !", ephemeral=True)
                    return
                
                marriages[user_id] = partner_id
                marriages[partner_id] = user_id
                save_data(MARRIAGES_FILE, marriages)
                
                unlocked1, achievement1 = check_achievement(user_id, "married", users_data)
                unlocked2, achievement2 = check_achievement(partner_id, "married", users_data)
                save_users_data()
                
                accept_embed = discord.Embed(
                    title="💑 Mariage célébré !",
                    description=f"🎉 {interaction.user.mention} et {personne.mention} sont maintenant mariés !\n\n💰 Vous partagez désormais 10% de vos gains !",
                    color=discord.Color.green()
                )
                
                if unlocked1 or unlocked2:
                    accept_embed.add_field(name="🏆 Achievement débloqué !", value=f"**{ACHIEVEMENT_LIST['married']['name']}** - +{ACHIEVEMENT_LIST['married']['reward']} pièces")
                
                await button_interaction.response.edit_message(embed=accept_embed, view=None)
            
            @discord.ui.button(label="💔 Refuser", style=discord.ButtonStyle.danger)
            async def decline(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id != personne.id:
                    await button_interaction.response.send_message("❌ Ce n'est pas ta demande !", ephemeral=True)
                    return
                
                decline_embed = discord.Embed(
                    title="💔 Demande refusée",
                    description=f"{personne.mention} a refusé la demande de {interaction.user.mention}...",
                    color=discord.Color.red()
                )
                
                await button_interaction.response.edit_message(embed=decline_embed, view=None)
        
        view = MarriageView()
        await interaction.response.send_message(embed=embed, view=view)
    
    @bot.tree.command(name="divorce", description="Divorce de ton partenaire")
    async def divorce(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        if user_id not in marriages:
            await interaction.response.send_message("❌ Tu n'es pas marié(e) !", ephemeral=True)
            return
        
        partner_id = marriages[user_id]
        partner = await bot.fetch_user(int(partner_id))
        
        del marriages[user_id]
        del marriages[partner_id]
        save_data(MARRIAGES_FILE, marriages)
        
        unlocked, achievement = check_achievement(user_id, "divorced", users_data)
        save_users_data()
        
        embed = discord.Embed(
            title="💔 Divorce prononcé",
            description=f"{interaction.user.mention} et {partner.mention} sont maintenant divorcés.\n\nVous ne partagez plus vos gains.",
            color=discord.Color.orange()
        )
        
        if unlocked:
            embed.add_field(name="🏆 Achievement débloqué", value=f"**{achievement['name']}** - +{achievement['reward']} pièces")
        
        await interaction.response.send_message(embed=embed)
        
        try:
            await partner.send(f"💔 {interaction.user.mention} a divorcé de toi sur **{interaction.guild.name}**...")
        except:
            pass
    
    @bot.tree.command(name="partenaire", description="Voir ton partenaire")
    async def partner(interaction: discord.Interaction, membre: discord.Member = None):
        target = membre or interaction.user
        user_id = str(target.id)
        
        if user_id not in marriages:
            await interaction.response.send_message(f"💔 {target.mention} n'est pas marié(e).", ephemeral=True)
            return
        
        partner = await bot.fetch_user(int(marriages[user_id]))
        
        embed = discord.Embed(
            title="💑 Partenaire",
            description=f"{target.mention} est marié(e) avec {partner.mention}",
            color=discord.Color.pink()
        )
        embed.set_thumbnail(url=partner.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

# ========== SYSTÈME DE GANGS ==========

async def setup_gang_commands(bot, users_data, save_users_data):
    gang_group = app_commands.Group(name="gang", description="Système de gangs")
    bot.tree.add_command(gang_group)

    @gang_group.command(name="creer", description="Crée un gang")
    @app_commands.describe(nom="Nom du gang")
    async def gang_create(interaction: discord.Interaction, nom: str):
        user_id = str(interaction.user.id)
        
        for gang_id, gang_data in gangs.items():
            if user_id in gang_data["members"] or user_id == gang_data["leader"]:
                await interaction.response.send_message(f"❌ Tu es déjà dans le gang **{gang_data['name']}** !", ephemeral=True)
                return
        
        cost = 1000
        if users_data[user_id]["pieces"] < cost:
            await interaction.response.send_message(f"❌ Créer un gang coûte {cost} pièces !", ephemeral=True)
            return
        
        gang_id = str(len(gangs) + 1)
        gangs[gang_id] = {
            "name": nom,
            "leader": user_id,
            "members": [user_id],
            "bank": 0,
            "created_at": datetime.now().isoformat()
        }
        
        users_data[user_id]["pieces"] -= cost
        save_data(GANGS_FILE, gangs)
        save_users_data()
        
        unlocked, achievement = check_achievement(user_id, "gang_leader", users_data)
        save_users_data()
        
        embed = discord.Embed(
            title="👑 Gang créé !",
            description=f"Le gang **{nom}** a été créé !\n\n{interaction.user.mention} en est le leader.",
            color=discord.Color.purple()
        )
        embed.add_field(name="Membres", value="1")
        embed.add_field(name="Banque", value="0 pièces")
        
        if unlocked:
            embed.add_field(name="🏆 Achievement", value=f"**{achievement['name']}** - +{achievement['reward']} pièces", inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @gang_group.command(name="inviter", description="Invite quelqu'un dans ton gang")
    @app_commands.describe(membre="Membre à inviter")
    async def gang_invite(interaction: discord.Interaction, membre: discord.Member):
        user_id = str(interaction.user.id)
        target_id = str(membre.id)
        
        user_gang = None
        for gang_id, gang_data in gangs.items():
            if gang_data["leader"] == user_id:
                user_gang = gang_id
                break
        
        if not user_gang:
            await interaction.response.send_message("❌ Tu n'es pas leader d'un gang !", ephemeral=True)
            return
        
        for gang_id, gang_data in gangs.items():
            if target_id in gang_data["members"] or target_id == gang_data["leader"]:
                await interaction.response.send_message(f"❌ {membre.mention} est déjà dans un gang !", ephemeral=True)
                return
        
        gang_data = gangs[user_gang]
        
        embed = discord.Embed(
            title="📩 Invitation au gang",
            description=f"{membre.mention}, {interaction.user.mention} t'invite à rejoindre le gang **{gang_data['name']}** !",
            color=discord.Color.purple()
        )
        
        class GangInviteView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
            
            @discord.ui.button(label="✅ Accepter", style=discord.ButtonStyle.success)
            async def accept(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id != membre.id:
                    await button_interaction.response.send_message("❌ Ce n'est pas ton invitation !", ephemeral=True)
                    return
                
                gang_data["members"].append(target_id)
                save_data(GANGS_FILE, gangs)
                
                accept_embed = discord.Embed(
                    title="✅ Invitation acceptée !",
                    description=f"{membre.mention} a rejoint le gang **{gang_data['name']}** !",
                    color=discord.Color.green()
                )
                
                await button_interaction.response.edit_message(embed=accept_embed, view=None)
            
            @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.danger)
            async def decline(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id != membre.id:
                    await button_interaction.response.send_message("❌ Ce n'est pas ton invitation !", ephemeral=True)
                    return
                
                decline_embed = discord.Embed(
                    title="❌ Invitation refusée",
                    description=f"{membre.mention} a refusé l'invitation.",
                    color=discord.Color.red()
                )
                
                await button_interaction.response.edit_message(embed=decline_embed, view=None)
        
        view = GangInviteView()
        await interaction.response.send_message(embed=embed, view=view)
    
    @gang_group.command(name="deposer", description="Dépose des pièces dans la banque du gang")
    @app_commands.describe(montant="Montant à déposer")
    async def gang_deposit(interaction: discord.Interaction, montant: int):
        user_id = str(interaction.user.id)
        
        user_gang = None
        for gang_id, gang_data in gangs.items():
            if user_id in gang_data["members"] or user_id == gang_data["leader"]:
                user_gang = gang_data
                break
        
        if not user_gang:
            await interaction.response.send_message("❌ Tu n'es pas dans un gang !", ephemeral=True)
            return
        
        if montant < 10:
            await interaction.response.send_message("❌ Montant minimum : 10 pièces !", ephemeral=True)
            return
        
        if users_data[user_id]["pieces"] < montant:
            await interaction.response.send_message(f"❌ Tu n'as que {users_data[user_id]['pieces']} pièces !", ephemeral=True)
            return
        
        users_data[user_id]["pieces"] -= montant
        user_gang["bank"] += montant
        save_data(GANGS_FILE, gangs)
        save_users_data()
        
        embed = discord.Embed(
            title="💰 Dépôt effectué",
            description=f"{interaction.user.mention} a déposé **{montant} pièces** dans la banque du gang !",
            color=discord.Color.green()
        )
        embed.add_field(name="Banque du gang", value=f"💰 {user_gang['bank']} pièces")
        
        await interaction.response.send_message(embed=embed)
    
    @gang_group.command(name="retirer", description="Retire des pièces de la banque (leader seulement)")
    @app_commands.describe(montant="Montant à retirer")
    async def gang_withdraw(interaction: discord.Interaction, montant: int):
        user_id = str(interaction.user.id)
        
        user_gang = None
        gang_id_found = None
        for gang_id, gang_data in gangs.items():
            if gang_data["leader"] == user_id:
                user_gang = gang_data
                gang_id_found = gang_id
                break
        
        if not user_gang:
            await interaction.response.send_message("❌ Tu n'es pas leader d'un gang !", ephemeral=True)
            return
        
        if montant < 10:
            await interaction.response.send_message("❌ Montant minimum : 10 pièces !", ephemeral=True)
            return
        
        if user_gang["bank"] < montant:
            await interaction.response.send_message(f"❌ La banque n'a que {user_gang['bank']} pièces !", ephemeral=True)
            return
        
        user_gang["bank"] -= montant
        users_data[user_id]["pieces"] += montant
        save_data(GANGS_FILE, gangs)
        save_users_data()
        
        embed = discord.Embed(
            title="💸 Retrait effectué",
            description=f"{interaction.user.mention} a retiré **{montant} pièces** de la banque du gang !",
            color=discord.Color.orange()
        )
        embed.add_field(name="Banque du gang", value=f"💰 {user_gang['bank']} pièces")
        
        await interaction.response.send_message(embed=embed)
    
    @gang_group.command(name="info", description="Affiche les infos de ton gang")
    async def gang_info(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        user_gang = None
        for gang_id, gang_data in gangs.items():
            if user_id in gang_data["members"] or user_id == gang_data["leader"]:
                user_gang = gang_data
                break
        
        if not user_gang:
            await interaction.response.send_message("❌ Tu n'es pas dans un gang !", ephemeral=True)
            return
        
        leader = await bot.fetch_user(int(user_gang["leader"]))
        
        members_list = []
        for member_id in user_gang["members"]:
            member = await bot.fetch_user(int(member_id))
            members_list.append(member.mention)
        
        embed = discord.Embed(
            title=f"👑 {user_gang['name']}",
            color=discord.Color.purple()
        )
        embed.add_field(name="Leader", value=leader.mention, inline=True)
        embed.add_field(name="Membres", value=str(len(user_gang["members"])), inline=True)
        embed.add_field(name="Banque", value=f"💰 {user_gang['bank']} pièces", inline=True)
        embed.add_field(name="Liste des membres", value="\n".join(members_list), inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @gang_group.command(name="quitter", description="Quitte ton gang")
    async def gang_leave(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        user_gang = None
        gang_id_found = None
        for gang_id, gang_data in gangs.items():
            if user_id in gang_data["members"]:
                user_gang = gang_data
                gang_id_found = gang_id
                break
        
        if not user_gang:
            await interaction.response.send_message("❌ Tu n'es pas dans un gang !", ephemeral=True)
            return
        
        if user_gang["leader"] == user_id:
            await interaction.response.send_message(
                "❌ Tu es le leader. Utilise `/gang dissoudre` pour dissoudre le gang, ou transmets le lead à un autre membre.",
                ephemeral=True
            )
            return
        
        user_gang["members"].remove(user_id)
        save_data(GANGS_FILE, gangs)
        
        await interaction.response.send_message(f"✅ Tu as quitté le gang **{user_gang['name']}** !")
    
    @gang_group.command(name="dissoudre", description="Dissout ton gang (leader seulement)")
    async def gang_disband(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        user_gang = None
        gang_id_found = None
        for gang_id, gang_data in gangs.items():
            if gang_data["leader"] == user_id:
                user_gang = gang_data
                gang_id_found = gang_id
                break
        
        if not user_gang:
            await interaction.response.send_message("❌ Tu n'es pas leader d'un gang !", ephemeral=True)
            return
        
        # Retourner les pièces de la banque au leader
        bank_amount = user_gang["bank"]
        users_data[user_id]["pieces"] += bank_amount
        save_users_data()
        
        # Supprimer le gang
        del gangs[gang_id_found]
        save_data(GANGS_FILE, gangs)
        
        embed = discord.Embed(
            title="💔 Gang dissous",
            description=f"Le gang **{user_gang['name']}** a été dissous.",
            color=discord.Color.red()
        )
        embed.add_field(name="Banque retournée", value=f"💰 {bank_amount} pièces", inline=False)
        embed.add_field(name="Membres affectés", value=f"{len(user_gang['members'])} membre(s)", inline=False)
        
        await interaction.response.send_message(embed=embed)

# ========== CLASSEMENTS ==========
# /richest, /gambler, /loser et /business_leaderboard ont été fusionnés dans
# une seule commande /leaderboard [categorie] (voir addon_profil.py), qui lit
# directement `game_stats` de ce module et `business_data` de business_system.py.

# ========== ACHIEVEMENTS ==========

async def setup_achievement_commands(bot, users_data):
    @bot.tree.command(name="succes", description="Affiche tes succès")
    async def achievements_cmd(interaction: discord.Interaction, membre: discord.Member = None):
        target = membre or interaction.user
        user_id = str(target.id)
        
        user_achievements = achievements.get(user_id, [])
        
        embed = discord.Embed(
            title=f"🏆 Achievements de {target.display_name}",
            description=f"**{len(user_achievements)}/{len(ACHIEVEMENT_LIST)}** débloqués",
            color=discord.Color.gold()
        )
        
        for achievement_id, achievement_data in ACHIEVEMENT_LIST.items():
            unlocked = achievement_id in user_achievements
            status = "✅" if unlocked else "🔒"
            embed.add_field(
                name=f"{status} {achievement_data['name']}",
                value=f"{achievement_data['description']}\n💰 Récompense : {achievement_data['reward']} pièces",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

# ========== WORK, CRIME, HEIST ==========
# Cooldowns persistés dans bot_data/cooldowns.json via utils.py — ils survivent
# désormais aux redémarrages du bot (avant : dicts en mémoire, remis à zéro à chaque restart).

async def setup_economy_commands(bot, users_data, save_users_data):
    @bot.tree.command(name="travailler", description="Travaille pour gagner des pièces")
    async def work(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        now = datetime.now()
        
        dispo, time_left_s = check_cooldown(user_id, "work")
        if not dispo:
            minutes = int(time_left_s / 60)
            seconds = int(time_left_s % 60)
            await interaction.response.send_message(
                f"⏰ Tu es fatigué ! Attends encore {minutes}m {seconds}s avant de retravailler.",
                ephemeral=True
            )
            return
        
        from slots_and_time import get_time_period, get_time_bonus
        period, emoji = get_time_period()
        bonus_data = get_time_bonus(period)
        work_multiplier = bonus_data["work_bonus"]
        
        jobs = [
            {"name": "🍕 Livreur de pizza", "min": 50, "max": 150},
            {"name": "💻 Développeur freelance", "min": 100, "max": 300},
            {"name": "🎨 Graphiste", "min": 80, "max": 200},
            {"name": "🎵 Streamer", "min": 30, "max": 500},
            {"name": "📝 Rédacteur", "min": 60, "max": 180},
            {"name": "🚗 Chauffeur Uber", "min": 70, "max": 150},
        ]
        
        job = random.choice(jobs)
        base_earnings = random.randint(job["min"], job["max"])
        earnings = int(base_earnings * work_multiplier)
        
        users_data[user_id]["pieces"] += earnings
        update_game_stats(user_id, "work_count", 1)
        save_users_data()
        
        if game_stats[user_id]["work_count"] >= 50:
            unlocked, achievement = check_achievement(user_id, "worker", users_data)
            if unlocked:
                save_users_data()
        
        set_cooldown(user_id, "work", now + timedelta(hours=1))
        
        embed = discord.Embed(
            title=job["name"],
            description=f"Tu as travaillé dur et gagné **{earnings} pièces** !",
            color=discord.Color.green()
        )
        
        if work_multiplier != 1.0:
            bonus_amount = earnings - base_earnings
            embed.add_field(
                name=f"{emoji} Bonus {bonus_data['name']}",
                value=f"+{bonus_amount} pièces (x{work_multiplier})",
                inline=False
            )
        
        embed.add_field(name="Nouveau solde", value=f"💰 {users_data[user_id]['pieces']} pièces")
        embed.set_footer(text="Tu pourras retravailler dans 1 heure")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="crime", description="Commets un crime (risqué)")
    async def crime(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        now = datetime.now()
        
        dispo, time_left_s = check_cooldown(user_id, "crime")
        if not dispo:
            minutes = int(time_left_s / 60)
            seconds = int(time_left_s % 60)
            await interaction.response.send_message(
                f"🚔 La police te surveille ! Attends {minutes}m {seconds}s.",
                ephemeral=True
            )
            return
        
        from slots_and_time import get_time_period, get_time_bonus
        period, emoji = get_time_period()
        bonus_data = get_time_bonus(period)
        crime_multiplier = bonus_data["crime_bonus"]
        
        success = random.randint(1, 100) <= 40
        
        crimes = [
            {"name": "🏪 Braquage de magasin", "reward": (200, 500), "penalty": (100, 300)},
            {"name": "💻 Hack de compte", "reward": (300, 600), "penalty": (150, 400)},
            {"name": "🚗 Vol de voiture", "reward": (400, 800), "penalty": (200, 500)},
            {"name": "💎 Vol de bijoux", "reward": (500, 1000), "penalty": (250, 600)},
        ]
        
        crime_chosen = random.choice(crimes)
        
        if success:
            base_earnings = random.randint(*crime_chosen["reward"])
            earnings = int(base_earnings * crime_multiplier)
            users_data[user_id]["pieces"] += earnings
            update_game_stats(user_id, "crime_count", 1)
            save_users_data()
            
            if game_stats[user_id]["crime_count"] >= 20:
                unlocked, achievement = check_achievement(user_id, "criminal", users_data)
                if unlocked:
                    save_users_data()
            
            embed = discord.Embed(
                title=f"✅ {crime_chosen['name']} réussi !",
                description=f"Tu as gagné **{earnings} pièces** !",
                color=discord.Color.green()
            )
            
            if crime_multiplier != 1.0:
                bonus_amount = earnings - base_earnings
                embed.add_field(
                    name=f"{emoji} Bonus {bonus_data['name']}",
                    value=f"+{bonus_amount} pièces (x{crime_multiplier})",
                    inline=False
                )
            
            embed.add_field(name="Nouveau solde", value=f"💰 {users_data[user_id]['pieces']} pièces")
        else:
            penalty = random.randint(*crime_chosen["penalty"])
            users_data[user_id]["pieces"] = max(0, users_data[user_id]["pieces"] - penalty)
            save_users_data()
            
            embed = discord.Embed(
                title=f"🚔 {crime_chosen['name']} raté !",
                description=f"Tu t'es fait prendre ! **-{penalty} pièces**",
                color=discord.Color.red()
            )
            embed.add_field(name="Nouveau solde", value=f"💰 {users_data[user_id]['pieces']} pièces")
        
        set_cooldown(user_id, "crime", now + timedelta(minutes=30))
        embed.set_footer(text="Prochain crime dans 30 minutes")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="braquage", description="Organise un braquage avec des potes")
    @app_commands.describe(complice1="Premier complice", complice2="Deuxième complice (optionnel)")
    async def heist(interaction: discord.Interaction, complice1: discord.Member, complice2: discord.Member = None):
        user_id = str(interaction.user.id)
        now = datetime.now()
        
        dispo, time_left_s = check_cooldown(user_id, "heist")
        if not dispo:
            hours = int(time_left_s / 3600)
            minutes = int((time_left_s % 3600) / 60)
            await interaction.response.send_message(
                f"🏦 Trop risqué ! Attends {hours}h {minutes}m avant un autre braquage.",
                ephemeral=True
            )
            return
        
        complices = [complice1]
        if complice2:
            complices.append(complice2)
        
        for complice in complices:
            if complice.bot:
                await interaction.response.send_message("❌ Les bots ne peuvent pas participer !", ephemeral=True)
                return
            if complice.id == interaction.user.id:
                await interaction.response.send_message("❌ T'as pas besoin de te rajouter toi-même !", ephemeral=True)
                return
        
        # Dédupliquer si même personne mentionnée deux fois
        seen = set()
        complices_uniques = []
        for c in complices:
            if c.id not in seen:
                seen.add(c.id)
                complices_uniques.append(c)
        complices = complices_uniques

        pending = {str(c.id): None for c in complices}  # None = en attente, True = accepté, False = refusé

        complices_mentions = " | ".join([c.mention for c in complices])

        embed = discord.Embed(
            title="🏦 Invitation de braquage",
            description=f"{interaction.user.mention} organise un braquage !\n\nLes complices doivent accepter avant de lancer.",
            color=discord.Color.orange()
        )
        embed.add_field(name="🔍 Complices invités", value=complices_mentions, inline=False)
        embed.add_field(name="⏱️ Délai", value="Vous avez 60 secondes pour accepter", inline=False)

        class HeistInviteView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)

            def get_status_text(self):
                lines = []
                for c in complices:
                    state = pending[str(c.id)]
                    if state is None:
                        lines.append(f"⏳ {c.mention} — en attente")
                    elif state is True:
                        lines.append(f"✅ {c.mention} — accepté")
                    else:
                        lines.append(f"❌ {c.mention} — refusé")
                return "\n".join(lines)

            def all_decided(self):
                return all(v is not None for v in pending.values())

            def all_accepted(self):
                return all(v is True for v in pending.values())

            @discord.ui.button(label="✅ Accepter", style=discord.ButtonStyle.success)
            async def accept(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                cid = str(button_interaction.user.id)
                if cid not in pending:
                    await button_interaction.response.send_message("❌ Tu n'es pas invité dans ce braquage !", ephemeral=True)
                    return
                if pending[cid] is not None:
                    await button_interaction.response.send_message("❌ Tu as déjà répondu !", ephemeral=True)
                    return

                pending[cid] = True

                new_embed = discord.Embed(
                    title="🏦 Invitation de braquage",
                    description=f"{interaction.user.mention} organise un braquage !",
                    color=discord.Color.orange()
                )
                new_embed.add_field(name="📋 Statut", value=self.get_status_text(), inline=False)

                if self.all_decided():
                    if self.all_accepted():
                        new_embed.add_field(name="✅ Tout le monde a accepté !", value="Le braquage se lance...", inline=False)
                        await button_interaction.response.edit_message(embed=new_embed, view=None)
                        await run_heist(interaction, complices)
                    else:
                        new_embed.color = discord.Color.red()
                        new_embed.add_field(name="❌ Braquage annulé", value="Pas tous les complices ont accepté.", inline=False)
                        await button_interaction.response.edit_message(embed=new_embed, view=None)
                else:
                    await button_interaction.response.edit_message(embed=new_embed, view=self)

            @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.danger)
            async def refuse(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                cid = str(button_interaction.user.id)
                if cid not in pending:
                    await button_interaction.response.send_message("❌ Tu n'es pas invité dans ce braquage !", ephemeral=True)
                    return
                if pending[cid] is not None:
                    await button_interaction.response.send_message("❌ Tu as déjà répondu !", ephemeral=True)
                    return

                pending[cid] = False

                new_embed = discord.Embed(
                    title="🏦 Invitation de braquage",
                    description=f"{interaction.user.mention} organise un braquage !",
                    color=discord.Color.red()
                )
                new_embed.add_field(name="📋 Statut", value=self.get_status_text(), inline=False)
                new_embed.add_field(name="❌ Braquage annulé", value=f"{button_interaction.user.mention} a refusé. Le braquage est annulé.", inline=False)
                await button_interaction.response.edit_message(embed=new_embed, view=None)

            async def on_timeout(self):
                if self.all_accepted():
                    return
                timeout_embed = discord.Embed(
                    title="🏦 Invitation de braquage",
                    description=f"{interaction.user.mention} organise un braquage !",
                    color=discord.Color.red()
                )
                timeout_embed.add_field(name="📋 Statut final", value=self.get_status_text(), inline=False)
                timeout_embed.add_field(name="⏰ Temps écoulé", value="Le délai est dépassé. Le braquage est annulé.", inline=False)
                try:
                    await interaction.edit_original_response(embed=timeout_embed, view=None)
                except:
                    pass

        view = HeistInviteView()
        await interaction.response.send_message(embed=embed, view=view)

    async def run_heist(interaction, complices):
        """Lance le braquage une fois tous les complices confirmés"""
        user_id = str(interaction.user.id)

        success = random.randint(1, 100) <= 30
        total_reward = random.randint(2000, 5000)
        total_penalty = random.randint(500, 1500)

        if success:
            share = total_reward // (len(complices) + 1)

            users_data[user_id]["pieces"] += share
            update_game_stats(user_id, "heist_count", 1)

            if game_stats.get(user_id, {}).get("heist_count", 0) >= 10:
                unlocked, achievement = check_achievement(user_id, "heist_master", users_data)
                if unlocked:
                    save_users_data()

            for complice in complices:
                complice_id = str(complice.id)
                if complice_id not in users_data:
                    users_data[complice_id] = {"xp": 0, "niveau": 1, "pieces": 100, "messages": 0, "inventaire": []}
                users_data[complice_id]["pieces"] += share

            save_users_data()

            embed = discord.Embed(
                title="🏦 BRAQUAGE RÉUSSI !",
                description=f"Vous avez braqué la banque et volé **{total_reward} pièces** !",
                color=discord.Color.gold()
            )
            embed.add_field(name="💰 Part de chacun", value=f"{share} pièces", inline=True)
            participants = [interaction.user.mention] + [c.mention for c in complices]
            embed.add_field(name="👥 Participants", value="\n".join(participants), inline=False)
        else:
            users_data[user_id]["pieces"] = max(0, users_data[user_id]["pieces"] - total_penalty)

            for complice in complices:
                complice_id = str(complice.id)
                if complice_id not in users_data:
                    users_data[complice_id] = {"xp": 0, "niveau": 1, "pieces": 100, "messages": 0, "inventaire": []}
                users_data[complice_id]["pieces"] = max(0, users_data[complice_id]["pieces"] - total_penalty)

            save_users_data()

            embed = discord.Embed(
                title="🚔 BRAQUAGE RATÉ !",
                description=f"Vous vous êtes fait prendre ! Chacun perd **{total_penalty} pièces** !",
                color=discord.Color.dark_red()
            )
            participants = [interaction.user.mention] + [c.mention for c in complices]
            embed.add_field(name="👥 Participants", value="\n".join(participants), inline=False)

        set_cooldown(user_id, "heist", datetime.now() + timedelta(hours=2))
        embed.set_footer(text="Prochain braquage dans 2 heures")

        await interaction.followup.send(embed=embed)

# ========== TRADE & DUEL ==========

async def setup_misc_commands(bot, users_data, save_users_data, fun_group):
    @bot.tree.command(name="echanger", description="Échange un objet avec quelqu'un")
    @app_commands.describe(membre="Avec qui échanger", objet="Objet à échanger")
    async def trade(interaction: discord.Interaction, membre: discord.Member, objet: str):
        user_id = str(interaction.user.id)
        target_id = str(membre.id)
        
        if membre.bot:
            await interaction.response.send_message("❌ Tu ne peux pas trader avec un bot !", ephemeral=True)
            return
        
        if user_id == target_id:
            await interaction.response.send_message("❌ Tu ne peux pas trader avec toi-même !", ephemeral=True)
            return
        
        if objet not in users_data[user_id].get("inventaire", []):
            await interaction.response.send_message(f"❌ Tu n'as pas **{objet}** dans ton inventaire !", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🔄 Proposition d'échange",
            description=f"{interaction.user.mention} propose d'échanger **{objet}** avec {membre.mention}",
            color=discord.Color.blue()
        )
        
        class TradeView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
            
            @discord.ui.button(label="✅ Accepter", style=discord.ButtonStyle.success)
            async def accept(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id != membre.id:
                    await button_interaction.response.send_message("❌ Ce n'est pas ton échange !", ephemeral=True)
                    return
                
                users_data[user_id]["inventaire"].remove(objet)
                if target_id not in users_data:
                    users_data[target_id] = {"inventaire": []}
                if "inventaire" not in users_data[target_id]:
                    users_data[target_id]["inventaire"] = []
                users_data[target_id]["inventaire"].append(objet)
                save_users_data()
                
                accept_embed = discord.Embed(
                    title="✅ Échange réussi !",
                    description=f"{membre.mention} a reçu **{objet}** de {interaction.user.mention}",
                    color=discord.Color.green()
                )
                
                await button_interaction.response.edit_message(embed=accept_embed, view=None)
            
            @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.danger)
            async def decline(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id != membre.id:
                    await button_interaction.response.send_message("❌ Ce n'est pas ton échange !", ephemeral=True)
                    return
                
                decline_embed = discord.Embed(
                    title="❌ Échange refusé",
                    description=f"{membre.mention} a refusé l'échange.",
                    color=discord.Color.red()
                )
                
                await button_interaction.response.edit_message(embed=decline_embed, view=None)
        
        view = TradeView()
        await interaction.response.send_message(embed=embed, view=view)
    
    @fun_group.command(name="duel", description="Défie quelqu'un en duel (pierre-papier-ciseaux)")
    @app_commands.describe(adversaire="Qui défier", mise="Coins à miser")
    async def duel(interaction: discord.Interaction, adversaire: discord.Member, mise: int):
        user_id = str(interaction.user.id)
        opponent_id = str(adversaire.id)
        
        if adversaire.bot:
            await interaction.response.send_message("❌ Tu ne peux pas défier un bot !", ephemeral=True)
            return
        
        if user_id == opponent_id:
            await interaction.response.send_message("❌ Tu ne peux pas te défier toi-même !", ephemeral=True)
            return
        
        if mise < 10:
            await interaction.response.send_message("❌ Mise minimum : 10 pièces !", ephemeral=True)
            return
        
        if users_data[user_id]["pieces"] < mise:
            await interaction.response.send_message(f"❌ Tu n'as que {users_data[user_id]['pieces']} pièces !", ephemeral=True)
            return
        
        if users_data[opponent_id]["pieces"] < mise:
            await interaction.response.send_message(f"❌ {adversaire.mention} n'a que {users_data[opponent_id]['pieces']} pièces !", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="⚔️ Défi en duel !",
            description=f"{interaction.user.mention} défie {adversaire.mention} !\n\nMise : **{mise} pièces**\nMode : Pierre-Papier-Ciseaux",
            color=discord.Color.red()
        )
        
        player_choice = None
        opponent_choice = None
        
        class DuelView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
            
            async def check_winner(self, button_interaction):
                nonlocal player_choice, opponent_choice
                
                if player_choice is None or opponent_choice is None:
                    return
                
                choices = {"🪨": "pierre", "📄": "papier", "✂️": "ciseaux"}
                
                p1_choice = choices[player_choice]
                p2_choice = choices[opponent_choice]
                
                if p1_choice == p2_choice:
                    result = "Égalité ! Personne ne perd de pièces."
                    color = discord.Color.gold()
                elif (p1_choice == "pierre" and p2_choice == "ciseaux") or \
                     (p1_choice == "papier" and p2_choice == "pierre") or \
                     (p1_choice == "ciseaux" and p2_choice == "papier"):
                    users_data[user_id]["pieces"] += mise
                    users_data[opponent_id]["pieces"] -= mise
                    result = f"{interaction.user.mention} gagne ! +{mise} pièces"
                    color = discord.Color.green()
                else:
                    users_data[opponent_id]["pieces"] += mise
                    users_data[user_id]["pieces"] -= mise
                    result = f"{adversaire.mention} gagne ! +{mise} pièces"
                    color = discord.Color.red()
                
                save_users_data()
                
                result_embed = discord.Embed(
                    title="⚔️ Résultat du duel",
                    description=f"{interaction.user.mention} : {player_choice}\n{adversaire.mention} : {opponent_choice}\n\n{result}",
                    color=color
                )
                
                # Envoyer le résultat via followup car l'interaction a déjà répondu
                await button_interaction.followup.send(embed=result_embed)
                self.clear_items()
                try:
                    await interaction.edit_original_response(view=self)
                except:
                    pass
            
            @discord.ui.button(label="🪨", style=discord.ButtonStyle.secondary)
            async def rock(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                nonlocal player_choice, opponent_choice
                
                if button_interaction.user.id == interaction.user.id:
                    if player_choice is not None:
                        await button_interaction.response.send_message("❌ Tu as déjà choisi !", ephemeral=True)
                        return
                    player_choice = "🪨"
                    await button_interaction.response.send_message("✅ Tu as choisi Pierre !", ephemeral=True)
                elif button_interaction.user.id == adversaire.id:
                    if opponent_choice is not None:
                        await button_interaction.response.send_message("❌ Tu as déjà choisi !", ephemeral=True)
                        return
                    opponent_choice = "🪨"
                    await button_interaction.response.send_message("✅ Tu as choisi Pierre !", ephemeral=True)
                else:
                    await button_interaction.response.send_message("❌ Ce n'est pas ton duel !", ephemeral=True)
                    return
                
                await self.check_winner(button_interaction)
            
            @discord.ui.button(label="📄", style=discord.ButtonStyle.secondary)
            async def paper(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                nonlocal player_choice, opponent_choice
                
                if button_interaction.user.id == interaction.user.id:
                    if player_choice is not None:
                        await button_interaction.response.send_message("❌ Tu as déjà choisi !", ephemeral=True)
                        return
                    player_choice = "📄"
                    await button_interaction.response.send_message("✅ Tu as choisi Papier !", ephemeral=True)
                elif button_interaction.user.id == adversaire.id:
                    if opponent_choice is not None:
                        await button_interaction.response.send_message("❌ Tu as déjà choisi !", ephemeral=True)
                        return
                    opponent_choice = "📄"
                    await button_interaction.response.send_message("✅ Tu as choisi Papier !", ephemeral=True)
                else:
                    await button_interaction.response.send_message("❌ Ce n'est pas ton duel !", ephemeral=True)
                    return
                
                await self.check_winner(button_interaction)
            
            @discord.ui.button(label="✂️", style=discord.ButtonStyle.secondary)
            async def scissors(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                nonlocal player_choice, opponent_choice
                
                if button_interaction.user.id == interaction.user.id:
                    if player_choice is not None:
                        await button_interaction.response.send_message("❌ Tu as déjà choisi !", ephemeral=True)
                        return
                    player_choice = "✂️"
                    await button_interaction.response.send_message("✅ Tu as choisi Ciseaux !", ephemeral=True)
                elif button_interaction.user.id == adversaire.id:
                    if opponent_choice is not None:
                        await button_interaction.response.send_message("❌ Tu as déjà choisi !", ephemeral=True)
                        return
                    opponent_choice = "✂️"
                    await button_interaction.response.send_message("✅ Tu as choisi Ciseaux !", ephemeral=True)
                else:
                    await button_interaction.response.send_message("❌ Ce n'est pas ton duel !", ephemeral=True)
                    return
                
                await self.check_winner(button_interaction)
        
        view = DuelView()
        await interaction.response.send_message(embed=embed, view=view)