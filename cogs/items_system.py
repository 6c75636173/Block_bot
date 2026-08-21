import discord
from discord import app_commands
from discord.ext import commands

from core.database import (
    SPECIAL_ITEMS,
    CRAFTED_ITEMS,
    DROPPABLE_ITEMS,
    set_cooldown,
    check_cooldown
)

from pathlib import Path
import json
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
ITEMS_FILE = DATA_DIR / "items.json"
BUFFS_FILE = DATA_DIR / "buffs.json"

#buffs generate by AI
ITEMS_BUFFS = {
    "🔮 Orbe de Cristal":     {"type": "casino_multiplier",    "value": 1.20, "duration": 60,  "label": "+20% gains casino"},
    "🌟 Étoile Filante":      {"type": "slots_luck",           "value": 1.15, "duration": 60,  "label": "+15% gains slots"},
    "⚔️ Épée Légendaire":     {"type": "crime_multiplier",     "value": 2.0,  "duration": 60,  "label": "x2 gains crime"},
    "👑 Couronne Dorée":      {"type": "cooldown_reducer",     "value": 0.5,  "duration": 120, "label": "Cooldowns -50%"},
    "🎪 Ticket VIP":          {"type": "work_multiplier",      "value": 1.50, "duration": 60,  "label": "+50% gains work"},
    "🏆 Trophée du Champion": {"type": "all_multiplier",       "value": 1.10, "duration": 30,  "label": "+10% tous les gains"},
    "🎭 Masque Mystérieux":   {"type": "crime_multiplier",     "value": 1.30, "duration": 60,  "label": "+30% gains crime"},
    "💎 Diamant Éternel":     {"type": "casino_multiplier",    "value": 1.50, "duration": 30,  "label": "+50% gains casino"},
    "🌈 Épée Diamantée":      {"type": "all_multiplier",       "value": 1.25, "duration": 120, "label": "+25% tous les gains"},
    "🔥 Orbe Enflammé":       {"type": "casino_multiplier",    "value": 2.0,  "duration": 60,  "label": "x2 gains casino"},
    "👑 Masque Royal":        {"type": "all_multiplier",       "value": 1.35, "duration": 90,  "label": "+35% tous les gains"}
}

def load_json(file_path, default=None):

    if default is None:
        default = {}

    if not file_path.exists():
        return default

    try:
        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError:
        return default


def save_json(file_path, data):

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

class ItemsSystem(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        DATA_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        if not ITEMS_FILE.exists():
            save_json(
                ITEMS_FILE,
                {}
            )

        if not BUFFS_FILE.exists():
            save_json(
                BUFFS_FILE,
                {}
            )

    @app_commands.command(
        name="items",
        description="Affiche tes items."
    )
    async def items(
        self,
        interaction: discord.Interaction
    ):

        data = load_json(
            ITEMS_FILE,
            {}
        )

        user_id = str(interaction.user.id)

        inventory = data.get(
            user_id,
            {}
        )

        if not inventory:

            await interaction.response.send_message(
                "🎒 Ton inventaire est vide."
            )

            return

        description = ""

        for item, quantity in inventory.items():

            description += (
                f"{item} **x{quantity}**\n"
            )

        embed = discord.Embed(
            title="🎒 Ton inventaire",
            description=description
        )

        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command(
        name="item_info",
        description="Affiche les informations d'un item."
    )
    @app_commands.describe(
        item="Nom de l'item"
    )
    async def item_info(
        self,
        interaction: discord.Interaction,
        item: str
    ):

        if item not in SPECIAL_ITEMS:

            await interaction.response.send_message(
                "❌ Cet item n'existe pas.",
                ephemeral=True
            )

            return

        info = SPECIAL_ITEMS[item]

        embed = discord.Embed(
            title=item,
            description=info["description"]
        )

        embed.add_field(
            name="💰 Valeur",
            value=f"{info['value']}$"
        )

        if item in ITEMS_BUFFS:

            buff = ITEMS_BUFFS[item]

            embed.add_field(
                name="✨ Effet",
                value=buff["label"],
                inline=False
            )

            embed.add_field(
                name="⏱️ Durée",
                value=f"{buff['duration']} secondes",
                inline=False
            )

        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command(
        name="give_item",
        description="Donne un item à un utilisateur."
    )
    @app_commands.describe(
        user="Utilisateur",
        item="Item à donner",
        quantity="Quantité"
    )
    async def give_item(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        item: str,
        quantity: int = 1
    ):

        if item not in SPECIAL_ITEMS:

            await interaction.response.send_message(
                "❌ Cet item n'existe pas.",
                ephemeral=True
            )

            return

        if quantity <= 0:

            await interaction.response.send_message(
                "❌ La quantité doit être supérieure à 0.",
                ephemeral=True
            )

            return

        data = load_json(
            ITEMS_FILE,
            {}
        )

        user_id = str(user.id)

        data.setdefault(
            user_id,
            {}
        )

        data[user_id][item] = (
            data[user_id].get(item, 0)
            + quantity
        )

        save_json(
            ITEMS_FILE,
            data
        )

        await interaction.response.send_message(
            f"🎁 {user.mention} reçoit "
            f"**{quantity}x {item}** !"
        )

    @app_commands.command(
        name="use_item",
        description="Utilise un item."
    )
    @app_commands.describe(
        item="Item à utiliser"
    )
    async def use_item(
        self,
        interaction: discord.Interaction,
        item: str
    ):

        data = load_json(
            ITEMS_FILE,
            {}
        )

        user_id = str(interaction.user.id)

        inventory = data.get(
            user_id,
            {}
        )

        if inventory.get(item, 0) <= 0:

            await interaction.response.send_message(
                "❌ Tu ne possèdes pas cet item.",
                ephemeral=True
            )

            return

        if item not in ITEMS_BUFFS:

            await interaction.response.send_message(
                "❌ Cet item ne peut pas encore être utilisé.",
                ephemeral=True
            )

            return


        inventory[item] -= 1

        if inventory[item] <= 0:
            del inventory[item]

        save_json(
            ITEMS_FILE,
            data
        )

        buff = ITEMS_BUFFS[item]

        buffs = load_json(
            BUFFS_FILE,
            {}
        )

        buffs.setdefault(
            user_id,
            {}
        )

        end_time = (
            datetime.now()
            + timedelta(
                seconds=buff["duration"]
            )
        )

        buffs[user_id][buff["type"]] = {
            "value": buff["value"],
            "label": buff["label"],
            "expires": end_time.isoformat()
        }

        save_json(
            BUFFS_FILE,
            buffs
        )

        await interaction.response.send_message(
            f"✨ **{item}** utilisé !\n"
            f"Effet : **{buff['label']}**\n"
            f"Durée : **{buff['duration']} secondes**"
        )

async def setup(bot):

    await bot.add_cog(
        ItemsSystem(bot)
    )