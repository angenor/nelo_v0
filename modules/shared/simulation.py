"""Les modes d'une dépendance externe simulée : un succès, et les quatre manières d'échouer."""

from enum import StrEnum


class ModeSimulation(StrEnum):
    SUCCES = "SUCCES"
    ACCUSE_EN_RETARD = "ACCUSE_EN_RETARD"
    ACCUSE_EN_DOUBLE = "ACCUSE_EN_DOUBLE"
    JAMAIS_RECU = "JAMAIS_RECU"
    INDISPONIBLE = "INDISPONIBLE"
