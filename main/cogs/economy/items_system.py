import discord
from discord import app_commands
import json
import os
import random
from datetime import datetime, timedelta

from utils import SPECIAL_ITEMS  # source unique — voir utils.py

# ========== FICHIERS ==========

ITEMS_FILE  = "bot_data/items_inventory.json"
MARKET_FILE = "bot_data/market_data.json"
BUFFS_FILE  = "bot_data/buffs_data.json"

# ========== BONUS DE JEU PAR ITEM ==========

ITEM_BUFFS = {
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
    "🎭👑 Masque Royal":      {"type": "all_multiplier",    "value": 1.35, "duration": 90,  "label": "+35% tous les gains"},
}

# ========== RECETTES DE CRAFT ==========

CRAFT_RECIPES = {
    "🌈 Épée Diamantée": {
        "ingredients": ["💎 Diamant Éternel", "⚔️ Épée Légendaire"],
        "description": "Forge une épée avec un diamant → +25% tous les gains 2h"
    },
    "🔥 Orbe Enflammé": {
        "ingredients": ["🔮 Orbe de Cristal", "🌟 Étoile Filante"],
        "description": "Combine deux objets mystiques → x2 gains casino 1h"
    },
    "🎭👑 Masque Royal": {
        "ingredients": ["🎭 Masque Mystérieux", "👑 Couronne Dorée"],
        "description": "Fusionne masque et couronne → +35% tous les gains 1h30"
    },
}

# ========== UTILITAIRES ==========

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

def get_user_items(items_inventory, user_id):
    return items_inventory.get(str(user_id), [])

def has_item(items_inventory, user_id, item_name):
    return item_name in get_user_items(items_inventory, user_id)

def count_item(items_inventory, user_id, item_name):
    """Nombre d'exemplaires de cet item possédés par l'utilisateur (inventaire = liste à plat)."""
    return get_user_items(items_inventory, user_id).count(item_name)


async def inventory_autocomplete(interaction: discord.Interaction, current: str):
    """Autocomplétion sur les items possédés par l'utilisateur (vendre/utiliser/offrir/fusionner)."""
    uid = str(interaction.user.id)
    owned = get_user_items(items_inventory, uid)
    unique_items = sorted(set(owned))
    return [
        app_commands.Choice(name=f"{name} (x{owned.count(name)})"[:100], value=name)
        for name in unique_items if current.lower() in name.lower()
    ][:25]

def remove_item(items_inventory, user_id, item_name):
    uid = str(user_id)
    if uid in items_inventory and item_name in items_inventory[uid]:
        items_inventory[uid].remove(item_name)
        return True
    return False

def add_item(items_inventory, user_id, item_name):
    uid = str(user_id)
    if uid not in items_inventory:
        items_inventory[uid] = []
    items_inventory[uid].append(item_name)

# ========== BUFFS ==========

def get_active_buffs(buffs_data, user_id):
    uid = str(user_id)
    if uid not in buffs_data:
        return []
    now = datetime.now()
    return [b for b in buffs_data[uid] if datetime.fromisoformat(b["expires"]) > now]

def get_multiplier(buffs_data, user_id, buff_type):
    multiplier = 1.0
    for buff in get_active_buffs(buffs_data, user_id):
        if buff["type"] in (buff_type, "all_multiplier"):
            multiplier *= buff["value"]
    return multiplier

def clean_expired_buffs(buffs_data, user_id):
    uid = str(user_id)
    if uid not in buffs_data:
        return
    now = datetime.now()
    buffs_data[uid] = [b for b in buffs_data[uid] if datetime.fromisoformat(b["expires"]) > now]

# Fonction publique pour les autres modules
def get_buff_multiplier(user_id, buff_type):
    buffs_data = load_data(BUFFS_FILE)
    clean_expired_buffs(buffs_data, user_id)
    return get_multiplier(buffs_data, user_id, buff_type)

# ========== ÉTAT PARTAGÉ (niveau module) ==========
# Chargé une fois au niveau module — comme business_data dans business_system.py —
# pour que le menu à boutons de /boutique (dans addon_boutique.py) puisse appeler directement
# la logique du marché sans dépendre des closures de setup_items_system().
items_inventory = load_data(ITEMS_FILE)
market_data     = load_data(MARKET_FILE, {"listings": []})
buffs_data      = load_data(BUFFS_FILE)

def save_items():  save_data_to(ITEMS_FILE,  items_inventory)
def save_market(): save_data_to(MARKET_FILE, market_data)
def save_buffs():  save_data_to(BUFFS_FILE,  buffs_data)

# Références vers users_data/save_users_callback, fixées au moment de setup_items_system().
# Permettent aux fonctions "core" ci-dessous d'être appelées depuis block_bot.py (boutons/modals)
# sans dupliquer users_data.
users_data_ref = None
save_users_ref = None


# ========== LOGIQUE MARCHÉ (réutilisée par les commandes ET le menu à boutons) ==========

async def market_sell_core(interaction: discord.Interaction, item: str, prix: int, quantite: int = 1):
    uid = str(interaction.user.id)
    if prix < 1:
        await interaction.response.send_message("❌ Prix minimum : 1 coin.", ephemeral=True)
        return
    if quantite < 1:
        await interaction.response.send_message("❌ La quantité doit être d'au moins 1.", ephemeral=True)
        return
    owned = count_item(items_inventory, uid, item)
    if owned < quantite:
        await interaction.response.send_message(
            f"❌ Tu ne possèdes que **{owned}x {item}** (tu essaies d'en vendre {quantite}).",
            ephemeral=True)
        return
    
    # Vérifier le nombre d'items différents en vente (max 3)
    user_listings = [l for l in market_data["listings"] if l["seller_id"] == uid]
    unique_items = {l["item"] for l in user_listings}
    
    if item not in unique_items and len(unique_items) >= 3:
        await interaction.response.send_message(
            f"❌ Tu as déjà **3 items différents** en vente ! Annule d'abord une annonce avec `/marche annuler` pour en ajouter une nouvelle.",
            ephemeral=True)
        return
    
    if any(l["seller_id"] == uid and l["item"] == item for l in market_data["listings"]):
        await interaction.response.send_message(
            f"❌ Tu as déjà **{item}** en vente ! Annule d'abord avec `/marche annuler` (ou le bouton ❌ du menu marché) si tu veux changer le prix ou la quantité.",
            ephemeral=True)
        return
    for _ in range(quantite):
        remove_item(items_inventory, uid, item)
    save_items()
    listing_id = max((l["id"] for l in market_data["listings"]), default=0) + 1
    market_data["listings"].append({
        "id": listing_id, "seller_id": uid,
        "seller_name": str(interaction.user),
        "item": item, "price": prix, "quantity": quantite,
        "listed_at": datetime.now().isoformat()
    })
    save_market()
    embed = discord.Embed(
        title="🏪 Item mis en vente !",
        description=f"**{quantite}x {item}** en vente à **{prix} pièces/unité** (total : {prix * quantite} pièces).\n\nID de l'annonce : `#{listing_id}`",
        color=discord.Color.blue())
    embed.add_field(name="💡", value="Retire l'annonce avec `/marche annuler` ou le bouton ❌ du menu marché.", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


def build_market_embed():
    """Retourne l'embed du marché, ou None si vide."""
    listings = market_data.get("listings", [])
    if not listings:
        return None
    embed = discord.Embed(
        title="🏪 Marché des items",
        description="Utilise `/marche acheter [listing_id] [quantite]` ou le bouton 🛒 du menu marché pour acheter !",
        color=discord.Color.blue())
    for l in listings[:10]:
        info = SPECIAL_ITEMS.get(l["item"], {})
        qty = l.get("quantity", 1)
        embed.add_field(
            name=f"#{l['id']} — {l['item']} (x{qty} dispo)",
            value=f"💰 **{l['price']} pièces/unité** | 👤 {l['seller_name']}\n*{info.get('description', '')}*",
            inline=False)
    return embed


async def market_purchase_core(interaction: discord.Interaction, listing_id: int, quantite: int = 1):
    uid = str(interaction.user.id)
    listing = next((l for l in market_data["listings"] if l["id"] == listing_id), None)
    if not listing:
        await interaction.response.send_message("❌ Annonce introuvable.", ephemeral=True)
        return
    if listing["seller_id"] == uid:
        await interaction.response.send_message("❌ Tu ne peux pas acheter ton propre item !", ephemeral=True)
        return
    if quantite < 1:
        await interaction.response.send_message("❌ La quantité doit être d'au moins 1.", ephemeral=True)
        return
    available = listing.get("quantity", 1)
    if quantite > available:
        await interaction.response.send_message(
            f"❌ Il n'y a que **{available}x** disponible sur cette annonce.", ephemeral=True)
        return
    total_price = listing["price"] * quantite
    if users_data_ref[uid]["pieces"] < total_price:
        await interaction.response.send_message(
            f"❌ Pas assez de pièces ! (Tu as {users_data_ref[uid]['pieces']}, il faut {total_price})", ephemeral=True)
        return
    users_data_ref[uid]["pieces"] -= total_price
    net = int(total_price * 0.95)
    sid = listing["seller_id"]
    if sid in users_data_ref:
        users_data_ref[sid]["pieces"] += net
    save_users_ref()
    for _ in range(quantite):
        add_item(items_inventory, uid, listing["item"])
    save_items()

    listing["quantity"] = available - quantite
    if listing["quantity"] <= 0:
        market_data["listings"] = [l for l in market_data["listings"] if l["id"] != listing_id]
    save_market()

    embed = discord.Embed(
        title="✅ Achat réussi !",
        description=f"Tu as acheté **{quantite}x {listing['item']}** pour **{total_price} pièces** !",
        color=discord.Color.green())
    embed.add_field(name="💰 Solde restant", value=f"{users_data_ref[uid]['pieces']} pièces", inline=True)
    embed.add_field(name="ℹ️ Taxe marché",   value="5% prélevé sur la vente",           inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)
    try:
        seller = await interaction.guild.fetch_member(int(sid))
        if seller:
            notif = discord.Embed(
                title="💰 Ton item a été vendu !",
                description=f"**{quantite}x {listing['item']}** vendu pour **{net} pièces** (après taxe 5%).",
                color=discord.Color.gold())
            await seller.send(embed=notif)
    except:
        pass


async def market_cancel_core(interaction: discord.Interaction, listing_id: int):
    uid = str(interaction.user.id)
    listing = next((l for l in market_data["listings"] if l["id"] == listing_id and l["seller_id"] == uid), None)
    if not listing:
        await interaction.response.send_message("❌ Annonce introuvable ou ce n'est pas la tienne.", ephemeral=True)
        return
    market_data["listings"] = [l for l in market_data["listings"] if l["id"] != listing_id]
    save_market()
    qty = listing.get("quantity", 1)
    for _ in range(qty):
        add_item(items_inventory, uid, listing["item"])
    save_items()
    await interaction.response.send_message(
        f"✅ Annonce retirée ! **{qty}x {listing['item']}** {'sont' if qty > 1 else 'est'} de retour dans ton inventaire.", ephemeral=True)


# ========== MODALS & VUE DU MENU MARCHÉ (boutons — voir /boutique dans addon_boutique.py) ==========

class MarketSellModal(discord.ui.Modal, title="Vendre un item"):
    item = discord.ui.TextInput(label="Nom exact de l'item", placeholder="ex: 💎 Diamant Éternel", required=True, max_length=100)
    prix = discord.ui.TextInput(label="Prix par exemplaire (pièces)", placeholder="ex: 250", required=True, max_length=10)
    quantite = discord.ui.TextInput(label="Quantité (défaut : 1)", placeholder="1", required=False, max_length=5)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            prix_val = int(self.prix.value)
            qte_val = int(self.quantite.value) if self.quantite.value.strip() else 1
        except ValueError:
            await interaction.response.send_message("❌ Le prix et la quantité doivent être des nombres entiers.", ephemeral=True)
            return
        await market_sell_core(interaction, self.item.value.strip(), prix_val, qte_val)


class MarketPurchaseModal(discord.ui.Modal, title="Acheter sur le marché"):
    listing_id = discord.ui.TextInput(label="ID de l'annonce (#voir dans Parcourir)", placeholder="ex: 3", required=True, max_length=10)
    quantite = discord.ui.TextInput(label="Quantité (défaut : 1)", placeholder="1", required=False, max_length=5)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            id_val = int(self.listing_id.value)
            qte_val = int(self.quantite.value) if self.quantite.value.strip() else 1
        except ValueError:
            await interaction.response.send_message("❌ L'ID et la quantité doivent être des nombres entiers.", ephemeral=True)
            return
        await market_purchase_core(interaction, id_val, qte_val)


class MarketCancelModal(discord.ui.Modal, title="Annuler une annonce"):
    listing_id = discord.ui.TextInput(label="ID de ton annonce", placeholder="ex: 3", required=True, max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            id_val = int(self.listing_id.value)
        except ValueError:
            await interaction.response.send_message("❌ L'ID doit être un nombre entier.", ephemeral=True)
            return
        await market_cancel_core(interaction, id_val)


class MarketMenuView(discord.ui.View):
    """Sous-menu marché, ouvert depuis le bouton 🏪 Marché de /shop."""
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="👀 Parcourir", style=discord.ButtonStyle.secondary, emoji="🔎")
    async def browse(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = build_market_embed()
        if embed is None:
            await interaction.response.send_message("🏪 Le marché est vide pour l'instant !", ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🛒 Acheter", style=discord.ButtonStyle.success)
    async def purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MarketPurchaseModal())

    @discord.ui.button(label="💰 Vendre", style=discord.ButtonStyle.primary)
    async def sell(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MarketSellModal())

    @discord.ui.button(label="❌ Annuler une annonce", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MarketCancelModal())


# ========== VIEWS (offres/ventes directes existantes) ==========

class ConfirmSellView(discord.ui.View):
    def __init__(self, item, price, user_id, items_inventory, users_data, save_items, save_users):
        super().__init__(timeout=30)
        self.item = item
        self.price = price
        self.user_id = user_id
        self.items_inventory = items_inventory
        self.users_data = users_data
        self.save_items = save_items
        self.save_users = save_users

    @discord.ui.button(label="✅ Confirmer la vente", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Ce n'est pas ton menu !", ephemeral=True)
            return
        remove_item(self.items_inventory, self.user_id, self.item)
        self.save_items()
        self.users_data[self.user_id]["pieces"] += self.price
        self.save_users()
        embed = discord.Embed(
            title="💰 Vendu !",
            description=f"**{self.item}** vendu pour **{self.price} pièces** !",
            color=discord.Color.green()
        )
        embed.add_field(name="💵 Nouveau solde", value=f"{self.users_data[self.user_id]['pieces']} pièces")
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="❌ Annuler", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Ce n'est pas ton menu !", ephemeral=True)
            return
        await interaction.response.edit_message(content="❌ Vente annulée.", embed=None, view=None)


class AcceptOfferView(discord.ui.View):
    def __init__(self, item, price, seller_id, buyer_id, items_inventory, users_data, save_items, save_users):
        super().__init__(timeout=120)
        self.item = item
        self.price = price
        self.seller_id = seller_id
        self.buyer_id = buyer_id
        self.items_inventory = items_inventory
        self.users_data = users_data
        self.save_items = save_items
        self.save_users = save_users

    @discord.ui.button(label="✅ Accepter", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.buyer_id:
            await interaction.response.send_message("❌ Cette offre n'est pas pour toi !", ephemeral=True)
            return
        if self.users_data.get(self.buyer_id, {}).get("pièces", 0) < self.price:
            await interaction.response.send_message("❌ Plus assez de pièces !", ephemeral=True)
            return
        if not has_item(self.items_inventory, self.seller_id, self.item):
            await interaction.response.send_message("❌ Le vendeur n'a plus cet item !", ephemeral=True)
            return
        self.users_data[self.buyer_id]["pieces"] -= self.price
        self.users_data[self.seller_id]["pieces"] += self.price
        self.save_users()
        remove_item(self.items_inventory, self.seller_id, self.item)
        add_item(self.items_inventory, self.buyer_id, self.item)
        self.save_items()
        embed = discord.Embed(
            title="🤝 Échange conclu !",
            description=f"**{self.item}** échangé pour **{self.price} pièces** !",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.danger)
    async def refuse(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.buyer_id:
            await interaction.response.send_message("❌ Cette offre n'est pas pour toi !", ephemeral=True)
            return
        await interaction.response.edit_message(content="❌ Offre refusée.", embed=None, view=None)


# ========== SETUP COMMANDES ==========

async def setup_items_system(bot, users_data, save_users_callback):
    global users_data_ref, save_users_ref
    users_data_ref = users_data
    save_users_ref = save_users_callback

    # ── /item_sell ──────────────────────────────────────────
    @bot.tree.command(name="objet_vendre", description="Vendre un item pour des pièces (80% de sa valeur)")
    @app_commands.describe(item="Nom exact de l'item à vendre")
    @app_commands.autocomplete(item=inventory_autocomplete)
    async def item_sell(interaction: discord.Interaction, item: str):
        uid = str(interaction.user.id)
        if not has_item(items_inventory, uid, item):
            await interaction.response.send_message(
                f"❌ Tu ne possèdes pas **{item}** !\nUtilise `/inventaire` pour voir tes items.", ephemeral=True)
            return
        info = SPECIAL_ITEMS.get(item)
        if not info:
            await interaction.response.send_message("❌ Item inconnu.", ephemeral=True)
            return
        sell_price = int(info["value"] * 0.8)
        view = ConfirmSellView(item, sell_price, uid, items_inventory, users_data, save_items, save_users_callback)
        embed = discord.Embed(title="💰 Confirmer la vente ?",
                              description=f"**{item}**\n{info['description']}",
                              color=discord.Color.orange())
        embed.add_field(name="💵 Prix de vente", value=f"**{sell_price} pièces** (80% valeur)", inline=True)
        embed.add_field(name="💰 Ton solde",     value=f"{users_data[uid]['pieces']} pièces",    inline=True)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # ── /item_fuse ──────────────────────────────────────────
    @bot.tree.command(name="objet_fusionner", description="Fusionner 2 items pour en créer un meilleur")
    @app_commands.describe(item1="Premier item", item2="Deuxième item")
    @app_commands.autocomplete(item1=inventory_autocomplete, item2=inventory_autocomplete)
    async def item_fuse(interaction: discord.Interaction, item1: str, item2: str):
        uid = str(interaction.user.id)
        recipe_result = None
        for result, recipe in CRAFT_RECIPES.items():
            if sorted([item1, item2]) == sorted(recipe["ingredients"]):
                recipe_result = result
                break
        if not recipe_result:
            embed = discord.Embed(title="🔨 Aucune recette trouvée",
                                  description="Ces deux items ne peuvent pas être fusionnés.\n\n**Recettes :**",
                                  color=discord.Color.red())
            for res, rec in CRAFT_RECIPES.items():
                embed.add_field(name=f"→ {res}",
                                value=f"{rec['ingredients'][0]} + {rec['ingredients'][1]}\n*{rec['description']}*",
                                inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        temp_items = list(get_user_items(items_inventory, uid))
        missing = []
        for ing in CRAFT_RECIPES[recipe_result]["ingredients"]:
            if ing in temp_items:
                temp_items.remove(ing)
            else:
                missing.append(ing)
        if missing:
            await interaction.response.send_message(f"❌ Il te manque : **{', '.join(missing)}**", ephemeral=True)
            return
        for ing in CRAFT_RECIPES[recipe_result]["ingredients"]:
            remove_item(items_inventory, uid, ing)
        add_item(items_inventory, uid, recipe_result)
        save_items()
        result_info = SPECIAL_ITEMS.get(recipe_result, {})
        embed = discord.Embed(
            title="✨ Fusion réussie !",
            description=f"**{CRAFT_RECIPES[recipe_result]['ingredients'][0]}** + **{CRAFT_RECIPES[recipe_result]['ingredients'][1]}**\n\n➡️ **{recipe_result}** créé !",
            color=discord.Color.gold())
        embed.add_field(name="📖 Description", value=result_info.get("description", ""), inline=False)
        embed.add_field(name="💎 Valeur",      value=f"{result_info.get('value', 0)} pièces", inline=True)
        if recipe_result in ITEM_BUFFS:
            b = ITEM_BUFFS[recipe_result]
            embed.add_field(name="⚡ Bonus", value=f"{b['label']} ({b['duration']} min)", inline=True)
        await interaction.response.send_message(embed=embed)

    # ── /item_use ───────────────────────────────────────────
    @bot.tree.command(name="objet_utiliser", description="Utiliser un item pour activer son bonus")
    @app_commands.describe(item="Nom exact de l'item à utiliser")
    @app_commands.autocomplete(item=inventory_autocomplete)
    async def item_use(interaction: discord.Interaction, item: str):
        uid = str(interaction.user.id)
        if not has_item(items_inventory, uid, item):
            await interaction.response.send_message(
                f"❌ Tu ne possèdes pas **{item}** !", ephemeral=True)
            return
        if item not in ITEM_BUFFS:
            await interaction.response.send_message(
                f"❌ **{item}** n'a pas de bonus activable.\n"
                f"💡 Tu peux le vendre (`/objet_vendre`) ou le fusionner (`/objet_fusionner`).", ephemeral=True)
            return
        buff_info = ITEM_BUFFS[item]
        remove_item(items_inventory, uid, item)
        save_items()
        expires = datetime.now() + timedelta(minutes=buff_info["duration"])
        if uid not in buffs_data:
            buffs_data[uid] = []
        buffs_data[uid].append({
            "type":    buff_info["type"],
            "value":   buff_info["value"],
            "label":   buff_info["label"],
            "item":    item,
            "expires": expires.isoformat()
        })
        clean_expired_buffs(buffs_data, uid)
        save_buffs()
        embed = discord.Embed(
            title=f"⚡ {item} activé !",
            description=f"**{buff_info['label']}**\npendant **{buff_info['duration']} minutes** !",
            color=discord.Color.green())
        embed.add_field(name="⏰ Expire", value=f"<t:{int(expires.timestamp())}:R>", inline=False)
        await interaction.response.send_message(embed=embed)

    # ── /buffs ──────────────────────────────────────────────
    @bot.tree.command(name="bonus", description="Voir tes bonus actifs")
    async def buffs_cmd(interaction: discord.Interaction):
        uid = str(interaction.user.id)
        clean_expired_buffs(buffs_data, uid)
        save_buffs()
        active = get_active_buffs(buffs_data, uid)
        if not active:
            await interaction.response.send_message("💤 Aucun bonus actif en ce moment.", ephemeral=True)
            return
        embed = discord.Embed(title="⚡ Bonus actifs", color=discord.Color.green())
        for buff in active:
            expires = datetime.fromisoformat(buff["expires"])
            embed.add_field(
                name=f"{buff['item']}",
                value=f"**{buff['label']}**\n⏰ Expire <t:{int(expires.timestamp())}:R>",
                inline=False)
        await interaction.response.send_message(embed=embed)

    # ── /marche (groupe) ────────────────────────────────────
    marche_group = app_commands.Group(name="marche", description="Marché entre joueurs")
    bot.tree.add_command(marche_group)

    @marche_group.command(name="vendre", description="Mettre un item en vente sur le marché")
    @app_commands.describe(item="Nom exact de l'item", prix="Prix par exemplaire, en pièces", quantite="Combien d'exemplaires mettre en vente (défaut : 1)")
    @app_commands.autocomplete(item=inventory_autocomplete)
    async def market_sell(interaction: discord.Interaction, item: str, prix: int, quantite: int = 1):
        await market_sell_core(interaction, item, prix, quantite)

    @marche_group.command(name="acheter", description="Acheter un item sur le marché")
    @app_commands.describe(listing_id="ID de l'annonce (visible dans /marche)", quantite="Combien d'exemplaires acheter (défaut : 1)")
    async def market_purchase(interaction: discord.Interaction, listing_id: int, quantite: int = 1):
        await market_purchase_core(interaction, listing_id, quantite)

    @marche_group.command(name="voir", description="Voir les items en vente sur le marché")
    async def marche_browse(interaction: discord.Interaction):
        embed = build_market_embed()
        if embed is None:
            await interaction.response.send_message("🏪 Le marché est vide pour l'instant !", ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed)

    @marche_group.command(name="annuler", description="Retirer ton item du marché")
    @app_commands.describe(listing_id="ID de ton annonce")
    async def market_cancel(interaction: discord.Interaction, listing_id: int):
        await market_cancel_core(interaction, listing_id)

    # ── /craft ──────────────────────────────────────────────
    @bot.tree.command(name="fabriquer", description="Voir toutes les recettes de fusion")
    async def craft_cmd(interaction: discord.Interaction):
        uid = str(interaction.user.id)
        user_items = get_user_items(items_inventory, uid)
        embed = discord.Embed(
            title="🔨 Recettes de craft",
            description="Utilise `/item_fuse [item1] [item2]` pour fusionner !",
            color=discord.Color.gold())
        for result, recipe in CRAFT_RECIPES.items():
            ing1, ing2 = recipe["ingredients"]
            h1 = "✅" if ing1 in user_items else "❌"
            h2 = "✅" if ing2 in user_items else "❌"
            result_info = SPECIAL_ITEMS.get(result, {})
            buff = ITEM_BUFFS.get(result)
            buff_text = f"\n⚡ *{buff['label']} ({buff['duration']} min)*" if buff else ""
            embed.add_field(
                name=f"→ {result}",
                value=(f"{h1} {ing1}\n{h2} {ing2}\n"
                       f"💎 Valeur : {result_info.get('value', 0)} pièces{buff_text}"),
                inline=False)
        await interaction.response.send_message(embed=embed)
