import discord
from discord import app_commands
import random
from collections import Counter

SUITS = ["♠️", "♥️", "♦️", "♣️"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RANK_VALUES = {r: i for i, r in enumerate(RANKS, 2)}

active_games = {}

class PokerGame:
    def __init__(self, player1_id, player2_id, buy_in):
        self.players = {
            player1_id: {"hand": [], "bet": buy_in, "folded": False, "name": ""},
            player2_id: {"hand": [], "bet": buy_in, "folded": False, "name": ""}
        }
        self.deck = self.create_deck()
        self.community_cards = []
        self.pot = buy_in * 2
        self.current_phase = "preflop"  # preflop, flop, turn, river, showdown
        self.buy_in = buy_in
        
    def create_deck(self):
        deck = [(rank, suit) for suit in SUITS for rank in RANKS]
        random.shuffle(deck)
        return deck
    
    def deal_hand(self):
        for pid in self.players:
            self.players[pid]["hand"] = [self.deck.pop(), self.deck.pop()]
    
    def deal_flop(self):
        self.community_cards = [self.deck.pop(), self.deck.pop(), self.deck.pop()]
        self.current_phase = "flop"
    
    def deal_turn(self):
        self.community_cards.append(self.deck.pop())
        self.current_phase = "turn"
    
    def deal_river(self):
        self.community_cards.append(self.deck.pop())
        self.current_phase = "river"
    
    def format_card(self, card):
        return f"{card[0]}{card[1]}"
    
    def get_hand_rank(self, cards):
        """Évalue une main de poker (retourne (rank, high_card))"""
        if len(cards) < 5:
            return (0, 0)
        
        from itertools import combinations
        best_hand = (0, [])
        
        for combo in combinations(cards, 5):
            rank = self.evaluate_5_cards(list(combo))
            if rank[0] > best_hand[0]:
                best_hand = rank
        
        return best_hand
    
    def evaluate_5_cards(self, cards):
        """Évalue exactement 5 cartes"""
        ranks = [RANK_VALUES[c[0]] for c in cards]
        suits = [c[1] for c in cards]
        
        rank_counts = Counter(ranks)
        is_flush = len(set(suits)) == 1
        sorted_ranks = sorted(ranks, reverse=True)
        
        is_straight = False
        if sorted_ranks == list(range(sorted_ranks[0], sorted_ranks[0] - 5, -1)):
            is_straight = True
        # Cas spécial : A-2-3-4-5
        elif sorted_ranks == [14, 5, 4, 3, 2]:
            is_straight = True
            sorted_ranks = [5, 4, 3, 2, 1]
        
        # Quinte flush royale
        if is_straight and is_flush and sorted_ranks[0] == 14:
            return (10, sorted_ranks)
        
        # Quinte flush
        if is_straight and is_flush:
            return (9, sorted_ranks)
        
        # Carré
        if 4 in rank_counts.values():
            quad = [r for r, c in rank_counts.items() if c == 4][0]
            kicker = [r for r in sorted_ranks if r != quad][0]
            return (8, [quad, kicker])
        
        # Full
        if 3 in rank_counts.values() and 2 in rank_counts.values():
            trip = [r for r, c in rank_counts.items() if c == 3][0]
            pair = [r for r, c in rank_counts.items() if c == 2][0]
            return (7, [trip, pair])
        
        # Couleur
        if is_flush:
            return (6, sorted_ranks)
        
        # Suite
        if is_straight:
            return (5, sorted_ranks)
        
        # Brelan
        if 3 in rank_counts.values():
            trip = [r for r, c in rank_counts.items() if c == 3][0]
            kickers = sorted([r for r in sorted_ranks if r != trip], reverse=True)
            return (4, [trip] + kickers)
        
        # Deux paires
        if list(rank_counts.values()).count(2) == 2:
            pairs = sorted([r for r, c in rank_counts.items() if c == 2], reverse=True)
            kicker = [r for r in sorted_ranks if r not in pairs][0]
            return (3, pairs + [kicker])
        
        # Paire
        if 2 in rank_counts.values():
            pair = [r for r, c in rank_counts.items() if c == 2][0]
            kickers = sorted([r for r in sorted_ranks if r != pair], reverse=True)
            return (2, [pair] + kickers)
        
        # Carte haute
        return (1, sorted_ranks)
    
    def get_hand_name(self, rank):
        names = {
            10: "Quinte Flush Royale 👑",
            9: "Quinte Flush",
            8: "Carré",
            7: "Full",
            6: "Couleur",
            5: "Suite",
            4: "Brelan",
            3: "Double Paire",
            2: "Paire",
            1: "Carte Haute"
        }
        return names.get(rank, "Main inconnue")

async def setup_poker(bot, users_data, save_users_callback):
    
    @bot.tree.command(name="poker", description="Défie quelqu'un au poker Texas Hold'em")
    @app_commands.describe(
        adversaire="Le joueur à défier",
        mise="Buy-in (10-1000 pièces)"
    )
    async def poker(interaction: discord.Interaction, adversaire: discord.Member, mise: int):
        user_id = str(interaction.user.id)
        opponent_id = str(adversaire.id)
        
        if adversaire.id == interaction.user.id:
            await interaction.response.send_message("❌ Tu ne peux pas jouer contre toi-même !", ephemeral=True)
            return
        
        if adversaire.bot:
            await interaction.response.send_message("❌ Tu ne peux pas jouer contre un bot !", ephemeral=True)
            return
        
        if mise < 10 or mise > 1000:
            await interaction.response.send_message("❌ La mise doit être entre 10 et 1000 pièces !", ephemeral=True)
            return
        
        if users_data[user_id]["pieces"] < mise:
            await interaction.response.send_message(
                f"❌ Pas assez de pièces ! Tu as {users_data[user_id]['pieces']} pièces.",
                ephemeral=True
            )
            return
        
        if opponent_id not in users_data or users_data[opponent_id]["pieces"] < mise:
            await interaction.response.send_message(
                f"❌ {adversaire.display_name} n'a pas assez de pièces !",
                ephemeral=True
            )
            return
        
        if user_id in active_games or opponent_id in active_games:
            await interaction.response.send_message("❌ L'un de vous est déjà en partie !", ephemeral=True)
            return
        
        game = PokerGame(user_id, opponent_id, mise)
        game.players[user_id]["name"] = interaction.user.display_name
        game.players[opponent_id]["name"] = adversaire.display_name
        
        class AcceptView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
            
            @discord.ui.button(label="✅ Accepter", style=discord.ButtonStyle.success)
            async def accept(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                if btn_interaction.user.id != adversaire.id:
                    await btn_interaction.response.send_message("❌ Ce défi ne te concerne pas !", ephemeral=True)
                    return
                
                users_data[user_id]["pieces"] -= mise
                users_data[opponent_id]["pieces"] -= mise
                save_users_callback()
                
                game.deal_hand()
                active_games[user_id] = game
                active_games[opponent_id] = game
                
                await start_poker_game(btn_interaction, game, user_id, opponent_id)
            
            @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.danger)
            async def refuse(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                if btn_interaction.user.id != adversaire.id:
                    await btn_interaction.response.send_message("❌ Ce défi ne te concerne pas !", ephemeral=True)
                    return
                
                await btn_interaction.response.edit_message(
                    content=f"❌ {adversaire.mention} a refusé le défi !",
                    embed=None,
                    view=None
                )
        
        embed = discord.Embed(
            title="🃏 Défi Poker Texas Hold'em",
            description=f"**{interaction.user.mention}** défie **{adversaire.mention}** au poker !",
            color=discord.Color.blue()
        )
        embed.add_field(name="💰 Buy-in", value=f"{mise} pièces chacun", inline=True)
        embed.add_field(name="🏆 Pot total", value=f"{mise * 2} pièces", inline=True)
        
        await interaction.response.send_message(content=adversaire.mention, embed=embed, view=AcceptView())

async def start_poker_game(interaction, game, p1_id, p2_id):
    """Lance la partie de poker"""
    embed = create_poker_embed(game, p1_id, p2_id)
    view = create_poker_view(game, p1_id, p2_id)
    
    await interaction.response.edit_message(content=None, embed=embed, view=view)

def create_poker_embed(game, p1_id, p2_id):
    """Crée l'embed du poker"""
    p1 = game.players[p1_id]
    p2 = game.players[p2_id]
    
    phase_names = {
        "preflop": "🎴 PRE-FLOP",
        "flop": "🃏 FLOP",
        "turn": "🎰 TURN",
        "river": "🌊 RIVER",
        "showdown": "🏆 SHOWDOWN"
    }
    
    embed = discord.Embed(
        title="🃏 POKER TEXAS HOLD'EM",
        description=phase_names[game.current_phase],
        color=discord.Color.gold()
    )
    
    if game.community_cards:
        cards_display = " ".join([game.format_card(c) for c in game.community_cards])
        embed.add_field(name="🎴 Table", value=cards_display, inline=False)
    
    embed.add_field(name="💰 Pot", value=f"{game.pot} pièces", inline=True)
    
    # Joueurs (sans montrer les cartes avant showdown)
    if game.current_phase != "showdown":
        status1 = "❌ FOLD" if p1["folded"] else "✅"
        status2 = "❌ FOLD" if p2["folded"] else "✅"
        embed.add_field(name=f"{status1} {p1['name']}", value="🎴 🎴", inline=True)
        embed.add_field(name=f"{status2} {p2['name']}", value="🎴 🎴", inline=True)
    
    return embed

def create_poker_view(game, p1_id, p2_id):
    """Crée les boutons de jeu"""
    
    class PokerView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=180)
        
        @discord.ui.button(label="✅ Check", style=discord.ButtonStyle.success)
        async def check_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
            uid = str(interaction.user.id)
            if uid not in [p1_id, p2_id]:
                await interaction.response.send_message("❌ Tu n'es pas dans cette partie !", ephemeral=True)
                return
            
            await next_phase(interaction, game, p1_id, p2_id)
        
        @discord.ui.button(label="❌ Fold", style=discord.ButtonStyle.danger)
        async def fold_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
            uid = str(interaction.user.id)
            if uid not in [p1_id, p2_id]:
                await interaction.response.send_message("❌ Tu n'es pas dans cette partie !", ephemeral=True)
                return
            
            game.players[uid]["folded"] = True
            winner_id = p2_id if uid == p1_id else p1_id
            
            await end_game(interaction, game, winner_id, p1_id, p2_id, fold=True)
    
    return PokerView()

async def next_phase(interaction, game, p1_id, p2_id):
    """Passe à la phase suivante du poker"""
    if game.current_phase == "preflop":
        game.deal_flop()
    elif game.current_phase == "flop":
        game.deal_turn()
    elif game.current_phase == "turn":
        game.deal_river()
    elif game.current_phase == "river":
        game.current_phase = "showdown"
        await showdown(interaction, game, p1_id, p2_id)
        return
    
    embed = create_poker_embed(game, p1_id, p2_id)
    view = create_poker_view(game, p1_id, p2_id)
    
    await interaction.response.edit_message(embed=embed, view=view)

async def showdown(interaction, game, p1_id, p2_id):
    """Révèle les cartes et détermine le gagnant"""
    p1_cards = game.players[p1_id]["hand"] + game.community_cards
    p2_cards = game.players[p2_id]["hand"] + game.community_cards
    
    p1_rank = game.get_hand_rank(p1_cards)
    p2_rank = game.get_hand_rank(p2_cards)
    
    if p1_rank > p2_rank:
        winner_id = p1_id
    elif p2_rank > p1_rank:
        winner_id = p2_id
    else:
        winner_id = None  # Égalité
    
    await end_game(interaction, game, winner_id, p1_id, p2_id, p1_rank, p2_rank)

async def end_game(interaction, game, winner_id, p1_id, p2_id, p1_rank=None, p2_rank=None, fold=False):
    """Termine la partie"""
    from block_bot import users_data, save_data, USERS_FILE
    
    if p1_id in active_games:
        del active_games[p1_id]
    if p2_id in active_games:
        del active_games[p2_id]
    
    p1_name = game.players[p1_id]["name"]
    p2_name = game.players[p2_id]["name"]
    
    embed = discord.Embed(
        title="🏆 FIN DE PARTIE",
        color=discord.Color.gold()
    )
    
    if game.community_cards:
        cards_display = " ".join([game.format_card(c) for c in game.community_cards])
        embed.add_field(name="🎴 Table", value=cards_display, inline=False)
    
    p1_hand = " ".join([game.format_card(c) for c in game.players[p1_id]["hand"]])
    p2_hand = " ".join([game.format_card(c) for c in game.players[p2_id]["hand"]])
    
    if fold:
        folder = p1_name if game.players[p1_id]["folded"] else p2_name
        embed.description = f"❌ **{folder}** a abandonné !"
        embed.add_field(name=f"🎴 {p1_name}", value=p1_hand, inline=True)
        embed.add_field(name=f"🎴 {p2_name}", value=p2_hand, inline=True)
    elif winner_id:
        winner_name = game.players[winner_id]["name"]
        winner_hand_name = game.get_hand_name(p1_rank[0] if winner_id == p1_id else p2_rank[0])
        
        embed.description = f"🎉 **{winner_name}** remporte {game.pot} pièces avec **{winner_hand_name}** !"
        embed.add_field(
            name=f"🎴 {p1_name}",
            value=f"{p1_hand}\n{game.get_hand_name(p1_rank[0])}",
            inline=True
        )
        embed.add_field(
            name=f"🎴 {p2_name}",
            value=f"{p2_hand}\n{game.get_hand_name(p2_rank[0])}",
            inline=True
        )
        
        users_data[winner_id]["pieces"] += game.pot
        save_data(USERS_FILE, users_data)
    else:
        embed.description = "🤝 Égalité ! Le pot est partagé."
        split = game.pot // 2
        users_data[p1_id]["pieces"] += split
        users_data[p2_id]["pieces"] += split
        save_data(USERS_FILE, users_data)
        
        embed.add_field(
            name=f"🎴 {p1_name}",
            value=f"{p1_hand}\n{game.get_hand_name(p1_rank[0])}",
            inline=True
        )
        embed.add_field(
            name=f"🎴 {p2_name}",
            value=f"{p2_hand}\n{game.get_hand_name(p2_rank[0])}",
            inline=True
        )
    
    await interaction.response.edit_message(embed=embed, view=None)
