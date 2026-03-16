"""
Module de chargement de la configuration de scoring GTFS.
Charge le fichier scoring_config.json une seule fois au démarrage
et expose SCORING_CONFIG pour être importé dans les fichiers d'audit.
"""
import json
import os

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "scoring_config.json")

def load_scoring_config(path: str = _CONFIG_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

SCORING_CONFIG = load_scoring_config()