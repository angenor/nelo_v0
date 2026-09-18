"""Les gabarits des messages courts, rédigés pour le message court (ADR 013, research.md R-17).

Trois gabarits, dans les deux langues du socle, écrits ensemble : une clé qui n'existerait que
dans une langue serait une personne qui reçoit un message vide. La langue est celle de la personne
du compte ; `fr` avant tout compte, et pour toute langue que le produit ne parle pas encore.

La longueur se vérifie **au dépôt**, par un test qui rend chaque gabarit avec les valeurs les plus
longues que le produit admet, et non à l'envoi : un message tronqué chez la personne est déjà trop
tard. T4a reprendra ces gabarits dans `modele_message` ; ils sont écrits pour être déplacés, pas
réécrits.
"""

import json
from functools import cache
from pathlib import Path

DOSSIER = Path(__file__).parent / "messages"
LANGUE_DE_SECOURS = "fr"
# Un message court tient sur un segment GSM : au-delà, l'opérateur en facture deux et les
# passerelles les recomposent mal.
LONGUEUR_MAXIMALE = 160


@cache
def _messages(langue: str) -> dict[str, str]:
    return json.loads((DOSSIER / f"{langue}.json").read_text(encoding="utf-8"))


def langues() -> list[str]:
    return sorted(chemin.stem for chemin in DOSSIER.glob("*.json"))


def rendre(cle: str, langue: str, **params: object) -> str:
    """Le texte du gabarit dans cette langue, ses paramètres posés.

    Une langue inconnue retombe sur `fr` : mieux vaut un message lisible dans une autre langue
    qu'aucun message.
    """
    if langue not in langues():
        langue = LANGUE_DE_SECOURS
    gabarit = _messages(langue).get(cle)
    if gabarit is None:
        raise KeyError(f"aucun gabarit « {cle} » en {langue}")
    return gabarit.format(**params)
