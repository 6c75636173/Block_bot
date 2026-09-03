"""
utils/__init__.py — Fait de utils/ un package qui se comporte exactement comme l'ancien
utils.py monolithique : `from utils import load_data, SPECIAL_ITEMS, ...` continue de
fonctionner sans qu'aucun fichier ailleurs dans le projet n'ait besoin d'être modifié.
"""

from .helpers import *
from .permissions import *
from .embeds import *
