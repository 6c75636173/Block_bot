import discord
from discord import app_commands
import json
import os
from datetime import datetime, timedelta

BUSINESS_FILE = "bot_data/business_data.json"

BUSINESS_TYPES = {
    "restaurant": {
        "name": "🍕 Pizzeria",
        "price": 5000,
        "income_base": 50,
        "description": "Une petite pizzeria de quartier",
        "max_level": 10,
        "upgrade_cost": lambda lvl: 1000 * lvl,
        "income_multiplier": lambda lvl: 1 + (lvl * 0.2)
    },
    "casino": {
        "name": "🎰 Mini Casino",
        "price": 15000,
        "income_base": 150,
        "description": "Un petit casino avec quelques machines",
        "max_level": 10,
        "upgrade_cost": lambda lvl: 3000 * lvl,
        "income_multiplier": lambda lvl: 1 + (lvl * 0.25)
    },
    "nightclub": {
        "name": "🎵 Boîte de Nuit",
        "price": 25000,
        "income_base": 250,
        "description": "Une boîte de nuit branchée",
        "max_level": 10,
        "upgrade_cost": lambda lvl: 5000 * lvl,
        "income_multiplier": lambda lvl: 1 + (lvl * 0.3)
    },
    "crypto": {
        "name": "💻 Ferme Crypto",
        "price": 50000,
        "income_base": 400,
        "description": "Une ferme de minage de crypto",
        "max_level": 10,
        "upgrade_cost": lambda lvl: 10000 * lvl,
        "income_multiplier": lambda lvl: 1 + (lvl * 0.35)
    },
    "empire": {
        "name": "🏰 Empire Commercial",
        "price": 100000,
        "income_base": 800,
        "description": "Un empire commercial international",
        "max_level": 10,
        "upgrade_cost": lambda lvl: 20000 * lvl,
        "income_multiplier": lambda lvl: 1 + (lvl * 0.4)
    }
}

def load_data(filepath, default=None):
    if default is None:
        default = {}
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_data_to_file(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def calculate_income(business_type, level):
    biz = BUSINESS_TYPES[business_type]
    base = biz["income_base"]
    multiplier = biz["income_multiplier"](level)
    return int(base * multiplier)

def calculate_pending_income(business_data_entry):
    business_type = business_data_entry["type"]
    level = business_data_entry["level"]
    last_claim = datetime.fromisoformat(business_data_entry["last_claim"])
    now = datetime.now()
    hours_passed = (now - last_claim).total_seconds() / 3600
    hours_passed = min(hours_passed, 24)
    income_per_hour = calculate_income(business_type, level)
    return int(income_per_hour * hours_passed), hours_passed

# Chargé au niveau module (comme game_stats dans economy_extensions.py) pour que
# /leaderboard (dans addon_profil.py) puisse lire les données du business sans dupliquer le state.
business_data = load_data(BUSINESS_FILE)

def save_business():
    save_data_to_file(BUSINESS_FILE, business_data)

async def setup_business_system(bot, users_data, save_users_callback):
    
    # ========== /business (UNIFIÉ) ==========
    
    @bot.tree.command(name="entreprise", description="Gérer ton entreprise (boutique + ton entreprise actuelle)")
    async def business(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        if user_id in business_data:
            biz_data = business_data[user_id]
            biz = BUSINESS_TYPES[biz_data["type"]]
            current_income = calculate_income(biz_data["type"], biz_data["level"])
            pending, hours = calculate_pending_income(biz_data)
            
            embed = discord.Embed(
                title=f"💼 {biz['name']}",
                description=biz["description"],
                color=discord.Color.blue()
            )
            embed.add_field(name="📊 Niveau", value=f"{biz_data['level']}/{biz['max_level']}", inline=True)
            embed.add_field(name="💰 Revenu", value=f"{current_income} pièces/h", inline=True)
            embed.add_field(name="💵 Gains en attente", value=f"**{pending} pièces**\n({hours:.1f}h)", inline=False)
            
            embed.set_footer(text="Utilise les boutons ci-dessous pour gérer ton business")
            
            await interaction.response.send_message(embed=embed, view=ManageBusinessView(business_data, users_data, save_business, save_users_callback))
        
        else:
            embed = discord.Embed(
                title="🏪 Boutique de Business",
                description="Achète un business pour générer des revenus passifs !",
                color=discord.Color.gold()
            )
            
            for biz_id, biz in BUSINESS_TYPES.items():
                income = calculate_income(biz_id, 1)
                embed.add_field(
                    name=f"{biz['name']} — {biz['price']} pièces",
                    value=f"{biz['description']}\n💰 {income} pièces/h (lvl 1)",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, view=BuyBusinessView(business_data, users_data, save_business, save_users_callback))
    
    # Le classement business est désormais dans /leaderboard (catégorie "Business"), voir addon_profil.py

# ========== VIEWS ==========

class BuyBusinessView(discord.ui.View):
    def __init__(self, business_data, users_data, save_business, save_users):
        super().__init__(timeout=180)
        self.business_data = business_data
        self.users_data = users_data
        self.save_business = save_business
        self.save_users = save_users
        
        for biz_id, biz in BUSINESS_TYPES.items():
            button = discord.ui.Button(
                label=f"{biz['name'].split()[1]} - {biz['price']}c",
                style=discord.ButtonStyle.primary,
                custom_id=f"buy_{biz_id}"
            )
            button.callback = self.create_buy_callback(biz_id)
            self.add_item(button)
    
    def create_buy_callback(self, biz_id):
        async def callback(interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            biz = BUSINESS_TYPES[biz_id]
            
            if user_id in self.business_data:
                await interaction.response.send_message("❌ Tu as déjà un business !", ephemeral=True)
                return
            
            if self.users_data[user_id]["pieces"] < biz["price"]:
                await interaction.response.send_message(
                    f"❌ Pas assez de pièces ! Il te faut {biz['price']} pièces.",
                    ephemeral=True
                )
                return
            
            self.users_data[user_id]["pieces"] -= biz["price"]
            self.save_users()
            
            self.business_data[user_id] = {
                "type": biz_id,
                "level": 1,
                "last_claim": datetime.now().isoformat()
            }
            self.save_business()
            
            income = calculate_income(biz_id, 1)
            
            embed = discord.Embed(
                title="🎉 Business acheté !",
                description=f"Tu es propriétaire de **{biz['name']}** !",
                color=discord.Color.green()
            )
            embed.add_field(name="💰 Revenu", value=f"{income} pièces/h", inline=True)
            embed.add_field(name="💵 Solde", value=f"{self.users_data[user_id]['pieces']} pièces", inline=True)
            
            await interaction.response.edit_message(embed=embed, view=None)
        
        return callback

class ManageBusinessView(discord.ui.View):
    def __init__(self, business_data, users_data, save_business, save_users):
        super().__init__(timeout=180)
        self.business_data = business_data
        self.users_data = users_data
        self.save_business = save_business
        self.save_users = save_users
    
    @discord.ui.button(label="💵 Réclamer", style=discord.ButtonStyle.success)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        biz_data = self.business_data[user_id]
        pending, hours = calculate_pending_income(biz_data)
        
        if pending == 0:
            await interaction.response.send_message("❌ Aucun revenu à réclamer !", ephemeral=True)
            return
        
        self.users_data[user_id]["pieces"] += pending
        self.save_users()
        self.business_data[user_id]["last_claim"] = datetime.now().isoformat()
        self.save_business()
        
        await interaction.response.send_message(
            f"✅ **+{pending} pièces** récupérés ({hours:.1f}h) !\n💰 Nouveau solde : {self.users_data[user_id]['pieces']} pièces",
            ephemeral=True
        )
    
    @discord.ui.button(label="📈 Améliorer", style=discord.ButtonStyle.primary)
    async def upgrade(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        biz_data = self.business_data[user_id]
        biz = BUSINESS_TYPES[biz_data["type"]]
        
        if biz_data["level"] >= biz["max_level"]:
            await interaction.response.send_message("❌ Niveau max atteint !", ephemeral=True)
            return
        
        upgrade_cost = biz["upgrade_cost"](biz_data["level"])
        
        if self.users_data[user_id]["pieces"] < upgrade_cost:
            await interaction.response.send_message(
                f"❌ Pas assez de pièces ! Il te faut {upgrade_cost} pièces.",
                ephemeral=True
            )
            return
        
        self.users_data[user_id]["pieces"] -= upgrade_cost
        self.save_users()
        self.business_data[user_id]["level"] += 1
        self.save_business()
        
        new_income = calculate_income(biz_data["type"], biz_data["level"])
        
        await interaction.response.send_message(
            f"✅ **{biz['name']}** niveau **{biz_data['level']}** !\n💰 Nouveau revenu : {new_income} pièces/h",
            ephemeral=True
        )
    
    @discord.ui.button(label="💸 Vendre", style=discord.ButtonStyle.danger)
    async def sell(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        biz_data = self.business_data[user_id]
        biz = BUSINESS_TYPES[biz_data["type"]]
        
        total_invested = biz["price"]
        for lvl in range(1, biz_data["level"]):
            total_invested += biz["upgrade_cost"](lvl)
        
        refund = int(total_invested * 0.5)
        pending, _ = calculate_pending_income(biz_data)
        
        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
            
            @discord.ui.button(label="✅ Confirmer", style=discord.ButtonStyle.danger)
            async def confirm(self, btn_interaction: discord.Interaction, btn: discord.ui.Button):
                if str(btn_interaction.user.id) != user_id:
                    await btn_interaction.response.send_message("❌ Pas ton business !", ephemeral=True)
                    return
                
                self.users_data[user_id]["pieces"] += refund + pending
                self.save_users()
                del self.business_data[user_id]
                self.save_business()
                
                await btn_interaction.response.edit_message(
                    content=f"✅ Business vendu ! Tu récupères {refund + pending} pièces.",
                    view=None
                )
            
            @discord.ui.button(label="❌ Annuler", style=discord.ButtonStyle.secondary)
            async def cancel(self, btn_interaction: discord.Interaction, btn: discord.ui.Button):
                await btn_interaction.response.edit_message(content="❌ Vente annulée.", view=None)
        
        await interaction.response.send_message(
            f"⚠️ Vendre **{biz['name']}** ?\nTu récupéreras {refund} pièces (50%) + {pending} pièces en attente.",
            view=ConfirmView(),
            ephemeral=True
        )