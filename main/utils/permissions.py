"""
utils/permissions.py — Vérification de permissions et confirmations d'actions
destructives, réutilisables par n'importe quel cog (extrait à l'origine de
cogs/admin/admin.py, généralisé pour être utilisable ailleurs aussi).
"""

import discord


def is_admin(interaction: discord.Interaction) -> bool:
    return interaction.guild is not None and interaction.user.guild_permissions.administrator


class ConfirmDangerView(discord.ui.View):
    """Confirmation générique pour une action destructive/irréversible."""
    def __init__(self, author_id: int):
        super().__init__(timeout=30)
        self.author_id = author_id
        self.confirmed = None

    @discord.ui.button(label="✅ Confirmer", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Seul l'auteur de la commande peut confirmer.", ephemeral=True)
            return
        self.confirmed = True
        self.stop()
        await interaction.response.edit_message(content="✅ Confirmé, action en cours...", view=None)

    @discord.ui.button(label="❌ Annuler", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Seul l'auteur de la commande peut annuler.", ephemeral=True)
            return
        self.confirmed = False
        self.stop()
        await interaction.response.edit_message(content="❌ Action annulée.", view=None)


async def ask_confirmation(interaction: discord.Interaction, message: str) -> bool:
    """Affiche un message de confirmation et attend la réponse. Retourne True/False/None (timeout)."""
    view = ConfirmDangerView(interaction.user.id)
    await interaction.response.send_message(message, view=view, ephemeral=True)
    await view.wait()
    return view.confirmed
