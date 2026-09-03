import discord
from discord import app_commands

import core

# État des paris — module-level (comme business_data dans business_system.py)
active_bets = {}
bet_counter = 0


async def setup_paris(bot):

    # ========== COMMANDES PARIS ==========
    @bot.tree.command(name="creer_pari", description="Créer un pari")
    @app_commands.describe(description="Description du pari", option1="Première option", option2="Deuxième option")
    async def createbet(interaction: discord.Interaction, description: str, option1: str, option2: str):
        global bet_counter
        bet_counter += 1
    
        bet_id = bet_counter
        active_bets[bet_id] = {
            "creator": interaction.user.id,
            "description": description,
            "participants": {},
            "choices": [option1, option2],
            "closed": False,
            "winner": None
        }
    
        embed = discord.Embed(
            title="🎲 Nouveau Pari !",
            description=f"**{description}**",
            color=discord.Color.blue()
        )
        embed.add_field(name="Option 1", value=f"✅ {option1}", inline=True)
        embed.add_field(name="Option 2", value=f"❌ {option2}", inline=True)
        embed.add_field(name="ID du pari", value=f"`{bet_id}`", inline=False)
        embed.set_footer(text=f"Utilise /placebet {bet_id} [option] [montant] pour parier")
    
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="parier", description="Parier sur un résultat")
    @app_commands.describe(bet_id="ID du pari", choix="1 ou 2", montant="Montant à parier")
    async def placebet(interaction: discord.Interaction, bet_id: int, choix: int, montant: int):
        if bet_id not in active_bets:
            await interaction.response.send_message("❌ Ce pari n'existe pas !", ephemeral=True)
            return
    
        bet = active_bets[bet_id]
    
        if bet["closed"]:
            await interaction.response.send_message("❌ Ce pari est fermé !", ephemeral=True)
            return
    
        if choix not in [1, 2]:
            await interaction.response.send_message("❌ Choisis 1 ou 2 !", ephemeral=True)
            return
    
        user_data = core.get_user_data(interaction.user.id)
    
        if montant < 10:
            await interaction.response.send_message("❌ Mise minimum : 10 pièces !", ephemeral=True)
            return
    
        if user_data["pieces"] < montant:
            await interaction.response.send_message(f"❌ Tu n'as que {user_data['pieces']} pièces !", ephemeral=True)
            return
    
        user_data["pieces"] -= montant
        core.save_data(core.USERS_FILE, core.users_data)
    
        completed_challenge = update_challenge_progress(interaction.user.id, "spent", montant)
        if completed_challenge:
            await complete_challenge(str(interaction.user.id), completed_challenge, interaction.channel)
    
        user_id = str(interaction.user.id)
        bet["participants"][user_id] = {
            "choice": choix,
            "amount": montant
        }
    
        chosen_option = bet["choices"][choix - 1]
    
        embed = discord.Embed(
            title="✅ Pari placé !",
            description=f"Tu as parié **{montant} pièces** sur :\n**{chosen_option}**",
            color=discord.Color.green()
        )
        embed.add_field(name="Solde restant", value=f"💰 {user_data['pieces']} pièces")
    
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="fermer_pari", description="Fermer un pari et désigner le gagnant")
    @app_commands.describe(bet_id="ID du pari", gagnant="1 ou 2")
    async def closebet(interaction: discord.Interaction, bet_id: int, gagnant: int):
        if bet_id not in active_bets:
            await interaction.response.send_message("❌ Ce pari n'existe pas !", ephemeral=True)
            return
    
        bet = active_bets[bet_id]
    
        if bet["creator"] != interaction.user.id:
            await interaction.response.send_message("❌ Seul le créateur peut fermer le pari !", ephemeral=True)
            return
    
        if bet["closed"]:
            await interaction.response.send_message("❌ Ce pari est déjà fermé !", ephemeral=True)
            return
    
        if gagnant not in [1, 2]:
            await interaction.response.send_message("❌ Choisis 1 ou 2 !", ephemeral=True)
            return
    
        total_pot = sum(p["amount"] for p in bet["participants"].values())
        winners = {uid: p for uid, p in bet["participants"].items() if p["choice"] == gagnant}
        total_winners_bet = sum(w["amount"] for w in winners.values())
    
        if not winners:
            await interaction.response.send_message("❌ Personne n'a parié sur cette option ! Pari annulé, pièces remboursés.", ephemeral=True)
            for user_id, participant in bet["participants"].items():
                user_data = core.get_user_data(int(user_id))
                user_data["pieces"] += participant["amount"]
            core.save_data(core.USERS_FILE, core.users_data)
            del active_bets[bet_id]
            return
    
        results = []
        for user_id, participant in winners.items():
            proportion = participant["amount"] / total_winners_bet
            winnings = int(total_pot * proportion)
        
            user_data = core.get_user_data(int(user_id))
            user_data["pieces"] += winnings
        
            user = await core.get_display_user(interaction, int(user_id))
            results.append(f"• {user.mention}: +**{winnings}** pièces")
    
        core.save_data(core.USERS_FILE, core.users_data)
    
        bet["closed"] = True
        bet["winner"] = gagnant
    
        winning_option = bet["choices"][gagnant - 1]
    
        embed = discord.Embed(
            title="🏆 Pari terminé !",
            description=f"**{bet['description']}**\n\nRésultat : **{winning_option}**",
            color=discord.Color.gold()
        )
        embed.add_field(name="Pot total", value=f"💰 {total_pot} pièces", inline=False)
        embed.add_field(name="Gagnants", value="\n".join(results) if results else "Aucun", inline=False)
    
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="paris", description="Voir les paris actifs")
    async def bets(interaction: discord.Interaction):
        active = [bet for bet_id, bet in active_bets.items() if not bet["closed"]]
    
        if not active:
            await interaction.response.send_message("📭 Aucun pari actif pour le moment !")
            return
    
        embed = discord.Embed(
            title="🎲 Paris actifs",
            color=discord.Color.blue()
        )
    
        for bet_id, bet in active_bets.items():
            if not bet["closed"]:
                participants_count = len(bet["participants"])
                total_pot = sum(p["amount"] for p in bet["participants"].values())
            
                embed.add_field(
                    name=f"ID: {bet_id}",
                    value=f"**{bet['description']}**\n✅ {bet['choices'][0]} | ❌ {bet['choices'][1]}\n👥 {participants_count} participants • 💰 {total_pot} pièces",
                    inline=False
                )
    
        await interaction.response.send_message(embed=embed)

