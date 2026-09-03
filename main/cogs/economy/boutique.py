import discord
from discord import app_commands

import core
import items_system
import temp_roles_system
from utils import SPECIAL_ITEMS


def build_shop_embed():
    embed = discord.Embed(
        title="🛒 Boutique du serveur",
        description="Achète des objets avec tes pièces ! Utilise le bouton 🛍️ ci-dessous, ou `/acheter [nom]`.",
        color=discord.Color.green()
    )
    for item_name, item_data in core.shop_items.items():
        item_type = item_data.get("type")
        if item_type == "limited":
            stock = item_data.get("stock", 0)
            stock_text = "🔴 ÉPUISÉ" if stock <= 0 else f"📦 {stock} restant(s)"
            value = f"{item_data['description']}\n💰 Prix : {item_data['prix']} pièces\n{stock_text}"
        elif item_type == "role_temp":
            value = f"{item_data['description']}\n💰 Prix : {item_data['prix']} pièces\n⏳ Rôle temporaire ({item_data.get('duree_heures')}h)"
        else:
            value = f"{item_data['description']}\n💰 Prix : {item_data['prix']} pièces"
        embed.add_field(name=f"💎 {item_name}", value=value, inline=False)
    return embed


async def execute_shop_purchase(interaction: discord.Interaction, item: str):
    """Logique d'achat partagée entre /acheter et le bouton 🛍️ du menu /boutique."""
    user_data = core.get_user_data(interaction.user.id)

    if item not in core.shop_items:
        await interaction.response.send_message("❌ Cet objet n'existe pas dans la boutique !", ephemeral=True)
        return

    item_data = core.shop_items[item]
    item_type = item_data.get("type")

    if item_type == "limited" and item_data.get("stock", 0) <= 0:
        await interaction.response.send_message("❌ Cet objet est épuisé !", ephemeral=True)
        return
    if item_type == "role_temp" and interaction.guild is None:
        await interaction.response.send_message("❌ Cet objet ne peut être acheté que depuis un serveur.", ephemeral=True)
        return
    if user_data["pieces"] < item_data["prix"]:
        await interaction.response.send_message(f"❌ Tu n'as pas assez de pièces ! Il te faut {item_data['prix']} pièces.", ephemeral=True)
        return

    user_data["pieces"] -= item_data["prix"]

    if item_type == "role_temp":
        role_name = item_data.get("role_name", item)
        try:
            expiry = await temp_roles_system.grant_temp_role(interaction.guild, interaction.user, role_name, item_data.get("duree_heures", 24))
        except discord.Forbidden:
            user_data["pieces"] += item_data["prix"]
            core.save_data(core.USERS_FILE, core.users_data)
            await interaction.response.send_message(
                "❌ Le bot n'a pas la permission de gérer ce rôle (vérifie sa position dans la hiérarchie des rôles). Achat annulé, pièces remboursées.",
                ephemeral=True
            )
            return
        core.save_data(core.USERS_FILE, core.users_data)
        embed = discord.Embed(title="✅ Achat réussi !", description=f"Tu as acheté **{item}** pour {item_data['prix']} pièces !", color=discord.Color.green())
        embed.add_field(name="⏳ Rôle actif jusqu'au", value=f"<t:{int(expiry.timestamp())}:F>", inline=False)
        embed.add_field(name="Pièces restantes", value=f"💰 {user_data['pieces']}")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if item_type == "limited":
        item_data["stock"] -= 1
        core.save_data(core.SHOP_FILE, core.shop_items)

    user_data["inventaire"].append(item)
    core.save_data(core.USERS_FILE, core.users_data)

    completed_challenge = core.update_challenge_progress(interaction.user.id, "spent", item_data["prix"])
    if completed_challenge:
        await core.complete_challenge(str(interaction.user.id), completed_challenge, interaction.channel)

    embed = discord.Embed(title="✅ Achat réussi !", description=f"Tu as acheté **{item}** pour {item_data['prix']} pièces !", color=discord.Color.green())
    if item_type == "limited":
        embed.add_field(name="📦 Stock restant", value=str(item_data["stock"]), inline=True)
    embed.add_field(name="Pièces restantes", value=f"💰 {user_data['pieces']}")
    await interaction.response.send_message(embed=embed, ephemeral=True)


class BuySelect(discord.ui.Select):
    def __init__(self):
        options = []
        for name, data in list(core.shop_items.items())[:25]:
            if data.get("type") == "limited" and data.get("stock", 0) <= 0:
                continue
            options.append(discord.SelectOption(label=name[:100], description=f"{data['prix']} pièces"[:100]))
        if not options:
            options.append(discord.SelectOption(label="Boutique vide", description="Rien à acheter pour le moment"))
        super().__init__(placeholder="Choisis un item à acheter...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "Boutique vide":
            await interaction.response.send_message("❌ La boutique est vide.", ephemeral=True)
            return
        await execute_shop_purchase(interaction, self.values[0])


class BuySelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(BuySelect())


class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label="Acheter", style=discord.ButtonStyle.success, emoji="🛍️")
    async def buy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Choisis un item dans la liste :", view=BuySelectView(), ephemeral=True)

    @discord.ui.button(label="Marché entre joueurs", style=discord.ButtonStyle.primary, emoji="🏪")
    async def market_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Que veux-tu faire sur le marché entre joueurs ?", view=items_system.MarketMenuView(), ephemeral=True)

    @discord.ui.button(label="Mon inventaire", style=discord.ButtonStyle.secondary, emoji="🎒")
    async def inventory_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_data = core.get_user_data(interaction.user.id)
        inv = user_data.get("inventaire", [])
        content = ", ".join(inv) if inv else "Ton inventaire est vide."
        await interaction.response.send_message(f"🎒 **Ton inventaire :**\n{content}", ephemeral=True)


async def shop_item_autocomplete(interaction: discord.Interaction, current: str):
    results = []
    for name, data in core.shop_items.items():
        if data.get("type") == "limited" and data.get("stock", 0) <= 0:
            continue
        if current.lower() in name.lower():
            results.append(app_commands.Choice(name=f"{name} ({data['prix']} pièces)"[:100], value=name))
    return results[:25]


async def setup_boutique(bot):

    @bot.tree.command(name="boutique", description="Affiche la boutique (menu à boutons)")
    async def shop(interaction: discord.Interaction):
        await interaction.response.send_message(embed=build_shop_embed(), view=ShopView())

    @bot.tree.command(name="acheter", description="Achète un objet de la boutique")
    @app_commands.describe(item="Le nom de l'objet à acheter")
    @app_commands.autocomplete(item=shop_item_autocomplete)
    async def buy(interaction: discord.Interaction, item: str):
        await execute_shop_purchase(interaction, item)

    @bot.tree.command(name="inventaire", description="Affiche ton inventaire complet")
    async def inventory(interaction: discord.Interaction):
        user_data = core.get_user_data(interaction.user.id)
        user_id = str(interaction.user.id)

        user_special_items = items_system.get_user_items(items_system.items_inventory, user_id)

        has_shop_items = bool(user_data.get("inventaire", []))
        has_special_items = bool(user_special_items)

        if not has_shop_items and not has_special_items:
            await interaction.response.send_message("🎒 Ton inventaire est complètement vide !", ephemeral=True)
            return

        embed = discord.Embed(title=f"🎒 Inventaire de {interaction.user.display_name}", color=discord.Color.purple())

        if has_shop_items:
            shop_items_text = "\n".join([f"• {item}" for item in user_data["inventaire"]])
            embed.add_field(name="🛒 Items Boutique", value=shop_items_text, inline=False)

        if has_special_items:
            total_value = 0
            special_text = ""
            for item in set(user_special_items):
                qty = user_special_items.count(item)
                info = SPECIAL_ITEMS.get(item, {"description": "Item inconnu", "value": 0})
                suffix = f" (x{qty})" if qty > 1 else ""
                special_text += f"{item}{suffix}\n*{info['description']}* — 💎 {info['value']} pièces\n\n"
                total_value += info['value'] * qty

            embed.add_field(name="✨ Items Spéciaux", value=special_text.strip(), inline=False)
            embed.add_field(name="💰 Valeur totale items spéciaux", value=f"{total_value} pièces", inline=False)

        await interaction.response.send_message(embed=embed)
