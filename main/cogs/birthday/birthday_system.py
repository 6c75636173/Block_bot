import discord
from discord import app_commands
import json
import os
import asyncio
from datetime import datetime

BIRTHDAY_FILE = "bot_data/birthday_data.json"

MOIS_NOMS = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
    5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
}

JOURS_PAR_MOIS = {
    1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30,
    7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
}

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

def get_next_birthday(day, month):
    """Retourne le timestamp du prochain anniversaire"""
    now = datetime.now()
    year = now.year

    try:
        next_bday = datetime(year, month, day)
    except ValueError:
        # 29 février sur année non bissextile
        next_bday = datetime(year, 3, 1)

    if next_bday < now:
        try:
            next_bday = datetime(year + 1, month, day)
        except ValueError:
            next_bday = datetime(year + 1, 3, 1)

    return int(next_bday.timestamp()), (next_bday - now).days

async def setup_birthday_system(bot, users_data, save_users_callback):
    birthday_data = load_data(BIRTHDAY_FILE, {"config": {}, "birthdays": {}})

    def save_birthday():
        save_data_to_file(BIRTHDAY_FILE, birthday_data)

    # ========== GROUPE /anniversaire ==========

    birthday_group = app_commands.Group(name="anniversaire", description="Système d'anniversaire 🎂")

    # ========== /anniversaire definir ==========

    @birthday_group.command(name="definir", description="Enregistre ton anniversaire")
    @app_commands.describe(jour="Jour de ton anniversaire (1-31)", mois="Mois de ton anniversaire (1-12)")
    async def birthday_set(interaction: discord.Interaction, jour: int, mois: int):
        user_id = str(interaction.user.id)

        if mois < 1 or mois > 12:
            await interaction.response.send_message("❌ Le mois doit être entre 1 et 12 !", ephemeral=True)
            return

        if jour < 1 or jour > JOURS_PAR_MOIS[mois]:
            await interaction.response.send_message(
                f"❌ Le jour doit être entre 1 et {JOURS_PAR_MOIS[mois]} pour {MOIS_NOMS[mois]} !",
                ephemeral=True
            )
            return

        if "birthdays" not in birthday_data:
            birthday_data["birthdays"] = {}

        already_set = user_id in birthday_data["birthdays"]

        birthday_data["birthdays"][user_id] = {
            "day": jour,
            "month": mois,
            "set_at": datetime.now().isoformat()
        }
        save_birthday()

        timestamp, days_left = get_next_birthday(jour, mois)

        embed = discord.Embed(
            title="🎂 Anniversaire enregistré !",
            color=discord.Color.pink()
        )

        if already_set:
            embed.description = "Ton anniversaire a été **mis à jour** !"
        else:
            embed.description = "Ton anniversaire a été **enregistré** !"

        embed.add_field(
            name="📅 Date",
            value=f"**{jour} {MOIS_NOMS[mois]}**",
            inline=True
        )
        embed.add_field(
            name="⏳ Prochain anniversaire",
            value=f"<t:{timestamp}:R>" if days_left > 0 else "🎉 C'est aujourd'hui !",
            inline=True
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Utilise /anniversaire supprimer pour supprimer ton anniversaire")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ========== /anniversaire supprimer ==========

    @birthday_group.command(name="supprimer", description="Supprime ton anniversaire enregistré")
    async def birthday_remove(interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        if user_id not in birthday_data.get("birthdays", {}):
            await interaction.response.send_message(
                "❌ Tu n'as pas d'anniversaire enregistré !",
                ephemeral=True
            )
            return

        del birthday_data["birthdays"][user_id]
        save_birthday()

        embed = discord.Embed(
            title="🗑️ Anniversaire supprimé",
            description="Ton anniversaire a été retiré de la base de données.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Tu peux en enregistrer un nouveau avec /anniversaire definir")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ========== /anniversaire voir ==========

    @birthday_group.command(name="voir", description="Voir l'anniversaire d'un membre")
    @app_commands.describe(membre="Le membre dont tu veux voir l'anniversaire")
    async def birthday_check(interaction: discord.Interaction, membre: discord.Member = None):
        target = membre or interaction.user
        user_id = str(target.id)

        if user_id not in birthday_data.get("birthdays", {}):
            msg = "Tu n'as pas enregistré ton anniversaire !" if not membre else f"{target.display_name} n'a pas enregistré son anniversaire !"
            await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
            return

        bday = birthday_data["birthdays"][user_id]
        jour, mois = bday["day"], bday["month"]
        timestamp, days_left = get_next_birthday(jour, mois)

        embed = discord.Embed(
            title=f"🎂 Anniversaire de {target.display_name}",
            color=discord.Color.pink()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="📅 Date", value=f"**{jour} {MOIS_NOMS[mois]}**", inline=True)

        if days_left == 0:
            embed.add_field(name="🎉 C'est aujourd'hui !", value="Bon anniversaire ! 🥳", inline=True)
        else:
            embed.add_field(name="⏳ Dans", value=f"<t:{timestamp}:R>", inline=True)

        await interaction.response.send_message(embed=embed)

    # ========== /anniversaire liste ==========

    @birthday_group.command(name="liste", description="Voir les prochains anniversaires du serveur")
    async def birthday_list(interaction: discord.Interaction):
        await interaction.response.defer()

        birthdays = birthday_data.get("birthdays", {})

        if not birthdays:
            await interaction.followup.send("❌ Aucun anniversaire enregistré sur ce serveur !", ephemeral=True)
            return

        guild_member_ids = {str(m.id) for m in interaction.guild.members}
        server_birthdays = {uid: data for uid, data in birthdays.items() if uid in guild_member_ids}

        if not server_birthdays:
            await interaction.followup.send("❌ Aucun membre de ce serveur n'a enregistré son anniversaire !", ephemeral=True)
            return

        sorted_bdays = []
        for user_id, bday in server_birthdays.items():
            timestamp, days_left = get_next_birthday(bday["day"], bday["month"])
            sorted_bdays.append((user_id, bday, timestamp, days_left))

        sorted_bdays.sort(key=lambda x: x[2])

        embed = discord.Embed(
            title="🎂 Prochains anniversaires",
            description=f"**{len(sorted_bdays)}** anniversaire(s) enregistré(s) sur ce serveur",
            color=discord.Color.pink()
        )

        today_bdays = []
        upcoming_bdays = []

        for user_id, bday, timestamp, days_left in sorted_bdays[:15]:
            member = interaction.guild.get_member(int(user_id))
            if not member:
                continue

            jour, mois = bday["day"], bday["month"]
            date_str = f"**{jour} {MOIS_NOMS[mois]}**"

            if days_left == 0:
                today_bdays.append(f"🎉 {member.mention} — {date_str} *(c'est aujourd'hui !)*")
            else:
                upcoming_bdays.append(f"• {member.mention} — {date_str} *(dans {days_left} jour(s))*")

        if today_bdays:
            embed.add_field(
                name="🥳 Anniversaires aujourd'hui !",
                value="\n".join(today_bdays),
                inline=False
            )

        if upcoming_bdays:
            embed.add_field(
                name="📅 À venir",
                value="\n".join(upcoming_bdays),
                inline=False
            )

        embed.set_footer(text="Enregistre le tien avec /anniversaire definir !")

        await interaction.followup.send(embed=embed)

    # ========== /anniversaire configurer_salon (ADMIN) ==========

    @birthday_group.command(name="configurer_salon", description="[ADMIN] Configurer le salon d'annonces d'anniversaire")
    @app_commands.describe(salon="Le salon où annoncer les anniversaires")
    @app_commands.default_permissions(administrator=True)
    async def birthday_setup(interaction: discord.Interaction, salon: discord.TextChannel):
        guild_id = str(interaction.guild.id)

        if "config" not in birthday_data:
            birthday_data["config"] = {}

        if guild_id not in birthday_data["config"]:
            birthday_data["config"][guild_id] = {}

        birthday_data["config"][guild_id]["channel_id"] = salon.id
        save_birthday()

        embed = discord.Embed(
            title="✅ Salon d'anniversaire configuré !",
            description=f"Les anniversaires seront annoncés dans {salon.mention} 🎂",
            color=discord.Color.green()
        )
        embed.add_field(
            name="📋 Fonctionnement",
            value="• Chaque jour à **minuit**, le bot vérifie les anniversaires\n"
                  "• Un message est envoyé automatiquement le jour J\n"
                  "• Le membre reçoit **500 pièces** en cadeau 🎁",
            inline=False
        )
        embed.set_footer(text="Configure aussi un rôle avec /anniversaire configurer_role")

        await interaction.response.send_message(embed=embed)

    # ========== /anniversaire configurer_role (ADMIN) ==========

    @birthday_group.command(name="configurer_role", description="[ADMIN] Configurer le rôle d'anniversaire temporaire")
    @app_commands.describe(role="Le rôle à donner le jour de l'anniversaire (retiré après 24h)")
    @app_commands.default_permissions(administrator=True)
    async def birthday_setup_role(interaction: discord.Interaction, role: discord.Role):
        guild_id = str(interaction.guild.id)

        if "config" not in birthday_data:
            birthday_data["config"] = {}

        if guild_id not in birthday_data["config"]:
            birthday_data["config"][guild_id] = {}

        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                f"❌ Je ne peux pas gérer le rôle {role.mention} car il est au-dessus de mon rôle !",
                ephemeral=True
            )
            return

        birthday_data["config"][guild_id]["role_id"] = role.id
        save_birthday()

        embed = discord.Embed(
            title="✅ Rôle d'anniversaire configuré !",
            color=discord.Color.green()
        )
        embed.add_field(name="🎭 Rôle", value=role.mention, inline=True)
        embed.add_field(name="⏰ Durée", value="**24 heures**", inline=True)
        embed.add_field(
            name="📋 Fonctionnement",
            value=f"Le rôle {role.mention} sera donné automatiquement le jour de l'anniversaire, puis retiré après 24h.",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    # ========== TÂCHE AUTOMATIQUE ==========

    async def birthday_check_task():
        await bot.wait_until_ready()
        while not bot.is_closed():
            try:
                now = datetime.now()
                today_day = now.day
                today_month = now.month

                birthdays = birthday_data.get("birthdays", {})
                configs = birthday_data.get("config", {})

                for guild in bot.guilds:
                    guild_id = str(guild.id)
                    config = configs.get(guild_id, {})
                    channel_id = config.get("channel_id")
                    role_id = config.get("role_id")

                    if not channel_id:
                        continue

                    channel = guild.get_channel(channel_id)
                    if not channel:
                        continue

                    for user_id, bday in birthdays.items():
                        if bday["day"] != today_day or bday["month"] != today_month:
                            continue

                        last_announced = bday.get("last_announced")
                        today_str = now.strftime("%Y-%m-%d")
                        if last_announced == today_str:
                            continue

                        member = guild.get_member(int(user_id))
                        if not member:
                            continue

                        user_str = str(member.id)
                        if user_str in users_data:
                            users_data[user_str]["pieces"] = users_data[user_str].get("pièces", 0) + 500
                            save_users_callback()

                        if role_id:
                            bday_role = guild.get_role(role_id)
                            if bday_role and bday_role < guild.me.top_role:
                                try:
                                    await member.add_roles(bday_role, reason="Anniversaire 🎂")
                                    async def remove_role_later(m, r):
                                        await asyncio.sleep(86400)
                                        try:
                                            await m.remove_roles(r, reason="Fin d'anniversaire")
                                        except:
                                            pass
                                    bot.loop.create_task(remove_role_later(member, bday_role))
                                except:
                                    pass

                        embed = discord.Embed(
                            title="🎂 Bon Anniversaire !",
                            description=f"Toute la communauté souhaite un **joyeux anniversaire** à {member.mention} ! 🥳🎉",
                            color=discord.Color.pink()
                        )
                        embed.add_field(name="🎁 Cadeau", value="**+500 pièces** offerts !", inline=True)
                        embed.set_thumbnail(url=member.display_avatar.url)
                        embed.set_footer(text=f"🎈 {bday['day']} {MOIS_NOMS[bday['month']]}")

                        await channel.send(content=member.mention, embed=embed)

                        birthday_data["birthdays"][user_id]["last_announced"] = today_str
                        save_birthday()

            except Exception as e:
                print(f"[Birthday] Erreur tâche auto: {e}")

            # Attendre jusqu'à la prochaine vérification (toutes les heures)
            await asyncio.sleep(3600)

    bot.loop.create_task(birthday_check_task())
    bot.tree.add_command(birthday_group)
