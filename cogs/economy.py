import discord
from discord import app_commands

import core


async def setup_economie(bot):

    # ========== COMMANDES ÉCONOMIE ==========
    @bot.tree.command(name="donner", description="Donner des pièces à quelqu'un")
    @app_commands.describe(membre="Le membre à qui donner", montant="Montant à donner", raison="Raison optionnelle (ex: remboursement)")
    async def give(interaction: discord.Interaction, membre: discord.Member, montant: int, raison: str = None):
        if membre.id == interaction.user.id:
            await interaction.response.send_message("❌ Tu ne peux pas te donner des pièces à toi-même !", ephemeral=True)
            return
    
        if membre.bot:
            await interaction.response.send_message("❌ Tu ne peux pas donner des pièces à un bot !", ephemeral=True)
            return
    
        if montant < 10:
            await interaction.response.send_message("❌ Montant minimum : 10 pièces !", ephemeral=True)
            return
    
        giver_data = core.get_user_data(interaction.user.id)
        receiver_data = core.get_user_data(membre.id)
    
        if giver_data["pieces"] < montant:
            await interaction.response.send_message(f"❌ Tu n'as que {giver_data['pieces']} pièces !", ephemeral=True)
            return
    
        giver_data["pieces"] -= montant
        receiver_data["pieces"] += montant
        core.save_data(core.USERS_FILE, core.users_data)
    
        embed = discord.Embed(
            title="💸 Transfert de pièces",
            description=f"{interaction.user.mention} a donné **{montant} pièces** à {membre.mention} !",
            color=discord.Color.green()
        )
        if raison:
            embed.add_field(name="📝 Raison", value=raison, inline=False)
        embed.add_field(name="Nouveau solde", value=f"💰 {giver_data['pieces']} pièces", inline=False)
    
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="pret", description="Prête des pièces avec intérêts (pour le délire)")
    @app_commands.describe(membre="À qui prêter", montant="Montant", interet="% d'intérêt (défaut: 20%)")
    async def loan(interaction: discord.Interaction, membre: discord.Member, montant: int, interet: int = 20):
        if membre.id == interaction.user.id:
            await interaction.response.send_message("❌ Tu ne peux pas te prêter des pièces !", ephemeral=True)
            return
    
        if membre.bot:
            await interaction.response.send_message("❌ Les bots ne font pas de prêts !", ephemeral=True)
            return
    
        if montant < 50:
            await interaction.response.send_message("❌ Montant minimum : 50 pièces !", ephemeral=True)
            return
    
        if interet < 0 or interet > 100:
            await interaction.response.send_message("❌ Les intérêts doivent être entre 0% et 100% !", ephemeral=True)
            return
    
        lender_data = core.get_user_data(interaction.user.id)
        borrower_data = core.get_user_data(membre.id)
    
        if lender_data["pieces"] < montant:
            await interaction.response.send_message(f"❌ Tu n'as que {lender_data['pieces']} pièces !", ephemeral=True)
            return
    
        remboursement = montant + int(montant * (interet / 100))
    
        embed = discord.Embed(
            title="🤝 Proposition de prêt",
            description=f"{interaction.user.mention} propose un prêt à {membre.mention}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Montant", value=f"💰 {montant} pièces", inline=True)
        embed.add_field(name="Intérêts", value=f"📈 {interet}%", inline=True)
        embed.add_field(name="À rembourser", value=f"💸 {remboursement} pièces", inline=True)
        embed.set_footer(text=f"{membre.display_name}, utilise les boutons pour accepter ou refuser. Utilise /give pour rembourser.")
    
        class LoanView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
        
            @discord.ui.button(label="✅ Accepter", style=discord.ButtonStyle.success)
            async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != membre.id:
                    await interaction.response.send_message("❌ Ce n'est pas ton prêt !", ephemeral=True)
                    return
            
                lender_data["pieces"] -= montant
                borrower_data["pieces"] += montant
                core.save_data(core.USERS_FILE, core.users_data)
            
                accept_embed = discord.Embed(
                    title="✅ Prêt accepté !",
                    description=f"{membre.mention} a accepté le prêt de {interaction.user.mention}",
                    color=discord.Color.green()
                )
                accept_embed.add_field(name="Reçu", value=f"💰 {montant} pièces")
                accept_embed.add_field(name="À rembourser", value=f"💸 {remboursement} pièces")
                accept_embed.set_footer(text="N'oublie pas de rembourser avec /give ! (ou pas 😏)")
            
                await interaction.response.edit_message(embed=accept_embed, view=None)
                self.stop()
        
            @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.danger)
            async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != membre.id:
                    await interaction.response.send_message("❌ Ce n'est pas ton prêt !", ephemeral=True)
                    return
            
                decline_embed = discord.Embed(
                    title="❌ Prêt refusé",
                    description=f"{membre.mention} a refusé le prêt",
                    color=discord.Color.red()
                )
            
                await interaction.response.edit_message(embed=decline_embed, view=None)
                self.stop()
    
        view = LoanView()
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await setup_economie(bot)

