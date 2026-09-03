import discord
from discord import app_commands
from datetime import datetime, timedelta

import core


async def setup_moderation(bot):

    @bot.tree.command(name="avertir", description="Avertir un membre")
    @app_commands.describe(membre="Le membre à avertir", raison="La raison de l'avertissement")
    @app_commands.default_permissions(moderate_members=True)
    async def warn(interaction: discord.Interaction, membre: discord.Member, raison: str):
        if membre.bot:
            await interaction.response.send_message("❌ Je ne peux pas avertir un bot !", ephemeral=True)
            return

        user_id = str(membre.id)
        if user_id not in core.warnings_data:
            core.warnings_data[user_id] = []

        warning = {"raison": raison, "date": datetime.now().isoformat(), "moderateur": str(interaction.user.id)}
        core.warnings_data[user_id].append(warning)
        core.save_data(core.WARNINGS_FILE, core.warnings_data)

        embed = discord.Embed(title="⚠️ Avertissement", description=f"{membre.mention} a reçu un avertissement", color=discord.Color.orange())
        embed.add_field(name="Raison", value=raison)
        embed.add_field(name="Modérateur", value=interaction.user.mention)
        embed.add_field(name="Total d'avertissements", value=f"{len(core.warnings_data[user_id])}")

        await interaction.response.send_message(embed=embed)
        try:
            await membre.send(f"⚠️ Tu as reçu un avertissement sur **{interaction.guild.name}**\n**Raison :** {raison}")
        except:
            pass

    @bot.tree.command(name="avertissements", description="Affiche les avertissements d'un membre")
    @app_commands.describe(membre="Le membre à vérifier")
    async def warnings(interaction: discord.Interaction, membre: discord.Member):
        user_id = str(membre.id)
        if user_id not in core.warnings_data or not core.warnings_data[user_id]:
            await interaction.response.send_message(f"✅ {membre.mention} n'a aucun avertissement !", ephemeral=True)
            return

        all_warns = core.warnings_data[user_id]
        embed = discord.Embed(
            title=f"⚠️ Avertissements de {membre.display_name}",
            description=f"Total : {len(all_warns)} avertissement(s)",
            color=discord.Color.orange()
        )
        # Numéros stables (pas relatifs à l'affichage) pour pouvoir cibler /effacer_avertissements [numero]
        start_index = max(0, len(all_warns) - 10)
        for i, warn_entry in enumerate(all_warns[start_index:], start=start_index + 1):
            mod = await core.get_display_user(interaction, int(warn_entry["moderateur"]))
            date = datetime.fromisoformat(warn_entry["date"]).strftime("%d/%m/%Y")
            embed.add_field(name=f"Avertissement #{i}", value=f"**Raison :** {warn_entry['raison']}\n**Par :** {mod.mention}\n**Date :** {date}", inline=False)
        if start_index > 0:
            embed.set_footer(text=f"{start_index} avertissement(s) plus ancien(s) non affiché(s)")

        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="effacer_avertissements", description="Efface les avertissements d'un membre (tous, ou un seul par son numéro)")
    @app_commands.describe(membre="Le membre concerné", numero="Numéro de l'avertissement à effacer (voir /avertissements) — laisse vide pour tout effacer")
    @app_commands.default_permissions(administrator=True)
    async def clearwarns(interaction: discord.Interaction, membre: discord.Member, numero: int = None):
        user_id = str(membre.id)
        if user_id not in core.warnings_data or not core.warnings_data[user_id]:
            await interaction.response.send_message(f"✅ {membre.mention} n'a aucun avertissement !", ephemeral=True)
            return

        if numero is not None:
            idx = numero - 1
            if idx < 0 or idx >= len(core.warnings_data[user_id]):
                await interaction.response.send_message(
                    f"❌ Numéro invalide. {membre.mention} a {len(core.warnings_data[user_id])} avertissement(s) (utilise /avertissements pour voir les numéros).",
                    ephemeral=True
                )
                return
            removed = core.warnings_data[user_id].pop(idx)
            core.save_data(core.WARNINGS_FILE, core.warnings_data)
            await interaction.response.send_message(f"✅ Avertissement #{numero} de {membre.mention} effacé (raison : {removed['raison']}).")
        else:
            core.warnings_data[user_id] = []
            core.save_data(core.WARNINGS_FILE, core.warnings_data)
            await interaction.response.send_message(f"✅ Tous les avertissements de {membre.mention} ont été effacés !")

    @bot.tree.command(name="expulser", description="Expulse un membre")
    @app_commands.describe(membre="Le membre à expulser", raison="La raison de l'expulsion")
    @app_commands.default_permissions(kick_members=True)
    async def kick(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison"):
        if membre.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ Tu ne peux pas expulser ce membre !", ephemeral=True)
            return
        try:
            await membre.send(f"👢 Tu as été expulsé de **{interaction.guild.name}**\n**Raison :** {raison}")
        except:
            pass
        await membre.kick(reason=raison)

        embed = discord.Embed(title="👢 Membre expulsé", description=f"{membre.mention} a été expulsé", color=discord.Color.red())
        embed.add_field(name="Raison", value=raison)
        embed.add_field(name="Modérateur", value=interaction.user.mention)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="bannir", description="Banni un membre")
    @app_commands.describe(membre="Le membre à bannir", raison="La raison du bannissement")
    @app_commands.default_permissions(ban_members=True)
    async def ban(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison"):
        if membre.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ Tu ne peux pas bannir ce membre !", ephemeral=True)
            return
        try:
            await membre.send(f"🔨 Tu as été banni de **{interaction.guild.name}**\n**Raison :** {raison}")
        except:
            pass
        await membre.ban(reason=raison)

        embed = discord.Embed(title="🔨 Membre banni", description=f"{membre.mention} a été banni", color=discord.Color.dark_red())
        embed.add_field(name="Raison", value=raison)
        embed.add_field(name="Modérateur", value=interaction.user.mention)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="nettoyer", description="Supprime des messages (de tout le monde, ou d'un membre précis)")
    @app_commands.describe(nombre="Nombre de messages à supprimer (max 100)", membre="Ne supprimer que les messages de ce membre (optionnel)")
    @app_commands.default_permissions(manage_messages=True)
    async def clear(interaction: discord.Interaction, nombre: int, membre: discord.Member = None):
        if nombre < 1 or nombre > 100:
            await interaction.response.send_message("❌ Le nombre doit être entre 1 et 100 !", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        if membre is not None:
            # purge() avec un check ne s'arrête pas après N suppressions — il supprime TOUS les
            # messages correspondants trouvés dans la limite de scan. On collecte donc nous-mêmes
            # exactement "nombre" messages du membre avant de les supprimer, pour ne jamais en
            # supprimer plus que demandé.
            messages_a_supprimer = []
            async for msg in interaction.channel.history(limit=1000):
                if msg.author.id == membre.id:
                    messages_a_supprimer.append(msg)
                    if len(messages_a_supprimer) >= nombre:
                        break
            if messages_a_supprimer:
                await interaction.channel.delete_messages(messages_a_supprimer)
            await interaction.followup.send(f"✅ {len(messages_a_supprimer)} message(s) de {membre.mention} supprimé(s) !", ephemeral=True)
        else:
            deleted = await interaction.channel.purge(limit=nombre)
            await interaction.followup.send(f"✅ {len(deleted)} message(s) supprimé(s) !", ephemeral=True)
