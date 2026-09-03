import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

LOGS_CONFIG_FILE = "bot_data/logs_config.json"

DEFAULT_CONFIG = {
    "enabled": False,
    "channel_id": None,
    "events": {
        "member_join": True,
        "member_leave": True,
        "member_kick": True,
        "member_ban": True,
        "member_unban": True,
        "member_voice_move": True,
        "member_voice_kick": True,
        "member_nickname_change": True,
        "member_roles_update": True,
        "member_timeout": True,
        "member_untimeout": True,
        "message_delete": True,
        "message_bulk_delete": True,
        "message_edit": True,
        "channel_create": True,
        "channel_delete": True,
        "channel_update": True,
        "role_create": True,
        "role_delete": True,
        "role_update": True,
        "invite_create": True,
        "invite_delete": True
    }
}

def load_logs_config():
    """Charger la configuration des logs"""
    if os.path.exists(LOGS_CONFIG_FILE):
        with open(LOGS_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_logs_config(config):
    """Sauvegarder la configuration des logs"""
    os.makedirs(os.path.dirname(LOGS_CONFIG_FILE), exist_ok=True)
    with open(LOGS_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def get_guild_config(guild_id):
    """Obtenir la config d'un serveur spécifique"""
    config = load_logs_config()
    guild_id = str(guild_id)
    if guild_id not in config:
        config[guild_id] = DEFAULT_CONFIG.copy()
        config[guild_id]["events"] = DEFAULT_CONFIG["events"].copy()
        save_logs_config(config)
    return config[guild_id]

def set_guild_config(guild_id, new_config):
    """Mettre à jour la config d'un serveur"""
    config = load_logs_config()
    config[str(guild_id)] = new_config
    save_logs_config(config)

async def send_log(guild, event_name, embed):
    """Envoyer un log si activé"""
    guild_config = get_guild_config(guild.id)
    
    if not guild_config["enabled"]:
        return
    
    if not guild_config["events"].get(event_name, False):
        return
    
    channel_id = guild_config["channel_id"]
    if not channel_id:
        return
    
    channel = guild.get_channel(channel_id)
    if channel:
        try:
            await channel.send(embed=embed)
        except:
            pass

# ========== EVENTS ==========

async def setup_logs_events(bot):
    
    # Note: on_member_join est géré dans addon_events.py pour éviter les conflits
    
    @bot.event
    async def on_member_remove(member):
        """Membre quitte le serveur"""
        # Vérifier si c'est un kick ou un leave normal
        guild = member.guild
        
        # Attendre un peu pour voir si c'est un audit log de kick
        await discord.utils.sleep_until(datetime.utcnow())
        
        try:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.kick):
                if entry.target.id == member.id and (datetime.utcnow() - entry.created_at).total_seconds() < 5:
                    # C'est un kick
                    embed = discord.Embed(
                        title="👢 Membre expulsé",
                        description=f"{member.mention} a été expulsé",
                        color=discord.Color.orange(),
                        timestamp=datetime.utcnow()
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.add_field(name="👤 Membre", value=f"{member.name} ({member.id})", inline=False)
                    embed.add_field(name="👮 Modérateur", value=f"{entry.user.mention}", inline=True)
                    embed.add_field(name="📝 Raison", value=entry.reason or "Aucune raison", inline=True)
                    
                    await send_log(guild, "member_kick", embed)
                    return
        except:
            pass
        
        embed = discord.Embed(
            title="📤 Membre parti",
            description=f"{member.mention} a quitté le serveur",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="👤 Utilisateur", value=f"{member.name} ({member.id})", inline=False)
        embed.add_field(name="📊 Membres restants", value=f"{guild.member_count}", inline=True)
        
        await send_log(guild, "member_leave", embed)
    
    @bot.event
    async def on_member_ban(guild, user):
        """Membre banni"""
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    embed = discord.Embed(
                        title="🔨 Membre banni",
                        description=f"{user.mention} a été banni",
                        color=discord.Color.dark_red(),
                        timestamp=datetime.utcnow()
                    )
                    embed.set_thumbnail(url=user.display_avatar.url)
                    embed.add_field(name="👤 Utilisateur", value=f"{user.name} ({user.id})", inline=False)
                    embed.add_field(name="👮 Modérateur", value=f"{entry.user.mention}", inline=True)
                    embed.add_field(name="📝 Raison", value=entry.reason or "Aucune raison", inline=True)
                    
                    await send_log(guild, "member_ban", embed)
                    return
        except:
            pass
    
    @bot.event
    async def on_member_unban(guild, user):
        """Membre débanni"""
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.unban):
                if entry.target.id == user.id:
                    embed = discord.Embed(
                        title="✅ Membre débanni",
                        description=f"{user.mention} a été débanni",
                        color=discord.Color.green(),
                        timestamp=datetime.utcnow()
                    )
                    embed.set_thumbnail(url=user.display_avatar.url)
                    embed.add_field(name="👤 Utilisateur", value=f"{user.name} ({user.id})", inline=False)
                    embed.add_field(name="👮 Modérateur", value=f"{entry.user.mention}", inline=True)
                    
                    await send_log(guild, "member_unban", embed)
                    return
        except:
            pass
    
    @bot.event
    async def on_voice_state_update(member, before, after):
        """Changements dans les salons vocaux"""
        guild = member.guild
        
        if before.channel and after.channel and before.channel != after.channel:
            embed = discord.Embed(
                title="🔊 Déplacement vocal",
                description=f"{member.mention} a été déplacé",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="👤 Membre", value=f"{member.mention}", inline=False)
            embed.add_field(name="📤 Depuis", value=before.channel.mention, inline=True)
            embed.add_field(name="📥 Vers", value=after.channel.mention, inline=True)
            
            # Vérifier si c'est un move manuel par un modo
            try:
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_move):
                    if entry.target.id == member.id and (datetime.utcnow() - entry.created_at).total_seconds() < 2:
                        embed.add_field(name="👮 Par", value=entry.user.mention, inline=True)
                        break
            except:
                pass
            
            await send_log(guild, "member_voice_move", embed)
        
        elif before.channel and not after.channel:
            try:
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_disconnect):
                    if entry.target.id == member.id and (datetime.utcnow() - entry.created_at).total_seconds() < 2:
                        embed = discord.Embed(
                            title="🔇 Expulsion vocale",
                            description=f"{member.mention} a été expulsé d'un salon vocal",
                            color=discord.Color.dark_orange(),
                            timestamp=datetime.utcnow()
                        )
                        embed.add_field(name="👤 Membre", value=f"{member.mention}", inline=False)
                        embed.add_field(name="📤 Salon", value=before.channel.mention, inline=True)
                        embed.add_field(name="👮 Modérateur", value=entry.user.mention, inline=True)
                        
                        await send_log(guild, "member_voice_kick", embed)
                        return
            except:
                pass
        
        if before.mute != after.mute:
            if after.mute:
                embed = discord.Embed(
                    title="🔇 Membre muté (serveur)",
                    description=f"{member.mention} a été muté",
                    color=discord.Color.orange(),
                    timestamp=datetime.utcnow()
                )
            else:
                embed = discord.Embed(
                    title="🔊 Membre démuté (serveur)",
                    description=f"{member.mention} a été démuté",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
            
            embed.add_field(name="👤 Membre", value=f"{member.mention}", inline=True)
            if after.channel:
                embed.add_field(name="📍 Salon", value=after.channel.mention, inline=True)
            
            try:
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                    if entry.target.id == member.id and (datetime.utcnow() - entry.created_at).total_seconds() < 2:
                        embed.add_field(name="👮 Par", value=entry.user.mention, inline=True)
                        break
            except:
                pass
            
            await send_log(guild, "member_timeout" if after.mute else "member_untimeout", embed)
    
    @bot.event
    async def on_member_update(before, after):
        """Mise à jour d'un membre"""
        guild = after.guild
        
        if before.nick != after.nick:
            embed = discord.Embed(
                title="✏️ Pseudo modifié",
                description=f"{after.mention} a changé de pseudo",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="👤 Membre", value=f"{after.mention}", inline=False)
            embed.add_field(name="📝 Ancien pseudo", value=before.nick or before.name, inline=True)
            embed.add_field(name="📝 Nouveau pseudo", value=after.nick or after.name, inline=True)
            
            await send_log(guild, "member_nickname_change", embed)
        
        if before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]
            
            embed = discord.Embed(
                title="🎭 Rôles modifiés",
                description=f"Les rôles de {after.mention} ont été modifiés",
                color=discord.Color.purple(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="👤 Membre", value=f"{after.mention}", inline=False)
            
            if added_roles:
                embed.add_field(
                    name="➕ Rôles ajoutés",
                    value=", ".join([role.mention for role in added_roles]),
                    inline=False
                )
            
            if removed_roles:
                embed.add_field(
                    name="➖ Rôles retirés",
                    value=", ".join([role.mention for role in removed_roles]),
                    inline=False
                )
            
            current_roles = [role.mention for role in after.roles if role.name != "@everyone"]
            embed.add_field(
                name="📋 Rôles actuels",
                value=", ".join(current_roles) if current_roles else "Aucun",
                inline=False
            )
            
            try:
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                    if entry.target.id == after.id and (datetime.utcnow() - entry.created_at).total_seconds() < 2:
                        embed.add_field(name="👮 Modifié par", value=entry.user.mention, inline=True)
                        break
            except:
                pass
            
            await send_log(guild, "member_roles_update", embed)
        
        if before.timed_out_until != after.timed_out_until:
            if after.timed_out_until:
                embed = discord.Embed(
                    title="⏱️ Timeout appliqué",
                    description=f"{after.mention} a été mis en timeout",
                    color=discord.Color.orange(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="👤 Membre", value=f"{after.mention}", inline=False)
                embed.add_field(name="⏰ Expire le", value=f"<t:{int(after.timed_out_until.timestamp())}:F>", inline=True)
                
                try:
                    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                        if entry.target.id == after.id and (datetime.utcnow() - entry.created_at).total_seconds() < 2:
                            embed.add_field(name="👮 Par", value=entry.user.mention, inline=True)
                            if entry.reason:
                                embed.add_field(name="📝 Raison", value=entry.reason, inline=False)
                            break
                except:
                    pass
                
                await send_log(guild, "member_timeout", embed)
            else:
                embed = discord.Embed(
                    title="✅ Timeout retiré",
                    description=f"{after.mention} n'est plus en timeout",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="👤 Membre", value=f"{after.mention}", inline=False)
                
                await send_log(guild, "member_untimeout", embed)
    
    @bot.event
    async def on_message_delete(message):
        """Message supprimé"""
        if message.author.bot:
            return
        
        embed = discord.Embed(
            title="🗑️ Message supprimé",
            description=f"Message de {message.author.mention} supprimé dans {message.channel.mention}",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="👤 Auteur", value=f"{message.author.mention}", inline=True)
        embed.add_field(name="📍 Salon", value=message.channel.mention, inline=True)
        
        if message.content:
            content = message.content[:1024]
            embed.add_field(name="📝 Contenu", value=content, inline=False)
        
        if message.attachments:
            embed.add_field(name="📎 Pièces jointes", value=f"{len(message.attachments)} fichier(s)", inline=True)
        
        try:
            async for entry in message.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
                if (datetime.utcnow() - entry.created_at).total_seconds() < 2:
                    embed.add_field(name="🗑️ Supprimé par", value=entry.user.mention, inline=True)
                    break
        except:
            pass
        
        await send_log(message.guild, "message_delete", embed)
    
    @bot.event
    async def on_bulk_message_delete(messages):
        """Messages supprimés en masse"""
        if not messages:
            return
        
        first_msg = messages[0]
        
        embed = discord.Embed(
            title="🗑️ Suppression en masse",
            description=f"{len(messages)} messages supprimés dans {first_msg.channel.mention}",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="📊 Nombre", value=f"{len(messages)} messages", inline=True)
        embed.add_field(name="📍 Salon", value=first_msg.channel.mention, inline=True)
        
        try:
            async for entry in first_msg.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_bulk_delete):
                if (datetime.utcnow() - entry.created_at).total_seconds() < 2:
                    embed.add_field(name="👮 Par", value=entry.user.mention, inline=True)
                    break
        except:
            pass
        
        await send_log(first_msg.guild, "message_bulk_delete", embed)
    
    @bot.event
    async def on_message_edit(before, after):
        """Message édité"""
        if before.author.bot or before.content == after.content:
            return
        
        embed = discord.Embed(
            title="✏️ Message édité",
            description=f"Message de {after.author.mention} édité dans {after.channel.mention}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="👤 Auteur", value=f"{after.author.mention}", inline=True)
        embed.add_field(name="📍 Salon", value=after.channel.mention, inline=True)
        embed.add_field(name="🔗 Lien", value=f"[Aller au message]({after.jump_url})", inline=True)
        
        if before.content:
            embed.add_field(name="📝 Avant", value=before.content[:1024], inline=False)
        if after.content:
            embed.add_field(name="📝 Après", value=after.content[:1024], inline=False)
        
        await send_log(after.guild, "message_edit", embed)
    
    @bot.event
    async def on_guild_channel_create(channel):
        """Salon créé"""
        embed = discord.Embed(
            title="➕ Salon créé",
            description=f"Un salon a été créé",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="📍 Nom", value=channel.mention, inline=True)
        embed.add_field(name="🔖 Type", value=str(channel.type), inline=True)
        
        try:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
                if entry.target.id == channel.id:
                    embed.add_field(name="👮 Créé par", value=entry.user.mention, inline=True)
                    break
        except:
            pass
        
        await send_log(channel.guild, "channel_create", embed)
    
    @bot.event
    async def on_guild_channel_delete(channel):
        """Salon supprimé"""
        embed = discord.Embed(
            title="➖ Salon supprimé",
            description=f"Un salon a été supprimé",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="📍 Nom", value=f"#{channel.name}", inline=True)
        embed.add_field(name="🔖 Type", value=str(channel.type), inline=True)
        
        try:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                if entry.target.id == channel.id:
                    embed.add_field(name="👮 Supprimé par", value=entry.user.mention, inline=True)
                    break
        except:
            pass
        
        await send_log(channel.guild, "channel_delete", embed)
    
    @bot.event
    async def on_guild_channel_update(before, after):
        """Salon modifié"""
        changes = []
        
        if before.name != after.name:
            changes.append(f"**Nom:** {before.name} → {after.name}")
        
        if hasattr(before, 'topic') and before.topic != after.topic:
            changes.append(f"**Topic:** {before.topic or 'Aucun'} → {after.topic or 'Aucun'}")
        
        if not changes:
            return
        
        embed = discord.Embed(
            title="✏️ Salon modifié",
            description=f"{after.mention} a été modifié",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="📝 Modifications", value="\n".join(changes), inline=False)
        
        try:
            async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
                if entry.target.id == after.id and (datetime.utcnow() - entry.created_at).total_seconds() < 2:
                    embed.add_field(name="👮 Par", value=entry.user.mention, inline=True)
                    break
        except:
            pass
        
        await send_log(after.guild, "channel_update", embed)
    
    @bot.event
    async def on_guild_role_create(role):
        """Rôle créé"""
        embed = discord.Embed(
            title="🎭 Rôle créé",
            description=f"Un nouveau rôle a été créé",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="📛 Nom", value=role.mention, inline=True)
        embed.add_field(name="🎨 Couleur", value=str(role.color), inline=True)
        
        try:
            async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
                if entry.target.id == role.id:
                    embed.add_field(name="👮 Créé par", value=entry.user.mention, inline=True)
                    break
        except:
            pass
        
        await send_log(role.guild, "role_create", embed)
    
    @bot.event
    async def on_guild_role_delete(role):
        """Rôle supprimé"""
        embed = discord.Embed(
            title="🎭 Rôle supprimé",
            description=f"Un rôle a été supprimé",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="📛 Nom", value=role.name, inline=True)
        embed.add_field(name="🎨 Couleur", value=str(role.color), inline=True)
        
        try:
            async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
                if entry.target.id == role.id:
                    embed.add_field(name="👮 Supprimé par", value=entry.user.mention, inline=True)
                    break
        except:
            pass
        
        await send_log(role.guild, "role_delete", embed)
    
    @bot.event
    async def on_guild_role_update(before, after):
        """Rôle modifié"""
        changes = []
        
        if before.name != after.name:
            changes.append(f"**Nom:** {before.name} → {after.name}")
        
        if before.color != after.color:
            changes.append(f"**Couleur:** {before.color} → {after.color}")
        
        if before.permissions != after.permissions:
            changes.append(f"**Permissions:** Modifiées")
        
        if not changes:
            return
        
        embed = discord.Embed(
            title="🎭 Rôle modifié",
            description=f"{after.mention} a été modifié",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="📝 Modifications", value="\n".join(changes), inline=False)
        
        try:
            async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
                if entry.target.id == after.id and (datetime.utcnow() - entry.created_at).total_seconds() < 2:
                    embed.add_field(name="👮 Par", value=entry.user.mention, inline=True)
                    break
        except:
            pass
        
        await send_log(after.guild, "role_update", embed)
    
    @bot.event
    async def on_invite_create(invite):
        """Invitation créée"""
        embed = discord.Embed(
            title="🔗 Invitation créée",
            description=f"Une invitation a été créée",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="🔗 Code", value=invite.code, inline=True)
        embed.add_field(name="📍 Salon", value=invite.channel.mention if invite.channel else "Inconnu", inline=True)
        embed.add_field(name="👤 Créée par", value=invite.inviter.mention if invite.inviter else "Inconnu", inline=True)
        
        if invite.max_uses:
            embed.add_field(name="📊 Utilisations max", value=str(invite.max_uses), inline=True)
        
        if invite.max_age:
            embed.add_field(name="⏰ Expire dans", value=f"{invite.max_age // 3600}h", inline=True)
        
        await send_log(invite.guild, "invite_create", embed)
    
    @bot.event
    async def on_invite_delete(invite):
        """Invitation supprimée"""
        embed = discord.Embed(
            title="🔗 Invitation supprimée",
            description=f"Une invitation a été supprimée",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="🔗 Code", value=invite.code, inline=True)
        
        await send_log(invite.guild, "invite_delete", embed)

# ========== COMMANDES ==========

async def setup_logs_commands(bot):
    journaux_group = app_commands.Group(name="journaux", description="[ADMIN] Configuration des logs du serveur", default_permissions=discord.Permissions(administrator=True))
    bot.tree.add_command(journaux_group)

    @journaux_group.command(name="configurer", description="Configurer le système de logs")
    @app_commands.describe(salon="Le salon où envoyer les logs")
    async def logs_setup(interaction: discord.Interaction, salon: discord.TextChannel):
        guild_config = get_guild_config(interaction.guild.id)
        guild_config["enabled"] = True
        guild_config["channel_id"] = salon.id
        set_guild_config(interaction.guild.id, guild_config)
        
        embed = discord.Embed(
            title="✅ Logs configurés",
            description=f"Les logs seront envoyés dans {salon.mention}",
            color=discord.Color.green()
        )
        embed.add_field(
            name="💡 Prochaine étape",
            value="Utilise `/journaux evenements` pour activer/désactiver les événements que tu veux logger",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @journaux_group.command(name="evenements", description="Configurer les événements à logger")
    @app_commands.default_permissions(administrator=True)
    async def logs_config(interaction: discord.Interaction):
        guild_config = get_guild_config(interaction.guild.id)
        
        if not guild_config["enabled"]:
            await interaction.response.send_message(
                "❌ Les logs ne sont pas activés ! Utilise `/journaux configurer` d'abord.",
                ephemeral=True
            )
            return
        
        class LogsConfigView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=300)
                self.config = guild_config
                self.update_buttons()
            
            def update_buttons(self):
                self.clear_items()
                
                events_fr = {
                    "member_join": "📥 Arrivée de membres",
                    "member_leave": "📤 Départ de membres",
                    "member_kick": "👢 Membres kick",
                    "member_ban": "🔨 Membres ban",
                    "member_unban": "✅ Membres unban",
                    "member_voice_move": "🔊 Déplacement vocal",
                    "member_voice_kick": "🔇 Expulsion vocale",
                    "member_nickname_change": "✏️ Changement pseudo",
                    "member_roles_update": "🎭 Modification rôles",
                    "member_timeout": "⏱️ Timeout",
                    "member_untimeout": "✅ Fin timeout",
                    "message_delete": "🗑️ Messages supprimés",
                    "message_bulk_delete": "🗑️ Suppression en masse",
                    "message_edit": "✏️ Messages édités",
                    "channel_create": "➕ Création salon",
                    "channel_delete": "➖ Suppression salon",
                    "channel_update": "✏️ Modification salon",
                    "role_create": "🎭 Création rôle",
                    "role_delete": "🎭 Suppression rôle",
                    "role_update": "🎭 Modification rôle",
                    "invite_create": "🔗 Création invitation",
                    "invite_delete": "🔗 Suppression invitation"
                }
                
                for event, label in events_fr.items():
                    enabled = self.config["events"].get(event, False)
                    button = discord.ui.Button(
                        label=label,
                        style=discord.ButtonStyle.success if enabled else discord.ButtonStyle.secondary,
                        custom_id=event
                    )
                    button.callback = self.toggle_event
                    self.add_item(button)
            
            async def toggle_event(self, button_interaction: discord.Interaction):
                event = button_interaction.data["custom_id"]
                self.config["events"][event] = not self.config["events"].get(event, False)
                set_guild_config(interaction.guild.id, self.config)
                
                self.update_buttons()
                
                embed = discord.Embed(
                    title="⚙️ Configuration des logs",
                    description="Clique sur les boutons pour activer/désactiver les événements\n\n🟢 Vert = Activé | ⚪ Gris = Désactivé",
                    color=discord.Color.blue()
                )
                
                await button_interaction.response.edit_message(embed=embed, view=self)
        
        embed = discord.Embed(
            title="⚙️ Configuration des logs",
            description="Clique sur les boutons pour activer/désactiver les événements\n\n🟢 Vert = Activé | ⚪ Gris = Désactivé",
            color=discord.Color.blue()
        )
        
        view = LogsConfigView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    