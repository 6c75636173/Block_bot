import discord
from discord import app_commands

import core


async def setup_economie(bot):

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

