import discord
from discord import app_commands

import core
from utils import ConfirmDangerView, ask_confirmation, is_admin


async def setup_admin(bot):

    # ========== GROUPE /admin (économie + boutique) ==========

    # ========== /admin — PANNEAU À BOUTONS (une seule ligne dans le "/", tout le reste en menus) ==========


    # ---------- Logique métier (ex-sous-commandes, maintenant de simples fonctions) ----------

    async def do_argent_ajouter(interaction: discord.Interaction, membre: discord.Member, montant: int):
        if montant <= 0:
            await interaction.response.send_message("❌ Le montant doit être positif !", ephemeral=True)
            return
        target_data = core.get_user_data(membre.id)
        avant = target_data["pieces"]
        target_data["pieces"] += montant
        core.save_data(core.USERS_FILE, core.users_data)
        embed = discord.Embed(title="✅ Pièces ajoutées", description=f"**{montant} pièces** ont été ajoutées à {membre.mention}", color=discord.Color.green())
        embed.add_field(name="Avant", value=f"💰 {avant} pièces", inline=True)
        embed.add_field(name="Après", value=f"💰 {target_data['pieces']} pièces", inline=True)
        embed.add_field(name="Par", value=interaction.user.mention, inline=True)
        await interaction.response.send_message(embed=embed)


    async def do_argent_retirer(interaction: discord.Interaction, membre: discord.Member, montant: int):
        if montant <= 0:
            await interaction.response.send_message("❌ Le montant doit être positif !", ephemeral=True)
            return
        target_data = core.get_user_data(membre.id)
        avant = target_data["pieces"]
        if montant > target_data["pieces"]:
            await interaction.response.send_message(f"❌ {membre.mention} n'a que **{target_data['pieces']} pièces**. Tu ne peux pas en retirer {montant}.", ephemeral=True)
            return
        confirmed = await ask_confirmation(interaction, f"⚠️ Retirer **{montant} pièces** à {membre.mention} (solde actuel : {avant}) ?")
        if not confirmed:
            return
        target_data["pieces"] -= montant
        core.save_data(core.USERS_FILE, core.users_data)
        embed = discord.Embed(title="✅ Pièces retirées", description=f"**{montant} pièces** ont été retirées de {membre.mention}", color=discord.Color.red())
        embed.add_field(name="Avant", value=f"💰 {avant} pièces", inline=True)
        embed.add_field(name="Après", value=f"💰 {target_data['pieces']} pièces", inline=True)
        embed.add_field(name="Par", value=interaction.user.mention, inline=True)
        await interaction.followup.send(embed=embed)


    async def do_argent_definir(interaction: discord.Interaction, membre: discord.Member, montant: int):
        if montant < 0:
            await interaction.response.send_message("❌ Le solde ne peut pas être négatif !", ephemeral=True)
            return
        target_data = core.get_user_data(membre.id)
        avant = target_data["pieces"]
        confirmed = await ask_confirmation(interaction, f"⚠️ Définir le solde de {membre.mention} à **{montant} pièces** (actuellement : {avant}) ?")
        if not confirmed:
            return
        target_data["pieces"] = montant
        core.save_data(core.USERS_FILE, core.users_data)
        embed = discord.Embed(title="✅ Solde défini", description=f"Le solde de {membre.mention} a été mis à jour", color=discord.Color.blue())
        embed.add_field(name="Avant", value=f"💰 {avant} pièces", inline=True)
        embed.add_field(name="Après", value=f"💰 {montant} pièces", inline=True)
        embed.add_field(name="Par", value=interaction.user.mention, inline=True)
        await interaction.followup.send(embed=embed)


    async def do_argent_reinitialiser(interaction: discord.Interaction, membre: discord.Member, montant=None):
        target_data = core.get_user_data(membre.id)
        avant = target_data["pieces"]
        confirmed = await ask_confirmation(interaction, f"⚠️ Remettre le solde de {membre.mention} à **0** (actuellement : {avant} pièces) ?")
        if not confirmed:
            return
        target_data["pieces"] = 0
        core.save_data(core.USERS_FILE, core.users_data)
        embed = discord.Embed(title="✅ Pièces réinitialisées", description=f"Le solde de {membre.mention} a été remis à **0 pièces**", color=discord.Color.orange())
        embed.add_field(name="Avant", value=f"💰 {avant} pièces", inline=True)
        embed.add_field(name="Après", value=f"💰 0 pièces", inline=True)
        embed.add_field(name="Par", value=interaction.user.mention, inline=True)
        await interaction.followup.send(embed=embed)


    async def do_xp_ajouter(interaction: discord.Interaction, membre: discord.Member, montant: int):
        if montant <= 0:
            await interaction.response.send_message("❌ Le montant doit être positif !", ephemeral=True)
            return
        target_data = core.get_user_data(membre.id)
        avant_xp = target_data["xp"]
        avant_niveau = target_data["niveau"]
        target_data["xp"] += montant
        while target_data["xp"] >= target_data["niveau"] * 100:
            target_data["niveau"] += 1
            target_data["pieces"] += 50
        core.save_data(core.USERS_FILE, core.users_data)
        embed = discord.Embed(title="✅ XP ajouté", description=f"**{montant} XP** ont été ajoutés à {membre.mention}", color=discord.Color.green())
        embed.add_field(name="XP : Avant → Après", value=f"⭐ {avant_xp} → {target_data['xp']}", inline=False)
        if target_data["niveau"] != avant_niveau:
            embed.add_field(name="🎉 Level Up !", value=f"Niveau {avant_niveau} → **{target_data['niveau']}**", inline=False)
        embed.add_field(name="Par", value=interaction.user.mention, inline=True)
        await interaction.response.send_message(embed=embed)


    async def do_stats_economie(interaction: discord.Interaction):
        if not core.users_data:
            await interaction.response.send_message("❌ Aucune donnée utilisateur pour l'instant.", ephemeral=True)
            return
        balances = [(uid, ud.get("pieces", 0)) for uid, ud in core.users_data.items()]
        total = sum(b for _, b in balances)
        moyenne = total / len(balances)
        sorted_balances = sorted(balances, key=lambda x: x[1], reverse=True)
        valeurs_triees = sorted(b for _, b in balances)
        n = len(valeurs_triees)
        mediane = valeurs_triees[n // 2] if n % 2 == 1 else (valeurs_triees[n // 2 - 1] + valeurs_triees[n // 2]) / 2
        seuil_anomalie = max(mediane * 20, 10000)
        anomalies = [(uid, bal) for uid, bal in balances if bal > seuil_anomalie]

        embed = discord.Embed(title="📊 Économie du serveur", color=discord.Color.blue())
        embed.add_field(name="👥 Joueurs", value=f"{len(balances)}", inline=True)
        embed.add_field(name="💰 Total en circulation", value=f"{total:,} pièces".replace(",", " "), inline=True)
        embed.add_field(name="📈 Moyenne", value=f"{moyenne:,.0f} pièces".replace(",", " "), inline=True)

        top_text = ""
        for i, (uid, bal) in enumerate(sorted_balances[:5], 1):
            try:
                user = await core.get_display_user(interaction, int(uid))
                name = user.display_name if hasattr(user, "display_name") else user.name
            except:
                name = f"ID {uid}"
            top_text += f"{i}. {name} — {bal:,} pièces\n".replace(",", " ")
        embed.add_field(name="🏆 Top 5 soldes", value=top_text or "—", inline=False)

        if anomalies:
            anomalies_text = ""
            for uid, bal in sorted(anomalies, key=lambda x: x[1], reverse=True)[:5]:
                anomalies_text += f"⚠️ ID `{uid}` — {bal:,} pièces (x{bal/mediane:.0f} la médiane)\n".replace(",", " ")
            embed.add_field(name="🚨 Soldes anormaux détectés", value=anomalies_text + "\nProbablement dû à un ajout de pièces mal utilisé. Corrige via le panneau 💰 Pièces → Définir si besoin.", inline=False)
        else:
            embed.add_field(name="✅ Anomalies", value="Aucun solde anormalement élevé détecté.", inline=False)

        await interaction.response.send_message(embed=embed)


    async def do_voir(interaction: discord.Interaction, membre: discord.Member, montant=None):
        target_data = core.get_user_data(membre.id)
        rank_name = core.get_rank_name(target_data["niveau"])
        embed = discord.Embed(title=f"🔍 Données de {membre.display_name}", color=discord.Color.blue())
        embed.set_thumbnail(url=membre.display_avatar.url)
        embed.add_field(name="💰 Pièces", value=f"{target_data['pieces']}", inline=True)
        embed.add_field(name="⭐ XP", value=f"{target_data['xp']}", inline=True)
        embed.add_field(name="📊 Niveau", value=f"{target_data['niveau']} — {rank_name}", inline=True)
        embed.add_field(name="💬 Messages", value=f"{target_data.get('messages', 0)}", inline=True)
        embed.add_field(name="🎒 Inventaire", value=", ".join(target_data.get("inventaire", [])) or "Vide", inline=False)
        await interaction.response.send_message(embed=embed)


    async def do_boutique_role(interaction: discord.Interaction, nom: str, prix: int, role_name: str, duree_heures: float, description: str):
        core.shop_items[nom] = {"prix": prix, "description": description, "type": "role_temp", "role_name": role_name, "duree_heures": duree_heures}
        core.save_data(core.SHOP_FILE, core.shop_items)
        await interaction.response.send_message(f"✅ Item **{nom}** ajouté à la boutique : rôle `{role_name}` pendant {duree_heures}h, {prix} pièces.", ephemeral=True)


    async def do_boutique_stock(interaction: discord.Interaction, nom: str, prix: int, stock: int, description: str):
        if stock < 1:
            await interaction.response.send_message("❌ Le stock doit être d'au moins 1.", ephemeral=True)
            return
        core.shop_items[nom] = {"prix": prix, "description": description, "type": "limited", "stock": stock, "stock_total": stock}
        core.save_data(core.SHOP_FILE, core.shop_items)
        await interaction.response.send_message(f"✅ Item **{nom}** ajouté à la boutique : {stock}x disponibles, {prix} pièces chacun.", ephemeral=True)


    async def do_boutique_retirer(interaction: discord.Interaction, nom: str):
        if nom not in core.shop_items:
            await interaction.response.send_message("❌ Cet item n'existe pas dans la boutique.", ephemeral=True)
            return
        confirmed = await ask_confirmation(interaction, f"⚠️ Retirer définitivement **{nom}** de la boutique ?")
        if not confirmed:
            return
        del core.shop_items[nom]
        core.save_data(core.SHOP_FILE, core.shop_items)
        await interaction.followup.send(f"✅ **{nom}** retiré de la boutique.")


    # ---------- Composants d'interface (boutons, sélecteurs, formulaires) ----------

    class AmountModal(discord.ui.Modal):
        """Étape 2 d'un flux 'choisir un membre puis un montant' : demande le montant."""
        def __init__(self, title: str, membre: discord.Member, callback):
            super().__init__(title=title[:45])
            self.membre = membre
            self.callback = callback
            self.montant_input = discord.ui.TextInput(label="Montant", placeholder="ex: 500", required=True, max_length=15)
            self.add_item(self.montant_input)

        async def on_submit(self, interaction: discord.Interaction):
            try:
                montant = int(self.montant_input.value)
            except ValueError:
                await interaction.response.send_message("❌ Le montant doit être un nombre entier.", ephemeral=True)
                return
            await self.callback(interaction, self.membre, montant)


    class MemberSelectView(discord.ui.View):
        """Étape 1 : choisir un membre via un menu déroulant Discord natif."""
        def __init__(self, action_title: str, callback, needs_amount: bool = True):
            super().__init__(timeout=60)
            self.action_title = action_title
            self.callback = callback
            self.needs_amount = needs_amount

        @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Choisis un membre...")
        async def select_member(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
            membre = select.values[0]
            if not isinstance(membre, discord.Member):
                # Peut arriver si l'utilisateur sélectionné a quitté le serveur entre-temps
                await interaction.response.send_message("❌ Ce membre n'est plus sur le serveur.", ephemeral=True)
                return
            if self.needs_amount:
                await interaction.response.send_modal(AmountModal(self.action_title, membre, self.callback))
            else:
                await self.callback(interaction, membre)


    class BoutiqueRoleModal(discord.ui.Modal, title="Ajouter un rôle temporaire"):
        nom = discord.ui.TextInput(label="Nom de l'item dans la boutique", max_length=100)
        prix = discord.ui.TextInput(label="Prix (pièces)", placeholder="ex: 5000", max_length=15)
        role_name = discord.ui.TextInput(label="Nom exact du rôle Discord", max_length=100)
        duree_heures = discord.ui.TextInput(label="Durée d'attribution (heures)", placeholder="ex: 48", max_length=10)
        description = discord.ui.TextInput(label="Description (optionnel)", required=False, max_length=200)

        async def on_submit(self, interaction: discord.Interaction):
            try:
                prix_val = int(self.prix.value)
                duree_val = float(self.duree_heures.value)
            except ValueError:
                await interaction.response.send_message("❌ Prix et durée doivent être des nombres.", ephemeral=True)
                return
            await do_boutique_role(interaction, self.nom.value, prix_val, self.role_name.value, duree_val, self.description.value or "Rôle temporaire")


    class BoutiqueStockModal(discord.ui.Modal, title="Ajouter un item à stock limité"):
        nom = discord.ui.TextInput(label="Nom de l'item dans la boutique", max_length=100)
        prix = discord.ui.TextInput(label="Prix (pièces)", placeholder="ex: 100", max_length=15)
        stock = discord.ui.TextInput(label="Stock total disponible", placeholder="ex: 100", max_length=10)
        description = discord.ui.TextInput(label="Description (optionnel)", required=False, max_length=200)

        async def on_submit(self, interaction: discord.Interaction):
            try:
                prix_val = int(self.prix.value)
                stock_val = int(self.stock.value)
            except ValueError:
                await interaction.response.send_message("❌ Prix et stock doivent être des nombres entiers.", ephemeral=True)
                return
            await do_boutique_stock(interaction, self.nom.value, prix_val, stock_val, self.description.value or "Item en édition limitée")


    class BoutiqueRetirerModal(discord.ui.Modal, title="Retirer un item de la boutique"):
        nom = discord.ui.TextInput(label="Nom exact de l'item à retirer", max_length=100)

        async def on_submit(self, interaction: discord.Interaction):
            await do_boutique_retirer(interaction, self.nom.value)


    class AdminPiecesMenuView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=120)

        @discord.ui.button(label="Ajouter", style=discord.ButtonStyle.success, emoji="➕")
        async def ajouter(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message("Choisis un membre :", view=MemberSelectView("Ajouter des pièces", do_argent_ajouter), ephemeral=True)

        @discord.ui.button(label="Retirer", style=discord.ButtonStyle.danger, emoji="➖")
        async def retirer(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message("Choisis un membre :", view=MemberSelectView("Retirer des pièces", do_argent_retirer), ephemeral=True)

        @discord.ui.button(label="Définir", style=discord.ButtonStyle.primary, emoji="✏️")
        async def definir(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message("Choisis un membre :", view=MemberSelectView("Définir le solde", do_argent_definir), ephemeral=True)

        @discord.ui.button(label="Réinitialiser", style=discord.ButtonStyle.secondary, emoji="🔄")
        async def reinitialiser(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message("Choisis un membre :", view=MemberSelectView("Réinitialiser", do_argent_reinitialiser, needs_amount=False), ephemeral=True)


    class AdminBoutiqueMenuView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=120)

        @discord.ui.button(label="Rôle temporaire", style=discord.ButtonStyle.success, emoji="⏳")
        async def role(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(BoutiqueRoleModal())

        @discord.ui.button(label="Stock limité", style=discord.ButtonStyle.primary, emoji="📦")
        async def stock(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(BoutiqueStockModal())

        @discord.ui.button(label="Retirer un item", style=discord.ButtonStyle.danger, emoji="🗑️")
        async def retirer(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(BoutiqueRetirerModal())


    class AdminPanelView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=180)

        @discord.ui.button(label="Pièces", style=discord.ButtonStyle.success, emoji="💰")
        async def pieces_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message("Que veux-tu faire ?", view=AdminPiecesMenuView(), ephemeral=True)

        @discord.ui.button(label="XP", style=discord.ButtonStyle.primary, emoji="⭐")
        async def xp_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message("Choisis un membre :", view=MemberSelectView("Ajouter de l'XP", do_xp_ajouter), ephemeral=True)

        @discord.ui.button(label="Voir un membre", style=discord.ButtonStyle.secondary, emoji="🔍")
        async def voir_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message("Choisis un membre :", view=MemberSelectView("Voir", do_voir, needs_amount=False), ephemeral=True)

        @discord.ui.button(label="Stats économie", style=discord.ButtonStyle.secondary, emoji="📊")
        async def stats_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            await do_stats_economie(interaction)

        @discord.ui.button(label="Boutique", style=discord.ButtonStyle.danger, emoji="🛍️")
        async def boutique_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message("Gérer la boutique :", view=AdminBoutiqueMenuView(), ephemeral=True)


    @bot.tree.command(name="admin", description="[ADMIN] Panneau de gestion économie et boutique")
    async def admin(interaction: discord.Interaction):
        if not is_admin(interaction):
            await interaction.response.send_message("❌ Cette commande est réservée aux administrateurs.", ephemeral=True)
            return
        embed = discord.Embed(
            title="⚙️ Panneau Admin",
            description="Choisis une catégorie ci-dessous.",
            color=discord.Color.dark_blue()
        )
        await interaction.response.send_message(embed=embed, view=AdminPanelView(), ephemeral=True)

