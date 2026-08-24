import discord
from discord import app_commands
from datetime import datetime, timedelta

import core


async def setup_quotidien(bot):

    # ========== COMMANDES DAILY & STREAKS ==========
    @bot.tree.command(name="quotidien", description="Récupère ta récompense quotidienne (ou consulte ton streak / celui d'un membre)")
    @app_commands.describe(membre="Consulter le streak de ce membre au lieu de réclamer ta récompense (optionnel)")
    async def daily(interaction: discord.Interaction, membre: discord.Member = None):
        # Consultation d'un autre membre -> toujours en mode "info", jamais de réclamation
        if membre is not None and membre.id != interaction.user.id:
            await _show_streak_info(interaction, membre)
            return

        user_id = str(interaction.user.id)
        user_data = core.get_user_data(interaction.user.id)

        if user_id not in core.daily_data:
            core.daily_data[user_id] = {"last_claim": None, "streak": 0}

        today = datetime.now().date().isoformat()
        last_claim = core.daily_data[user_id].get("last_claim")

        if last_claim == today:
            # Déjà réclamé aujourd'hui -> on affiche les infos de streak au lieu d'une simple erreur
            await _show_streak_info(interaction, interaction.user, already_claimed_today=True)
            return

        yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()

        if last_claim == yesterday:
            core.daily_data[user_id]["streak"] += 1
        elif last_claim is None:
            core.daily_data[user_id]["streak"] = 1
        else:
            core.daily_data[user_id]["streak"] = 1

        streak = core.daily_data[user_id]["streak"]

        base_reward = 100
        streak_bonus = min(streak * 50, 500)
        total_reward = base_reward + streak_bonus

        week_bonus = 0
        if streak % 7 == 0:
            week_bonus = 1000
            total_reward += week_bonus

        user_data["pieces"] += total_reward
        core.daily_data[user_id]["last_claim"] = today

        core.save_data(core.USERS_FILE, core.users_data)
        core.save_data(core.DAILY_FILE, core.daily_data)

        embed = discord.Embed(
            title="💰 Récompense quotidienne !",
            description=f"Tu as récupéré tes pièces quotidiennes !",
            color=discord.Color.gold()
        )
        embed.add_field(name="Récompense de base", value=f"💵 {base_reward} pièces", inline=True)
        embed.add_field(name="Bonus streak", value=f"🔥 {streak_bonus} pièces", inline=True)

        if week_bonus > 0:
            embed.add_field(name="🎉 BONUS SEMAINE !", value=f"🎁 {week_bonus} pièces", inline=False)

        embed.add_field(name="Total reçu", value=f"✨ **{total_reward} pièces**", inline=False)
        embed.add_field(name="Streak actuel", value=f"🔥 **{streak} jour(s)**", inline=True)
        embed.add_field(name="Nouveau solde", value=f"💰 {user_data['pieces']} pièces", inline=True)

        embed.set_footer(text="Reviens demain pour continuer ton streak !")

        await interaction.response.send_message(embed=embed)


    async def _show_streak_info(interaction: discord.Interaction, target: discord.Member, already_claimed_today: bool = False):
        """Affiche les infos de streak sans réclamer (anciennement /streak, fusionné dans /quotidien)."""
        user_id = str(target.id)

        if user_id not in core.daily_data:
            await interaction.response.send_message(f"{target.mention} n'a pas encore récupéré de récompense quotidienne !", ephemeral=True)
            return

        streak = core.daily_data[user_id].get("streak", 0)
        last_claim = core.daily_data[user_id].get("last_claim")

        if last_claim:
            last_claim_date = datetime.fromisoformat(last_claim)
            last_claim_str = last_claim_date.strftime("%d/%m/%Y")
        else:
            last_claim_str = "Jamais"

        embed = discord.Embed(
            title=f"🔥 Streak de {target.display_name}",
            color=discord.Color.orange()
        )
        if already_claimed_today:
            embed.description = "✅ Déjà réclamée aujourd'hui — reviens demain !"
        embed.add_field(name="Streak actuel", value=f"**{streak} jour(s)**", inline=True)
        embed.add_field(name="Dernière récompense", value=last_claim_str, inline=True)

        next_week_bonus = 7 - (streak % 7) if streak % 7 != 0 else 7
        embed.add_field(
            name="Prochain bonus semaine",
            value=f"Dans {next_week_bonus} jour(s) 🎁",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    # ========== COMMANDES DÉFIS ==========
    @bot.tree.command(name="defi", description="Affiche ton défi du jour")
    async def challenge(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
    
        is_new = core.assign_daily_challenge(user_id)
    
        if user_id not in core.challenges_data or not core.challenges_data[user_id].get("current"):
            await interaction.response.send_message("❌ Erreur lors de la récupération du défi", ephemeral=True)
            return
    
        current = core.challenges_data[user_id]["current"]
        challenge = current["challenge"]
        progress = current["progress"]
    
        percentage = min(int((progress / challenge["objectif"]) * 100), 100)
        bar_length = int(percentage / 10)
        bar = "█" * bar_length + "░" * (10 - bar_length)
    
        embed = discord.Embed(
            title="🎯 Défi du jour",
            description=f"**{challenge['nom']}**",
            color=discord.Color.blue()
        )
    
        if is_new:
            embed.add_field(name="✨ Nouveau défi !", value="Un nouveau défi t'a été assigné !", inline=False)
    
        embed.add_field(name="Objectif", value=challenge["description"], inline=False)
        embed.add_field(
            name="Progression",
            value=f"`{bar}` {progress}/{challenge['objectif']} ({percentage}%)",
            inline=False
        )
        embed.add_field(name="Récompense", value=f"💰 {challenge['recompense']} pièces", inline=False)
    
        completed_count = len(core.challenges_data[user_id].get("completed", []))
        embed.set_footer(text=f"Défis complétés : {completed_count}")
    
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await setup_quotidien(bot)

