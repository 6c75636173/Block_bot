import discord
from discord import app_commands

import core
import economy_extensions
import business_system


async def setup_profil(bot):

    @bot.tree.command(name="profil", description="Affiche ton profil complet (niveau, XP, pièces, streak, défis...)")
    async def rank(interaction: discord.Interaction, membre: discord.Member = None):
        target = membre or interaction.user
        user_data = core.get_user_data(target.id)
        user_id = str(target.id)

        rank_name = core.get_rank_name(user_data["niveau"])
        next_level_xp = user_data["niveau"] * 100
        progress = (user_data["xp"] / next_level_xp) * 100
        streak = core.daily_data.get(user_id, {}).get("streak", 0)
        challenges_completed = len(core.challenges_data.get(user_id, {}).get("completed", []))
        items_count = len(user_data.get("inventaire", []))

        embed = discord.Embed(title=f"📊 Profil de {target.display_name}", color=discord.Color.blue())
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Niveau", value=f"🎯 {user_data['niveau']}", inline=True)
        embed.add_field(name="Rang", value=f"🏆 {rank_name}", inline=True)
        embed.add_field(name="Pièces", value=f"💰 {user_data['pieces']}", inline=True)
        embed.add_field(name="XP", value=f"⭐ {user_data['xp']}/{next_level_xp} ({progress:.1f}%)", inline=False)
        embed.add_field(name="Messages", value=f"💬 {user_data['messages']}", inline=True)
        embed.add_field(name="🔥 Streak quotidien", value=f"{streak} jour(s)", inline=True)
        embed.add_field(name="✅ Défis complétés", value=f"{challenges_completed}", inline=True)
        embed.add_field(name="🎒 Objets", value=f"{items_count}", inline=True)

        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="leaderboard", description="Affiche un classement du serveur")
    @app_commands.describe(categorie="Le classement à afficher (par défaut : XP)")
    @app_commands.choices(categorie=[
        app_commands.Choice(name="⭐ XP / Niveau", value="xp"),
        app_commands.Choice(name="💰 Plus riches", value="richest"),
        app_commands.Choice(name="🎰 Plus gros joueurs (casino)", value="gambler"),
        app_commands.Choice(name="💸 Plus gros perdants (casino)", value="loser"),
        app_commands.Choice(name="💼 Meilleurs business", value="business"),
    ])
    async def leaderboard(interaction: discord.Interaction, categorie: str = "xp"):
        if categorie == "xp":
            sorted_users = sorted(core.users_data.items(), key=lambda x: x[1]["xp"], reverse=True)[:10]
            if not sorted_users:
                await interaction.response.send_message("📊 Personne n'a encore de XP !", ephemeral=True)
                return
            embed = discord.Embed(title="🏆 Classement du serveur — XP", description="Top 10 des membres les plus actifs", color=discord.Color.gold())
            medals = ["🥇", "🥈", "🥉"]
            for i, (user_id, data) in enumerate(sorted_users):
                user = await core.get_display_user(interaction, int(user_id))
                medal = medals[i] if i < 3 else f"`#{i+1}`"
                rank_name = core.get_rank_name(data["niveau"])
                embed.add_field(name=f"{medal} {user.display_name}", value=f"Niveau {data['niveau']} • {data['xp']} XP • {rank_name}", inline=False)

        elif categorie == "richest":
            sorted_users = sorted(core.users_data.items(), key=lambda x: x[1]["pieces"], reverse=True)[:10]
            if not sorted_users:
                await interaction.response.send_message("📊 Personne n'a encore de pièces !", ephemeral=True)
                return
            embed = discord.Embed(title="💰 Classement du serveur — Plus riches", color=discord.Color.gold())
            medals = ["🥇", "🥈", "🥉"]
            for i, (user_id, data) in enumerate(sorted_users):
                user = await core.get_display_user(interaction, int(user_id))
                medal = medals[i] if i < 3 else f"`#{i+1}`"
                embed.add_field(name=f"{medal} {user.display_name}", value=f"💰 {data['pieces']} pièces", inline=False)

        elif categorie in ("gambler", "loser"):
            game_stats = economy_extensions.game_stats
            stat_key = "total_bet" if categorie == "gambler" else "total_lost"
            sorted_stats = sorted(
                [(uid, stats) for uid, stats in game_stats.items() if stats.get(stat_key, 0) > 0],
                key=lambda x: x[1].get(stat_key, 0), reverse=True
            )[:10]
            if not sorted_stats:
                await interaction.response.send_message("📊 Personne n'a encore joué au casino !", ephemeral=True)
                return
            if categorie == "gambler":
                embed = discord.Embed(title="🎰 Classement du serveur — Plus gros joueurs", description="Classement par montant total misé", color=discord.Color.red())
                medals = ["🥇", "🥈", "🥉"]
            else:
                embed = discord.Embed(title="💸 Classement du serveur — Plus gros perdants", description="Pour se vanner 😂", color=discord.Color.dark_red())
                medals = ["💀", "😭", "😢"]
            for i, (user_id, stats) in enumerate(sorted_stats):
                user = await core.get_display_user(interaction, int(user_id))
                medal = medals[i] if i < 3 else f"`#{i+1}`"
                if categorie == "gambler":
                    value = f"💸 {stats['total_bet']} pièces misés • {stats.get('casino_plays', 0)} parties"
                else:
                    value = f"💸 {stats['total_lost']} pièces perdus"
                embed.add_field(name=f"{medal} {user.display_name}", value=value, inline=False)

        elif categorie == "business":
            sorted_business = sorted(
                business_system.business_data.items(),
                key=lambda x: business_system.calculate_income(x[1]["type"], x[1]["level"]), reverse=True
            )[:10]
            if not sorted_business:
                await interaction.response.send_message("📊 Personne n'a encore de business !", ephemeral=True)
                return
            embed = discord.Embed(title="💼 Classement du serveur — Business", color=discord.Color.gold())
            for i, (uid, biz_data) in enumerate(sorted_business, 1):
                user = await core.get_display_user(interaction, int(uid))
                biz = business_system.BUSINESS_TYPES[biz_data["type"]]
                income = business_system.calculate_income(biz_data["type"], biz_data["level"])
                medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"#{i}")
                embed.add_field(name=f"{medal} {user.display_name}", value=f"{biz['name']} — Niveau {biz_data['level']}\n💰 {income} pièces/h", inline=False)

        await interaction.response.send_message(embed=embed)
