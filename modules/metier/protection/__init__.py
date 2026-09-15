"""La protection de l'enfance — **cloisonné**, troisième verrou de la porte P-11.

Aucun paquet ne l'importe, aucun ne le déclare. Rien ne sort de ce module hors de son interface de
service : ni entité, ni accès aux données, ni session. Un compilateur refusait, un test signale —
c'est plus faible, et c'est écrit (ADR 017).
"""

from typing import Protocol


class ServiceProtection(Protocol):
    """L'interface de service, sans opération en T0a."""


__all__ = ["ServiceProtection"]
