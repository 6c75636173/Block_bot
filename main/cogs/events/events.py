import discord
from discord import app_commands
from datetime import datetime

import core
import verification_system
import logs_system


def setup_events(bot):

    @bot.event
    async def on_ready():
        print(f"✅ Bot connecté en tant que {bot.user}")
        await bot.tree.sync()
        print("✅ Commandes slash synchronisées")

        activity = discord.Activity(type=discord.ActivityType.watching, name="le serveur 👀")
        await bot.change_presence(activity=activity)

    @bot.event
    async def on_member_join(member):
        guild_id = str(member.guild.id)

        if guild_id in core.verification_config:
            config = core.verification_config[guild_id]

            if config.get("unverified_role_id"):
                unverified_role = member.guild.get_role(config["unverified_role_id"])
                if unverified_role:
                    try:
                        await member.add_roles(unverified_role)
                        print(f"✅ Rôle non-vérifié ajouté à {member}")
                    except Exception as e:
                        print(f"❌ Erreur ajout rôle non-vérifié: {e}")

            if config.get("channel_id"):
                channel = member.guild.get_channel(config["channel_id"])
                if channel:
                    try:
                        await verification_system.send_verification_message(channel, member, core.verification_config)
                        print(f"✅ Captcha envoyé à {member}")
                    except Exception as e:
                        print(f"❌ Erreur envoi captcha: {e}")

            if config.get("log_channel_id"):
                log_channel = member.guild.get_channel(config["log_channel_id"])
                if log_channel:
                    log_embed = discord.Embed(
                        title="👤 Nouveau membre en attente",
                        description=f"{member.mention} ({member})\nCaptcha envoyé",
                        color=discord.Color.orange(),
                        timestamp=datetime.now()
                    )
                    log_embed.set_thumbnail(url=member.display_avatar.url)
                    await log_channel.send(embed=log_embed)
        else:
            channel = discord.utils.get(member.guild.text_channels, name="bienvenue")
            if channel:
                embed = discord.Embed(
                    title=f"👋 Bienvenue {member.display_name} !",
                    description=f"Tu es le **{member.guild.member_count}ème** membre du serveur !",
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                await channel.send(embed=embed)

        log_embed = discord.Embed(
            title="📥 Membre rejoint",
            description=f"{member.mention} a rejoint le serveur",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        log_embed.set_thumbnail(url=member.display_avatar.url)
        log_embed.add_field(name="👤 Utilisateur", value=f"{member.name} ({member.id})", inline=False)
        log_embed.add_field(name="📅 Compte créé le", value=f"<t:{int(member.created_at.timestamp())}:F>", inline=True)
        log_embed.add_field(name="📊 Membres total", value=f"{member.guild.member_count}", inline=True)
        await logs_system.send_log(member.guild, "member_join", log_embed)

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return

        leveled_up, new_level = core.add_xp(message.author.id)

        if leveled_up:
            rank_name = core.get_rank_name(new_level)
            embed = discord.Embed(
                title="🎉 Level Up !",
                description=f"{message.author.mention} vient d'atteindre le **niveau {new_level}** !\n🏆 Rang : **{rank_name}**\n💰 +50 pièces",
                color=discord.Color.gold()
            )
            await message.channel.send(embed=embed)

            completed_challenge = core.update_challenge_progress(message.author.id, "level_ups", 1)
            if completed_challenge:
                await core.complete_challenge(str(message.author.id), completed_challenge, message.channel)

        completed_challenge = core.update_challenge_progress(message.author.id, "messages", 1)
        if completed_challenge:
            await core.complete_challenge(str(message.author.id), completed_challenge, message.channel)

        await bot.process_commands(message)

    # Gestion d'erreur globale — sans ça, une commande qui plante affiche juste
    # "L'application n'a pas répondu" côté utilisateur, sans explication ni trace exploitable.
    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            message = "❌ Tu n'as pas la permission d'utiliser cette commande."
        elif isinstance(error, app_commands.BotMissingPermissions):
            message = f"❌ Il me manque une permission pour faire ça : `{', '.join(error.missing_permissions)}`."
        elif isinstance(error, app_commands.CommandOnCooldown):
            message = f"⏰ Cette commande est en cooldown, réessaie dans {error.retry_after:.0f}s."
        elif isinstance(error, app_commands.CheckFailure):
            message = "❌ Tu ne peux pas utiliser cette commande ici."
        else:
            message = "❌ Une erreur inattendue est survenue. Les admins ont été notifiés."
            print(f"[ERREUR COMMANDE] /{interaction.command.qualified_name if interaction.command else '?'} — {type(error).__name__}: {error}")
            import traceback
            traceback.print_exception(type(error), error, error.__traceback__)

            try:
                if interaction.guild:
                    log_channel_id = logs_system.get_guild_config(interaction.guild.id).get("channel_id")
                    if log_channel_id:
                        channel = interaction.guild.get_channel(log_channel_id)
                        if channel:
                            embed = discord.Embed(
                                title="🐛 Erreur de commande",
                                description=f"**Commande :** `/{interaction.command.qualified_name if interaction.command else '?'}`\n**Utilisateur :** {interaction.user.mention}",
                                color=discord.Color.dark_red()
                            )
                            embed.add_field(name="Erreur", value=f"```{type(error).__name__}: {str(error)[:900]}```", inline=False)
                            await channel.send(embed=embed)
            except Exception as log_error:
                print(f"[ERREUR] Impossible d'envoyer le log d'erreur : {log_error}")

        try:
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
        except discord.HTTPException:
            pass
