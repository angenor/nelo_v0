"""Les constantes de sécurité du produit, en un seul endroit (FR-060).

Une valeur qui décide d'un refus ne se cherche pas dans dix fichiers. Ce module ne lit **aucune
configuration** : ce sont des choix de produit, pas des réglages de déploiement. Ce qu'un
établissement peut régler passe par le catalogue de paramètres (`securite.*`), jamais par ici.

Les valeurs de ce fichier restent à confirmer par l'utilisateur (Q30, au journal) ; elles sont
celles de la spécification.
"""

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True, slots=True)
class PolitiqueSecurite:
    """Ce que le produit tient pour vrai sur les codes, les sessions et les appareils."""

    # Le code à usage unique reçu par SMS.
    OTP_LONGUEUR: int = 6
    OTP_VALIDITE: timedelta = timedelta(minutes=10)
    OTP_TENTATIVES: int = 5
    OTP_RENVOI: timedelta = timedelta(seconds=60)
    OTP_PAR_HEURE_PAR_NUMERO: int = 5
    OTP_PAR_HEURE_PAR_CLIENT: int = 20

    # Le code personnel, lié à un appareil connu.
    PIN_LONGUEUR: int = 4
    DISPENSE_PIN_COURANT: timedelta = timedelta(minutes=10)

    # La session et son jeton.
    FENETRE_CONCURRENCE_REFRESH: timedelta = timedelta(seconds=10)
    JETON_ACCES: timedelta = timedelta(minutes=60)


POLITIQUE = PolitiqueSecurite()
