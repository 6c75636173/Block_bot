import discord
from discord import app_commands
import random


async def setup_fun(bot):

    # ========== GROUPE /fun ==========
    fun_group = app_commands.Group(name="fun", description="Commandes fun et sociales")
    bot.tree.add_command(fun_group)

    @fun_group.command(name="calin", description="Fais un câlin à quelqu'un")
    @app_commands.describe(membre="La personne à câliner")
    async def hug(interaction: discord.Interaction, membre: discord.Member):
        if membre.id == interaction.user.id:
            await interaction.response.send_message("🤗 Tu te fais un auto-câlin... Mignon !")
            return
    
        messages = [
            f"🤗 {interaction.user.mention} fait un gros câlin à {membre.mention} !",
            f"💕 Aww ! {interaction.user.mention} serre {membre.mention} dans ses bras !",
            f"🫂 {interaction.user.mention} et {membre.mention} partagent un moment wholesome !",
        ]
    
        await interaction.response.send_message(random.choice(messages))

    @fun_group.command(name="clasher", description="Insulte gentiment quelqu'un")
    @app_commands.describe(membre="La victime")
    async def roast(interaction: discord.Interaction, membre: discord.Member = None):
        target = membre or interaction.user
    
        roasts = [
            f"{target.mention} est tellement nul qu'il ferait perdre une IA à Pierre-Papier-Ciseaux",
            f"{target.mention} a le QI d'une huître... et encore, l'huître est vexée",
            f"Si {target.mention} était un pokémon, ce serait un Magicarpe niveau 1",
            f"{target.mention} est la raison pour laquelle y'a des instructions sur les shampoings",
            f"{target.mention} a déjà perdu une bataille de regards contre un poisson rouge",
            f"Le Wi-Fi se déconnecte quand {target.mention} entre dans la pièce",
            f"{target.mention} est comme Internet Explorer : lent et personne ne l'utilise",
            f"Si la médiocrité était un art, {target.mention} serait Picasso",
        ]
    
        await interaction.response.send_message(f"🔥 {random.choice(roasts)}")

    @fun_group.command(name="boule_magique", description="Pose une question à la boule magique")
    @app_commands.describe(question="Ta question")
    async def eightball(interaction: discord.Interaction, question: str):
        responses = [
            "✅ Oui, absolument !",
            "✅ Sans aucun doute",
            "✅ C'est certain",
            "✅ Très probable",
            "🤔 Peut-être",
            "🤔 Demande à nouveau plus tard",
            "🤔 Je ne peux pas prédire maintenant",
            "🤔 Concentre-toi et redemande",
            "❌ N'y compte pas",
            "❌ Très peu probable",
            "❌ Non",
            "❌ Certainement pas",
        ]
    
        embed = discord.Embed(title="🎱 Boule Magique", color=discord.Color.purple())
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Réponse", value=random.choice(responses), inline=False)
    
        await interaction.response.send_message(embed=embed)

    @fun_group.command(name="paff", description="Mesure ton paff (virtuel évidemment)")
    async def pp(interaction: discord.Interaction, membre: discord.Member = None):
        target = membre or interaction.user
    
        random.seed(target.id)
        size = random.randint(1, 30)
        random.seed()
    
        pp = "8" + "=" * size + "D"
    
        await interaction.response.send_message(f"🍆 PP de {target.mention} :\n`{pp}`\n**{size}cm**")

    return fun_group
