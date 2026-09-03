"""
core/__init__.py — Fait de core/ un package qui se comporte exactement comme l'ancien
core.py monolithique : `import core` puis `core.users_data`, `core.get_user_data(...)`,
etc. continuent de fonctionner sans qu'aucun fichier ailleurs dans le projet n'ait besoin
d'être modifié. Le contenu est simplement réparti en 3 fichiers pour plus de clarté :
config.py (constantes), database.py (données chargées), bot.py (bot + fonctions liées).
"""

from .config import *
from .database import *
from .bot import *
