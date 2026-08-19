import discord
from discord import app_commands
from discord.ext import commands

import json
from pathlib import Path
from datetime import datetime, timezone


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PING_FILE = DATA_DIR / "ping.json"


class Ping(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        DATA_DIR.mkdir(parents=True, exist_ok=True)

        if not PING_FILE.exists():
            PING_FILE.write_text("[]", encoding="utf-8")


    @app_commands.command(
        name="ping",
        description="Vérifie si le bot est en ligne."
    )
    async def ping(self, interaction: discord.Interaction):

        await interaction.response.send_message(
            "🤖 Bot en ligne !"
        )

        try:
            with PING_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)

        except (json.JSONDecodeError, FileNotFoundError):
            data = []

        request = {
            "user": {
                "id": interaction.user.id,
                "name": str(interaction.user)
            },
            "guild": {
                "id": interaction.guild.id if interaction.guild else None,
                "name": interaction.guild.name if interaction.guild else None
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        data.append(request)

        # Sauvegarde
        with PING_FILE.open("w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Ping(bot))