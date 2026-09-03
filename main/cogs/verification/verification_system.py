"""
Système de vérification avec captcha visuel simple et fonctionnel
"""

import discord
from discord import app_commands
import random
import string
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import io

# Données de vérification en mémoire
pending_verifications = {}  # {guild_id: {user_id: {"code": str, "expires": datetime}}}

def generate_captcha_code():
    """Génère un code captcha aléatoire (6 caractères, sans ambiguïté)"""
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(random.choices(chars, k=6))

def generate_captcha_image(code):
    """Génère une image de captcha simple avec le code"""
    width, height = 300, 100
    
    bg_color = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
    image = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(image)
    
    for _ in range(8):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        color = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
        draw.line([(x1, y1), (x2, y2)], fill=color, width=2)
    
    for _ in range(100):
        x, y = random.randint(0, width), random.randint(0, height)
        draw.point((x, y), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
    except:
        try:
            font = ImageFont.truetype("C:\\Windows\\Fonts\\Arial.ttf", 50)
        except:
            font = ImageFont.load_default()
    
    text_bbox = draw.textbbox((0, 0), code, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x+2, y+2), code, fill=(0, 0, 0), font=font)
    draw.text((x, y), code, fill=(random.randint(0, 100), random.randint(0, 100), random.randint(0, 100)), font=font)
    
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes

async def send_verification_message(channel, member, verification_config):
    """Envoie le message de captcha à un nouveau membre"""
    guild_id = str(member.guild.id)
    user_id = str(member.id)
    
    code = generate_captcha_code()
    
    if guild_id not in pending_verifications:
        pending_verifications[guild_id] = {}
    
    pending_verifications[guild_id][user_id] = {
        "code": code,
        "expires": datetime.now() + timedelta(minutes=10),
        "message_id": None,
        "channel_id": channel.id
    }
    
    captcha_image = generate_captcha_image(code)
    file = discord.File(fp=captcha_image, filename="captcha.png")
    
    embed = discord.Embed(
        title="🛡️ Vérification Anti-Raid",
        description=f"Bienvenue {member.mention} !\n\nPour accéder au serveur, entre le code affiché ci-dessous.",
        color=discord.Color.blue()
    )
    embed.set_image(url="attachment://captcha.png")
    embed.add_field(
        name="📝 Comment se vérifier ?",
        value="Utilise la commande `/verify [code]`\nExemple : `/verify ABC123`",
        inline=False
    )
    embed.add_field(
        name="⏰ Expiration",
        value="Tu as **10 minutes** pour entrer le code.",
        inline=True
    )
    embed.add_field(
        name="🔄 Nouveau code ?",
        value="Utilise `/verification nouveau_captcha`",
        inline=True
    )
    embed.set_footer(text="⚠️ Le code est sensible à la casse (majuscules/minuscules)")
    
    try:
        message = await channel.send(content=f"{member.mention}", embed=embed, file=file)
        pending_verifications[guild_id][user_id]["message_id"] = message.id
    except Exception as e:
        print(f"Erreur envoi captcha: {e}")

def setup_verification_commands(bot, verification_config, save_verification_config):
    """Configure toutes les commandes du groupe /verification (anciennement coupé entre
    ce fichier et block_bot.py — maintenant tout est ici, un seul endroit pour ce domaine)."""
    verification_group = app_commands.Group(name="verification", description="Système de vérification anti-raid")
    bot.tree.add_command(verification_group)

    @verification_group.command(name="verifier", description="Vérifie ton compte avec le code captcha")
    @app_commands.describe(code="Le code affiché dans l'image")
    async def verify(interaction: discord.Interaction, code: str):
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        if guild_id not in verification_config:
            await interaction.response.send_message("❌ Le système de vérification n'est pas configuré.", ephemeral=True)
            return
        
        config = verification_config[guild_id]
        
        if guild_id not in pending_verifications or user_id not in pending_verifications[guild_id]:
            await interaction.response.send_message(
                "❌ Tu n'as pas de captcha en attente. Utilise `/verification nouveau_captcha` pour en obtenir un.",
                ephemeral=True
            )
            return
        
        user_data = pending_verifications[guild_id][user_id]
        
        if datetime.now() > user_data["expires"]:
            del pending_verifications[guild_id][user_id]
            await interaction.response.send_message(
                "❌ Ton captcha a expiré. Utilise `/verification nouveau_captcha` pour en obtenir un nouveau.",
                ephemeral=True
            )
            return
        
        # Vérifier le code (sensible à la casse)
        if code.upper() != user_data["code"].upper():
            await interaction.response.send_message(
                "❌ Code incorrect ! Vérifie bien l'image et réessaye.\n💡 Le code est sensible à la casse.",
                ephemeral=True
            )
            return
        
        if user_data.get("message_id") and user_data.get("channel_id"):
            try:
                channel = interaction.guild.get_channel(user_data["channel_id"])
                if channel:
                    message = await channel.fetch_message(user_data["message_id"])
                    await message.delete()
                    print(f"✅ Message captcha supprimé pour {interaction.user}")
            except Exception as e:
                print(f"⚠️ Impossible de supprimer le captcha: {e}")
        
        del pending_verifications[guild_id][user_id]
        
        if config.get("unverified_role_id"):
            unverified_role = interaction.guild.get_role(config["unverified_role_id"])
            if unverified_role and unverified_role in interaction.user.roles:
                try:
                    await interaction.user.remove_roles(unverified_role)
                except:
                    pass
        
        verified_role = interaction.guild.get_role(config["verified_role_id"])
        if verified_role:
            try:
                await interaction.user.add_roles(verified_role)
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ Erreur lors de l'attribution du rôle : {e}",
                    ephemeral=True
                )
                return
        
        await interaction.response.send_message(
            "✅ Vérification réussie ! Tu as maintenant accès au serveur. Bienvenue ! 🎉",
            ephemeral=True
        )
        
        if config.get("log_channel_id"):
            log_channel = interaction.guild.get_channel(config["log_channel_id"])
            if log_channel:
                log_embed = discord.Embed(
                    title="✅ Membre vérifié",
                    description=f"{interaction.user.mention} ({interaction.user})",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                log_embed.set_thumbnail(url=interaction.user.display_avatar.url)
                await log_channel.send(embed=log_embed)
    
    @verification_group.command(name="nouveau_captcha", description="Demande un nouveau captcha")
    async def request_captcha(interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        
        if guild_id not in verification_config:
            await interaction.response.send_message("❌ Le système de vérification n'est pas configuré.", ephemeral=True)
            return
        
        config = verification_config[guild_id]
        channel = interaction.guild.get_channel(config["channel_id"])
        
        if not channel:
            await interaction.response.send_message("❌ Le salon de vérification n'existe plus.", ephemeral=True)
            return
        
        user_id = str(interaction.user.id)
        if guild_id in pending_verifications and user_id in pending_verifications[guild_id]:
            old_data = pending_verifications[guild_id][user_id]
            if old_data.get("message_id") and old_data.get("channel_id"):
                try:
                    old_channel = interaction.guild.get_channel(old_data["channel_id"])
                    if old_channel:
                        old_message = await old_channel.fetch_message(old_data["message_id"])
                        await old_message.delete()
                        print(f"✅ Ancien captcha supprimé pour {interaction.user}")
                except Exception as e:
                    print(f"⚠️ Impossible de supprimer l'ancien captcha: {e}")
        
        await interaction.response.send_message("✅ Un nouveau captcha va être envoyé...", ephemeral=True)
        await send_verification_message(channel, interaction.user, verification_config)
    @verification_group.command(name="configurer", description="Configure le système de vérification")
    @app_commands.describe(
        salon_verification="Le salon où les captchas apparaîtront",
        role_verifie="Le rôle à donner après vérification",
        role_non_verifie="Le rôle à donner en attendant (optionnel)",
        salon_logs="Salon pour les logs de vérification (optionnel)"
    )
    @app_commands.default_permissions(administrator=True)
    async def setup_verification(
        interaction: discord.Interaction, 
        salon_verification: discord.TextChannel,
        role_verifie: discord.Role,
        role_non_verifie: discord.Role = None,
        salon_logs: discord.TextChannel = None
    ):
        guild_id = str(interaction.guild.id)
    
        verification_config[guild_id] = {
            "channel_id": salon_verification.id,
            "verified_role_id": role_verifie.id,
            "unverified_role_id": role_non_verifie.id if role_non_verifie else None,
            "log_channel_id": salon_logs.id if salon_logs else None
        }
    
        save_verification_config()
    
        embed = discord.Embed(
            title="🛡️ Salon de vérification",
            description="Les nouveaux membres recevront leur captcha ici.\n\nPour se vérifier, ils devront entrer le code affiché dans l'image avec `/verification verifier [code]`",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="💡 Conseils",
            value="• Le code est sensible à la casse (A ≠ a)\n• Chaque captcha expire après 10 minutes\n• Utilise `/verification nouveau_captcha` pour un nouveau code",
            inline=False
        )
    
        await salon_verification.send(embed=embed)
    
        confirm_embed = discord.Embed(
            title="✅ Système de vérification configuré !",
            description="Les nouveaux membres devront résoudre un captcha visuel pour accéder au serveur.",
            color=discord.Color.green()
        )
        confirm_embed.add_field(name="Salon de vérification", value=salon_verification.mention, inline=False)
        confirm_embed.add_field(name="Rôle vérifié", value=role_verifie.mention, inline=True)
        if role_non_verifie:
            confirm_embed.add_field(name="Rôle non-vérifié", value=role_non_verifie.mention, inline=True)
        if salon_logs:
            confirm_embed.add_field(name="Salon de logs", value=salon_logs.mention, inline=True)
    
        confirm_embed.add_field(
            name="📋 Fonctionnement",
            value=f"1️⃣ Nouveau membre rejoint → Reçoit le rôle {role_non_verifie.mention if role_non_verifie else 'non-vérifié'}\n2️⃣ Un captcha visuel apparaît dans {salon_verification.mention}\n3️⃣ Il entre le code avec `/verification verifier [code]`\n4️⃣ Il obtient {role_verifie.mention} et accède au serveur",
            inline=False
        )
    
        await interaction.response.send_message(embed=confirm_embed)

    @verification_group.command(name="desactiver", description="Désactive le système de vérification")
    @app_commands.default_permissions(administrator=True)
    async def disable_verification(interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
    
        if guild_id not in verification_config:
            await interaction.response.send_message("❌ Le système de vérification n'est pas configuré sur ce serveur.", ephemeral=True)
            return
    
        del verification_config[guild_id]
        save_verification_config()
    
        if guild_id in verification_system.pending_verifications:
            del verification_system.pending_verifications[guild_id]
    
        embed = discord.Embed(
            title="✅ Système de vérification désactivé",
            description="Les nouveaux membres n'auront plus besoin de se vérifier.",
            color=discord.Color.orange()
        )
    
        await interaction.response.send_message(embed=embed)

    @verification_group.command(name="verifier_membre", description="Vérifie manuellement un utilisateur")
    @app_commands.describe(membre="Le membre à vérifier manuellement")
    @app_commands.default_permissions(moderate_members=True)
    async def verify_user_cmd(interaction: discord.Interaction, membre: discord.Member):
        guild_id = str(interaction.guild.id)
    
        if guild_id not in verification_config:
            await interaction.response.send_message("❌ Le système de vérification n'est pas configuré sur ce serveur.", ephemeral=True)
            return
    
        config = verification_config[guild_id]
    
        verified_role = interaction.guild.get_role(config.get("verified_role_id"))
        if verified_role and verified_role in membre.roles:
            await interaction.response.send_message(f"✅ {membre.mention} est déjà vérifié !", ephemeral=True)
            return
    
        if config.get("unverified_role_id"):
            unverified_role = interaction.guild.get_role(config["unverified_role_id"])
            if unverified_role and unverified_role in membre.roles:
                await membre.remove_roles(unverified_role)
    
        if verified_role:
            await membre.add_roles(verified_role)
    
        user_id = str(membre.id)
        if guild_id in verification_system.pending_verifications and user_id in verification_system.pending_verifications[guild_id]:
            message_id = verification_system.pending_verifications[guild_id][user_id].get("message_id")
            if message_id and config.get("channel_id"):
                try:
                    channel = interaction.guild.get_channel(config["channel_id"])
                    message = await channel.fetch_message(message_id)
                    await message.delete()
                except:
                    pass
            del verification_system.pending_verifications[guild_id][user_id]
    
        embed = discord.Embed(
            title="✅ Membre vérifié manuellement",
            description=f"{membre.mention} a été vérifié par {interaction.user.mention}",
            color=discord.Color.green()
        )
    
        await interaction.response.send_message(embed=embed)
    
        try:
            dm_embed = discord.Embed(
                title="✅ Tu as été vérifié !",
                description=f"Un modérateur t'a vérifié manuellement sur **{interaction.guild.name}**.\n\nTu as maintenant accès à tous les salons !",
                color=discord.Color.green()
            )
            await membre.send(embed=dm_embed)
        except:
            pass
    
        if config.get("log_channel_id"):
            log_channel = interaction.guild.get_channel(config["log_channel_id"])
            if log_channel:
                log_embed = discord.Embed(
                    title="✅ Vérification manuelle",
                    description=f"{membre.mention} ({membre})\nVérifié par {interaction.user.mention}",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                log_embed.set_thumbnail(url=membre.display_avatar.url)
                await log_channel.send(embed=log_embed)

class VerificationView(discord.ui.View):
    def __init__(self, user_id, code):
        super().__init__(timeout=600)  # 10 minutes
        self.user_id = user_id
        self.code = code
    
    @discord.ui.button(label="✅ J'ai entré le code", style=discord.ButtonStyle.green, custom_id="check_verification")
    async def check_verification(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Ce n'est pas ton captcha !", ephemeral=True)
            return
        
        await interaction.response.send_message("⏳ Vérification en cours...", ephemeral=True)
        
        # La vérification se fait via la commande /verify
        # Ce bouton sert juste à confirmer qu'ils ont essayé
    
    @discord.ui.button(label="🔄 Nouveau captcha", style=discord.ButtonStyle.blurple, custom_id="new_captcha")
    async def new_captcha(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Ce n'est pas ton captcha !", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            await interaction.message.delete()
        except:
            pass
        
        await interaction.followup.send("✅ Utilise `/verification nouveau_captcha` pour obtenir un nouveau code.", ephemeral=True)

async def send_captcha_to_channel(channel, user, verification_config):
    """Envoie un captcha visuel dans le salon de vérification"""
    guild_id = str(channel.guild.id)
    user_id = str(user.id)
    
    code = generate_captcha_code()
    
    captcha_image = generate_captcha_image(code)
    file = discord.File(fp=captcha_image, filename="captcha.png")
    
    embed = discord.Embed(
        title="🛡️ Vérification requise",
        description=f"{user.mention}, bienvenue sur le serveur !\n\nPour accéder aux salons, entre le code affiché dans l'image ci-dessous.",
        color=discord.Color.blue()
    )
    embed.set_image(url="attachment://captcha.png")
    embed.add_field(
        name="📝 Comment se vérifier ?",
        value=f"Utilise la commande : `/verify [code]`\nExemple : `/verify ABC123`",
        inline=False
    )
    embed.set_footer(text="⏱️ Ce code expire dans 10 minutes • Sensible à la casse")
    
    view = VerificationView(user.id, code)
    
    message = await channel.send(embed=embed, file=file, view=view)
    
    if guild_id not in pending_verifications:
        pending_verifications[guild_id] = {}
    
    pending_verifications[guild_id][user_id] = {
        "code": code,
        "message_id": message.id,
        "expires": datetime.now() + timedelta(minutes=10)
    }
    
    return message

async def verify_user_with_code(interaction, code, verification_config):
    """Vérifie un utilisateur avec le code fourni"""
    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)
    
    config = verification_config.get(guild_id)
    if not config:
        return False, "❌ Le système de vérification n'est pas configuré sur ce serveur."
    
    verified_role = interaction.guild.get_role(config.get("verified_role_id"))
    if verified_role and verified_role in interaction.user.roles:
        return False, "✅ Tu es déjà vérifié !"
    
    if guild_id not in pending_verifications or user_id not in pending_verifications[guild_id]:
        return False, "❌ Tu n'as pas de code de vérification en attente. Utilise `/verification nouveau_captcha` pour en obtenir un."
    
    user_verification = pending_verifications[guild_id][user_id]
    
    if datetime.now() > user_verification["expires"]:
        del pending_verifications[guild_id][user_id]
        return False, "❌ Ton code a expiré ! Utilise `/verification nouveau_captcha` pour en obtenir un nouveau."
    
    # Vérifier le code (sensible à la casse)
    if code != user_verification["code"]:
        return False, "❌ Code incorrect ! Vérifie bien les majuscules/minuscules.\n💡 Astuce : Le code est sensible à la casse (A ≠ a)"
    
    if config.get("unverified_role_id"):
        unverified_role = interaction.guild.get_role(config["unverified_role_id"])
        if unverified_role and unverified_role in interaction.user.roles:
            await interaction.user.remove_roles(unverified_role)
    
    if verified_role:
        await interaction.user.add_roles(verified_role)
    
    try:
        if config.get("channel_id"):
            channel = interaction.guild.get_channel(config["channel_id"])
            if channel:
                message = await channel.fetch_message(user_verification["message_id"])
                await message.delete()
    except:
        pass
    
    del pending_verifications[guild_id][user_id]
    
    if config.get("log_channel_id"):
        log_channel = interaction.guild.get_channel(config["log_channel_id"])
        if log_channel:
            log_embed = discord.Embed(
                title="✅ Nouveau membre vérifié",
                description=f"{interaction.user.mention} ({interaction.user})",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            log_embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await log_channel.send(embed=log_embed)
    
    return True, f"✅ Vérification réussie !\n\nBienvenue sur le serveur {interaction.user.mention} !\nTu as maintenant accès à tous les salons. Amuse-toi bien ! 🎉"

def cleanup_expired_verifications():
    """Nettoie les vérifications expirées"""
    now = datetime.now()
    for guild_id in list(pending_verifications.keys()):
        for user_id in list(pending_verifications[guild_id].keys()):
            if now > pending_verifications[guild_id][user_id]["expires"]:
                del pending_verifications[guild_id][user_id]
        if not pending_verifications[guild_id]:
            del pending_verifications[guild_id]