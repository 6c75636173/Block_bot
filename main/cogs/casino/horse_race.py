import discord
from discord import app_commands
import random
import asyncio
from datetime import datetime, timedelta

from utils import check_cooldown, set_cooldown  # cooldown persistant — voir utils.py

HORSES = {
    "🐎": {"name": "Thunder", "speed_range": (1, 3)},
    "🏇": {"name": "Lightning", "speed_range": (1, 4)},
    "🐴": {"name": "Spirit", "speed_range": (2, 3)},
    "🦄": {"name": "Mystique", "speed_range": (1, 5)},
    "🎠": {"name": "Carousel", "speed_range": (2, 2)},
}

TRACK_LENGTH = 20

async def setup_horse_race(bot, users_data, save_users_callback):
    
    @bot.tree.command(name="course", description="Course de chevaux — Parie sur un cheval !")
    @app_commands.describe(
        cheval="Choisis ton cheval",
        mise="Combien tu paries (10-1000 pièces)"
    )
    @app_commands.choices(cheval=[
        app_commands.Choice(name="🐎 Thunder (vitesse 1-3)", value="🐎"),
        app_commands.Choice(name="🏇 Lightning (vitesse 1-4)", value="🏇"),
        app_commands.Choice(name="🐴 Spirit (vitesse 2-3)", value="🐴"),
        app_commands.Choice(name="🦄 Mystique (vitesse 1-5)", value="🦄"),
        app_commands.Choice(name="🎠 Carousel (vitesse 2)", value="🎠"),
    ])
    async def race(interaction: discord.Interaction, cheval: str, mise: int):
        user_id = str(interaction.user.id)
        now = datetime.now()
        
        # Cooldown 2 minutes
        dispo, time_left_s = check_cooldown(user_id, "race")
        if not dispo:
            seconds = int(time_left_s)
            await interaction.response.send_message(
                f"⏰ Attends {seconds}s avant la prochaine course !",
                ephemeral=True
            )
            return
        
        if mise < 10 or mise > 1000:
            await interaction.response.send_message(
                "❌ La mise doit être entre 10 et 1000 pièces !",
                ephemeral=True
            )
            return
        
        if users_data[user_id]["pieces"] < mise:
            await interaction.response.send_message(
                f"❌ Pas assez de pièces ! Tu as {users_data[user_id]['pieces']} pièces.",
                ephemeral=True
            )
            return
        
        users_data[user_id]["pieces"] -= mise
        save_users_callback()
        
        set_cooldown(user_id, "race", now + timedelta(minutes=2))
        
        positions = {emoji: 0 for emoji in HORSES.keys()}
        
        embed = discord.Embed(
            title="🏁 COURSE DE CHEVAUX 🏁",
            description=f"**{interaction.user.display_name}** parie **{mise} pièces** sur **{cheval} {HORSES[cheval]['name']}** !",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="🏇 La course commence...",
            value=create_track_visual(positions, cheval),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        winner = None
        round_num = 0
        
        while not winner:
            round_num += 1
            await asyncio.sleep(1.5)
            
            for emoji, horse_data in HORSES.items():
                speed = random.randint(*horse_data["speed_range"])
                positions[emoji] += speed
                
                if positions[emoji] >= TRACK_LENGTH and not winner:
                    winner = emoji
            
            embed = discord.Embed(
                title="🏁 COURSE DE CHEVAUX 🏁",
                description=f"**Round {round_num}** — La course continue...",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🏇 Positions",
                value=create_track_visual(positions, cheval),
                inline=False
            )
            
            await message.edit(embed=embed)
        
        await asyncio.sleep(1)
        
        if winner == cheval:
            # Multiplicateur selon le cheval (plus risqué = plus de gains)
            multipliers = {
                "🐎": 2.5,
                "🏇": 3.0,
                "🐴": 2.0,
                "🦄": 4.0,
                "🎠": 1.5
            }
            
            winnings = int(mise * multipliers[cheval])
            users_data[user_id]["pieces"] += winnings
            save_users_callback()
            
            embed = discord.Embed(
                title="🎉 VICTOIRE ! 🎉",
                description=f"**{cheval} {HORSES[cheval]['name']}** remporte la course !",
                color=discord.Color.green()
            )
            embed.add_field(name="🏆 Résultat final", value=create_track_visual(positions, cheval), inline=False)
            embed.add_field(name="💰 Tu gagnes", value=f"**+{winnings} pièces** (x{multipliers[cheval]})", inline=True)
            embed.add_field(name="💵 Nouveau solde", value=f"{users_data[user_id]['pieces']} pièces", inline=True)
        else:
            embed = discord.Embed(
                title="❌ Défaite !",
                description=f"**{winner} {HORSES[winner]['name']}** remporte la course...",
                color=discord.Color.red()
            )
            embed.add_field(name="🏆 Résultat final", value=create_track_visual(positions, cheval), inline=False)
            embed.add_field(name="💸 Tu perds", value=f"-{mise} pièces", inline=True)
            embed.add_field(name="💵 Nouveau solde", value=f"{users_data[user_id]['pieces']} pièces", inline=True)
        
        await message.edit(embed=embed)

def create_track_visual(positions, bet_on):
    """Crée la piste visuelle de la course"""
    track = ""
    
    sorted_horses = sorted(positions.items(), key=lambda x: x[1], reverse=True)
    
    for emoji, pos in sorted_horses:
        pos = min(pos, TRACK_LENGTH)
        
        progress = "▬" * pos
        remaining = "▬" * (TRACK_LENGTH - pos)
        
        # Marquer le cheval sur lequel on a parié
        marker = "⭐" if emoji == bet_on else ""
        
        track += f"{marker}{emoji} {progress}🏁{remaining} ({pos}/{TRACK_LENGTH})\n"
    
    return track
