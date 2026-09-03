import discord
from discord import app_commands
import json
import os
from datetime import datetime, timedelta
import asyncio

JAIL_FILE = "bot_data/jail_data.json"

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

async def setup_jail_system(bot):
    jail_data = load_data(JAIL_FILE)
    
    def save_jail():
        save_data_to_file(JAIL_FILE, jail_data)
    
    @bot.tree.command(name="emprisonner", description="[ADMIN] Emprisonner un membre")
    @app_commands.describe(membre="Le membre à emprisonner", raison="La raison")
    @app_commands.default_permissions(administrator=True)
    async def jail(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison"):
        guild_id = str(interaction.guild.id)
        
        if membre.id == interaction.user.id:
            await interaction.response.send_message("❌ Tu ne peux pas t'emprisonner !", ephemeral=True)
            return
        
        if membre.guild_permissions.administrator:
            await interaction.response.send_message("❌ Impossible d'emprisonner un admin !", ephemeral=True)
            return
        
        jail_role = discord.utils.get(interaction.guild.roles, name="🔒 Prison")
        if not jail_role:
            jail_role = await interaction.guild.create_role(
                name="🔒 Prison",
                color=discord.Color.dark_grey(),
                reason="Rôle de prison automatique"
            )
        
        jail_channel = discord.utils.get(interaction.guild.text_channels, name="prison")
        if not jail_channel:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                jail_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            jail_channel = await interaction.guild.create_text_channel(
                name="prison",
                overwrites=overwrites,
                topic="🔒 Salon réservé aux prisonniers"
            )
        
        for channel in interaction.guild.channels:
            if channel != jail_channel:
                await channel.set_permissions(jail_role, read_messages=False, send_messages=False)
        
        old_roles = [r.id for r in membre.roles if r != interaction.guild.default_role]
        
        user_id = str(membre.id)
        if guild_id not in jail_data:
            jail_data[guild_id] = {"prisoners": {}}
        
        jail_data[guild_id]["prisoners"][user_id] = {
            "old_roles": old_roles,
            "jailed_at": datetime.now().isoformat(),
            "jailed_by": str(interaction.user.id),
            "reason": raison,
            "temporary": False,
            "release_at": None
        }
        save_jail()
        
        await membre.remove_roles(*[r for r in membre.roles if r != interaction.guild.default_role])
        await membre.add_roles(jail_role)
        
        embed = discord.Embed(
            title="🔒 Membre emprisonné",
            description=f"{membre.mention} a été mis en prison.",
            color=discord.Color.dark_red()
        )
        embed.add_field(name="👮 Par", value=interaction.user.mention, inline=True)
        embed.add_field(name="📝 Raison", value=raison, inline=False)
        embed.add_field(name="⏰ Durée", value="**PERMANENT**", inline=True)
        
        await interaction.response.send_message(embed=embed)
        await jail_channel.send(f"🔒 {membre.mention} a été emprisonné.\n**Raison :** {raison}")
    
    @bot.tree.command(name="emprisonner_temporaire", description="[ADMIN] Prison temporaire")
    @app_commands.describe(membre="Le membre", duree="Durée en minutes", raison="La raison")
    @app_commands.default_permissions(administrator=True)
    async def temp_jail(interaction: discord.Interaction, membre: discord.Member, duree: int, raison: str = "Aucune raison"):
        guild_id = str(interaction.guild.id)
        
        if membre.id == interaction.user.id or membre.guild_permissions.administrator:
            await interaction.response.send_message("❌ Impossible !", ephemeral=True)
            return
        
        if duree < 1 or duree > 10080:
            await interaction.response.send_message("❌ Durée entre 1min et 7 jours !", ephemeral=True)
            return
        
        jail_role = discord.utils.get(interaction.guild.roles, name="🔒 Prison")
        if not jail_role:
            jail_role = await interaction.guild.create_role(name="🔒 Prison", color=discord.Color.dark_grey())
        
        jail_channel = discord.utils.get(interaction.guild.text_channels, name="prison")
        if not jail_channel:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                jail_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True)
            }
            jail_channel = await interaction.guild.create_text_channel("prison", overwrites=overwrites)
        
        for channel in interaction.guild.channels:
            if channel != jail_channel:
                await channel.set_permissions(jail_role, read_messages=False, send_messages=False)
        
        old_roles = [r.id for r in membre.roles if r != interaction.guild.default_role]
        release_time = datetime.now() + timedelta(minutes=duree)
        
        user_id = str(membre.id)
        if guild_id not in jail_data:
            jail_data[guild_id] = {"prisoners": {}}
        
        jail_data[guild_id]["prisoners"][user_id] = {
            "old_roles": old_roles,
            "jailed_at": datetime.now().isoformat(),
            "jailed_by": str(interaction.user.id),
            "reason": raison,
            "temporary": True,
            "release_at": release_time.isoformat()
        }
        save_jail()
        
        await membre.remove_roles(*[r for r in membre.roles if r != interaction.guild.default_role])
        await membre.add_roles(jail_role)
        
        hours = duree // 60
        minutes = duree % 60
        duration_text = f"{hours}h {minutes}min" if hours > 0 else f"{minutes}min"
        
        embed = discord.Embed(
            title="🔒 Prison temporaire",
            description=f"{membre.mention} emprisonné pour {duration_text}",
            color=discord.Color.orange()
        )
        embed.add_field(name="👮 Par", value=interaction.user.mention, inline=True)
        embed.add_field(name="📝 Raison", value=raison, inline=False)
        embed.add_field(name="🕐 Libération", value=f"<t:{int(release_time.timestamp())}:R>", inline=True)
        
        await interaction.response.send_message(embed=embed)
        await jail_channel.send(f"🔒 {membre.mention} emprisonné pour {duration_text}.\n**Raison :** {raison}")
    
    @bot.tree.command(name="liberer", description="[ADMIN] Libérer un prisonnier")
    @app_commands.describe(membre="Le membre à libérer")
    @app_commands.default_permissions(administrator=True)
    async def unjail(interaction: discord.Interaction, membre: discord.Member):
        guild_id = str(interaction.guild.id)
        user_id = str(membre.id)
        
        if guild_id not in jail_data or user_id not in jail_data[guild_id].get("prisoners", {}):
            await interaction.response.send_message("❌ Ce membre n'est pas en prison !", ephemeral=True)
            return
        
        prisoner_data = jail_data[guild_id]["prisoners"][user_id]
        jail_role = discord.utils.get(interaction.guild.roles, name="🔒 Prison")
        
        old_roles = [interaction.guild.get_role(rid) for rid in prisoner_data["old_roles"]]
        old_roles = [r for r in old_roles if r]
        
        if jail_role:
            await membre.remove_roles(jail_role)
        if old_roles:
            await membre.add_roles(*old_roles)
        
        del jail_data[guild_id]["prisoners"][user_id]
        save_jail()
        
        embed = discord.Embed(
            title="🔓 Membre libéré",
            description=f"{membre.mention} a été libéré.",
            color=discord.Color.green()
        )
        embed.add_field(name="👮 Par", value=interaction.user.mention)
        
        await interaction.response.send_message(embed=embed)
    
    # Auto-release task — vérifie une fois par jour à 12h00 (+ une vérification immédiate
    # au démarrage du bot, au cas où une prison temporaire aurait expiré pendant que le bot était hors ligne)
    async def auto_release_task():
        await bot.wait_until_ready()
        while not bot.is_closed():
            try:
                now = datetime.now()
                for guild_id, guild_data in jail_data.items():
                    if "prisoners" not in guild_data:
                        continue
                    
                    guild = bot.get_guild(int(guild_id))
                    if not guild:
                        continue
                    
                    jail_role = discord.utils.get(guild.roles, name="🔒 Prison")
                    to_release = []
                    
                    for user_id, data in guild_data["prisoners"].items():
                        if data["temporary"] and data["release_at"]:
                            release_time = datetime.fromisoformat(data["release_at"])
                            if now >= release_time:
                                to_release.append(user_id)
                    
                    for user_id in to_release:
                        member = guild.get_member(int(user_id))
                        if not member:
                            del guild_data["prisoners"][user_id]
                            continue
                        
                        prisoner_data = guild_data["prisoners"][user_id]
                        old_roles = [guild.get_role(rid) for rid in prisoner_data["old_roles"]]
                        old_roles = [r for r in old_roles if r]
                        
                        if jail_role:
                            await member.remove_roles(jail_role)
                        if old_roles:
                            await member.add_roles(*old_roles)
                        
                        del guild_data["prisoners"][user_id]
                
                save_jail()
            except Exception as e:
                print(f"Erreur auto-release: {e}")
            
            # Prochaine vérification : le lendemain (ou aujourd'hui si pas encore passé) à 12h00
            now = datetime.now()
            next_run = now.replace(hour=12, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            await asyncio.sleep((next_run - now).total_seconds())
    
    bot.loop.create_task(auto_release_task())