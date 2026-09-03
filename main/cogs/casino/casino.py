import discord
from discord import app_commands
import random

import core


async def setup_casino(bot):

    # ========== COMMANDES MINI-JEUX ==========
    @bot.tree.command(name="pile_ou_face", description="Pile ou face - Parie tes pièces !")
    @app_commands.describe(mise="Nombre de pièces à miser", choix="pile ou face")
    async def coinflip(interaction: discord.Interaction, mise: int, choix: str):
        user_data = core.get_user_data(interaction.user.id)
        choix = choix.lower()
    
        if choix not in ["pile", "face"]:
            await interaction.response.send_message("❌ Choisis 'pile' ou 'face' !", ephemeral=True)
            return
    
        if mise < 10:
            await interaction.response.send_message("❌ Mise minimum : 10 pièces !", ephemeral=True)
            return
    
        if user_data["pieces"] < mise:
            await interaction.response.send_message(f"❌ Tu n'as que {user_data['pieces']} pièces !", ephemeral=True)
            return
    
        result = random.choice(["pile", "face"])
        won = (result == choix)
    
        if won:
            user_data["pieces"] += mise
            color = discord.Color.green()
            emoji = "🎉"
            message = f"C'est **{result}** ! Tu gagnes **{mise} pièces** !"
        
            completed_challenge = core.update_challenge_progress(interaction.user.id, "coinflip_wins", 1)
            if completed_challenge:
                await core.complete_challenge(str(interaction.user.id), completed_challenge, interaction.channel)
        else:
            user_data["pieces"] -= mise
            color = discord.Color.red()
            emoji = "😢"
            message = f"C'est **{result}** ! Tu perds **{mise} pièces**..."
    
        core.save_data(core.USERS_FILE, core.users_data)
    
        completed_challenge = core.update_challenge_progress(interaction.user.id, "casino_plays", 1)
        if completed_challenge:
            await core.complete_challenge(str(interaction.user.id), completed_challenge, interaction.channel)
    
        if not won:
            completed_challenge = core.update_challenge_progress(interaction.user.id, "spent", mise)
            if completed_challenge:
                await core.complete_challenge(str(interaction.user.id), completed_challenge, interaction.channel)
    
        embed = discord.Embed(
            title=f"{emoji} Pile ou Face",
            description=f"Tu as choisi : **{choix}**\n{message}",
            color=color
        )
        embed.add_field(name="Solde", value=f"💰 {user_data['pieces']} pièces")
    
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="des", description="Lance un ou plusieurs dés")
    @app_commands.describe(nombre="Nombre de dés (1-10)", faces="Nombre de faces (4, 6, 8, 12, 20)")
    async def dice(interaction: discord.Interaction, nombre: int = 1, faces: int = 6):
        if nombre < 1 or nombre > 10:
            await interaction.response.send_message("❌ Tu peux lancer entre 1 et 10 dés !", ephemeral=True)
            return
    
        if faces not in [4, 6, 8, 12, 20]:
            await interaction.response.send_message("❌ Choisis 4, 6, 8, 12 ou 20 faces !", ephemeral=True)
            return
    
        results = [random.randint(1, faces) for _ in range(nombre)]
        total = sum(results)
    
        dice_emoji = "🎲"
        results_str = " + ".join([f"**{r}**" for r in results])
    
        embed = discord.Embed(
            title=f"{dice_emoji} Lancé de dés",
            description=f"{nombre}d{faces}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Résultats", value=results_str, inline=False)
        embed.add_field(name="Total", value=f"🎯 **{total}**", inline=False)
    
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="roulette", description="Roulette russe - 1 chance sur 5 de mourir, x5 la mise si tu survis")
    @app_commands.describe(mise="Coins à miser (max 100)")
    async def roulette(interaction: discord.Interaction, mise: int):
        user_data = core.get_user_data(interaction.user.id)

        if mise < 10:
            await interaction.response.send_message("❌ Mise minimum : 10 pièces !", ephemeral=True)
            return

        if mise > 100:
            await interaction.response.send_message("❌ Mise maximum : 100 pièces pour la roulette russe !", ephemeral=True)
            return

        if user_data["pieces"] < mise:
            await interaction.response.send_message(f"❌ Tu n'as que {user_data['pieces']} pièces !", ephemeral=True)
            return

        user_data["pieces"] -= mise
        survived = random.randint(1, 5) != 1

        completed_challenge = core.update_challenge_progress(interaction.user.id, "casino_plays", 1)

        if survived:
            winnings = mise * 5
            user_data["pieces"] += winnings
            embed = discord.Embed(
                title="🎉 *CLICK* Tu survis !",
                description=f"Le barillet était vide.\n\nTu gagnes **{winnings} pièces** (x5) !",
                color=discord.Color.gold()
            )
            embed.add_field(name="💰 Solde", value=f"{user_data['pieces']} pièces")
        else:
            embed = discord.Embed(
                title="💀 *BANG !*",
                description=f"Le coup est parti !\n\nTu perds ta mise : **-{mise} pièces**",
                color=discord.Color.dark_red()
            )
            embed.add_field(name="💰 Solde", value=f"{user_data['pieces']} pièces")
            completed_spent = core.update_challenge_progress(interaction.user.id, "spent", mise)
            if completed_spent:
                completed_challenge = completed_spent

        core.save_data(core.USERS_FILE, core.users_data)

        embed.add_field(
            name="📜 Règles",
            value="1 chance sur 5 de perdre toute la mise • x5 la mise si tu survis",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

        if completed_challenge:
            await core.complete_challenge(str(interaction.user.id), completed_challenge, interaction.channel)

    # ========== ROULETTE SOVIÉTIQUE ==========

    @bot.tree.command(name="roulette_sovietique", description="Roulette soviétique - 5 chances sur 6 de mourir, x2.5 si survie !")
    @app_commands.describe(mise="Coins à miser (max 1000)")
    async def soviet_roulette(interaction: discord.Interaction, mise: int):
        user_data = core.get_user_data(interaction.user.id)
    
        if mise < 50:
            await interaction.response.send_message("❌ Mise minimum : 50 pièces !", ephemeral=True)
            return
    
        if mise > 1000:
            await interaction.response.send_message("❌ Mise maximum : 1000 pièces !", ephemeral=True)
            return
    
        if user_data["pieces"] < mise:
            await interaction.response.send_message(f"❌ Tu n'as que {user_data['pieces']} pièces !", ephemeral=True)
            return
    
        await interaction.response.send_message("☭ *Le barillet soviétique tourne... 5 balles sur 6...*")
        await asyncio.sleep(2)
    
        survived = random.randint(1, 6) == 6
    
        completed_challenge = core.update_challenge_progress(interaction.user.id, "casino_plays", 1)
    
        if survived:
            winnings = int(mise * 2.5)
            user_data["pieces"] += winnings
            core.save_data(core.USERS_FILE, core.users_data)
        
            embed = discord.Embed(
                title="☭ *CLICK* MIRACLE SOVIÉTIQUE !",
                description=f"Tu as survécu contre toute attente !\n\nTu gagnes **{winnings} pièces** (x2.5) !",
                color=discord.Color.gold()
            )
            embed.add_field(name="💰 Solde", value=f"{user_data['pieces']} pièces")
            embed.set_footer(text="☭ La chance du prolétariat !")
    
        else:
            user_data["pieces"] -= mise
            core.save_data(core.USERS_FILE, core.users_data)
        
            completed_challenge2 = core.update_challenge_progress(interaction.user.id, "spent", mise)
        
            embed = discord.Embed(
                title="💀 *BANG !*",
                description=f"Le Goulag t'attend !\n\nTu perds **{mise} pièces** !",
                color=discord.Color.dark_red()
            )
            embed.add_field(name="💰 Solde", value=f"{user_data['pieces']} pièces")
            embed.set_footer(text="☭ Pour Staline !")
        
            if completed_challenge2:
                await core.complete_challenge(str(interaction.user.id), completed_challenge2, interaction.channel)
    
        await interaction.edit_original_response(content=None, embed=embed)
    
        if completed_challenge:
            await core.complete_challenge(str(interaction.user.id), completed_challenge, interaction.channel)

    @bot.tree.command(name="blackjack", description="Joue au blackjack contre le bot")
    @app_commands.describe(mise="Coins à miser")
    async def blackjack(interaction: discord.Interaction, mise: int):
        user_data = core.get_user_data(interaction.user.id)
    
        if mise < 50:
            await interaction.response.send_message("❌ Mise minimum : 50 pièces !", ephemeral=True)
            return
    
        if user_data["pieces"] < mise:
            await interaction.response.send_message(f"❌ Tu n'as que {user_data['pieces']} pièces !", ephemeral=True)
            return
    
        deck = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'] * 4
        random.shuffle(deck)
    
        def card_value(card):
            if card in ['J', 'Q', 'K']:
                return 10
            elif card == 'A':
                return 11
            return int(card)
    
        def calculate_hand(hand):
            value = sum(card_value(card) for card in hand)
            aces = hand.count('A')
            while value > 21 and aces:
                value -= 10
                aces -= 1
            return value
    
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]
    
        player_value = calculate_hand(player_hand)
        dealer_value = calculate_hand(dealer_hand)
    
        embed = discord.Embed(title="🃏 Blackjack", color=discord.Color.blue())
        embed.add_field(
            name="Ta main",
            value=f"{' '.join(player_hand)} = **{player_value}**",
            inline=False
        )
        embed.add_field(
            name="Main du croupier",
            value=f"{dealer_hand[0]} 🎴",
            inline=False
        )
    
        completed_challenge = core.update_challenge_progress(interaction.user.id, "casino_plays", 1)
    
        if player_value == 21:
            winnings = int(mise * 2.5)
            user_data["pieces"] += winnings - mise
            core.save_data(core.USERS_FILE, core.users_data)
            embed.add_field(name="🎉 BLACKJACK !", value=f"Tu gagnes {winnings} pièces !", inline=False)
            await interaction.response.send_message(embed=embed)
        
            if completed_challenge:
                await core.complete_challenge(str(interaction.user.id), completed_challenge, interaction.channel)
            return
    
        embed.set_footer(text="Utilise les boutons pour jouer")
    
        class BlackjackView(discord.ui.View):
            def __init__(self, player_id):
                super().__init__(timeout=60)
                self.value = None
                self.player_id = player_id
        
            @discord.ui.button(label="Tirer (Hit)", style=discord.ButtonStyle.primary)
            async def hit(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id != self.player_id:
                    await button_interaction.response.send_message("❌ Ce n'est pas ton jeu !", ephemeral=True)
                    return
            
                player_hand.append(deck.pop())
                player_value = calculate_hand(player_hand)
            
                if player_value > 21:
                    user_data["pieces"] -= mise
                    core.save_data(core.USERS_FILE, core.users_data)
                
                    completed = core.update_challenge_progress(self.player_id, "spent", mise)
                
                    embed = discord.Embed(title="🃏 Blackjack - Résultat", color=discord.Color.red())
                    embed.add_field(name="Ta main", value=f"{' '.join(player_hand)} = **{player_value}**", inline=False)
                    embed.add_field(name="💥 BUST !", value=f"Tu perds {mise} pièces", inline=False)
                    embed.add_field(name="Solde", value=f"💰 {user_data['pieces']} pièces")
                
                    await button_interaction.response.edit_message(embed=embed, view=None)
                    self.stop()
                
                    if completed:
                        await core.complete_challenge(str(self.player_id), completed, button_interaction.channel)
                else:
                    embed = discord.Embed(title="🃏 Blackjack", color=discord.Color.blue())
                    embed.add_field(name="Ta main", value=f"{' '.join(player_hand)} = **{player_value}**", inline=False)
                    embed.add_field(name="Main du croupier", value=f"{dealer_hand[0]} 🎴", inline=False)
                    await button_interaction.response.edit_message(embed=embed)
        
            @discord.ui.button(label="Rester (Stand)", style=discord.ButtonStyle.success)
            async def stand(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id != self.player_id:
                    await button_interaction.response.send_message("❌ Ce n'est pas ton jeu !", ephemeral=True)
                    return
            
                dealer_value = calculate_hand(dealer_hand)
                while dealer_value < 17:
                    dealer_hand.append(deck.pop())
                    dealer_value = calculate_hand(dealer_hand)
            
                player_value = calculate_hand(player_hand)
            
                embed = discord.Embed(title="🃏 Blackjack - Résultat", color=discord.Color.blue())
                embed.add_field(name="Ta main", value=f"{' '.join(player_hand)} = **{player_value}**", inline=False)
                embed.add_field(name="Main du croupier", value=f"{' '.join(dealer_hand)} = **{dealer_value}**", inline=False)
            
                if dealer_value > 21 or player_value > dealer_value:
                    winnings = mise * 2
                    user_data["pieces"] += winnings - mise
                    embed.add_field(name="✅ Victoire !", value=f"Tu gagnes {winnings} pièces !", inline=False)
                    embed.color = discord.Color.green()
                elif player_value == dealer_value:
                    embed.add_field(name="🤝 Égalité", value="Tu récupères ta mise", inline=False)
                    embed.color = discord.Color.gold()
                else:
                    user_data["pieces"] -= mise
                
                    completed = core.update_challenge_progress(self.player_id, "spent", mise)
                
                    embed.add_field(name="❌ Défaite", value=f"Tu perds {mise} pièces", inline=False)
                    embed.color = discord.Color.red()
                
                    if completed:
                        await core.complete_challenge(str(self.player_id), completed, button_interaction.channel)
            
                core.save_data(core.USERS_FILE, core.users_data)
                embed.add_field(name="Solde", value=f"💰 {user_data['pieces']} pièces")
            
                await button_interaction.response.edit_message(embed=embed, view=None)
                self.stop()
    
        view = BlackjackView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)
    
        if completed_challenge:
            await core.complete_challenge(str(interaction.user.id), completed_challenge, interaction.channel)

