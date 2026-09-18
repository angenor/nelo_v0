"""Les deux tables du schéma `personnes`, déclarées une fois en SQLAlchemy Core.

Le noyau : les seules colonnes de docs/02-domaine.md § 2.2 que le contexte lit. T3a pose les
autres, sans renommer ni retirer celles-ci (research.md R-02).
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID

metadata = MetaData(schema="personnes")

ETATS_EVENEMENT = ("en_attente", "pris", "traite", "en_echec")

personne = Table(
    "personne",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("tenant_id", UUID(as_uuid=True), nullable=False),
    Column("nom", Text, nullable=False),
    Column("prenoms", Text, nullable=False),
    Column("langue_preferee", Text, nullable=False),
    Column("telephone_principal", Text),
    Column("cree_le", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    CheckConstraint("langue_preferee ~ '^[a-z]{2}$'", name="ck_personne_langue"),
    Index("ix_personne_tenant", "tenant_id"),
)

evenement_outbox = Table(
    "evenement_outbox",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("tenant_id", UUID(as_uuid=True), nullable=False),
    Column("type", Text, nullable=False),
    Column("charge", JSONB, nullable=False),
    Column("ecrit_le", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    Column("etat", Text, nullable=False, server_default=text("'en_attente'")),
    Column("tentatives", Integer, nullable=False, server_default=text("0")),
    Column("pris_le", TIMESTAMP(timezone=True)),
    Column("traite_le", TIMESTAMP(timezone=True)),
    Column("derniere_erreur", Text),
    CheckConstraint(
        "etat IN ('en_attente', 'pris', 'traite', 'en_echec')", name="ck_evenement_etat"
    ),
    Index("ix_evenement_file", "tenant_id", "etat", "ecrit_le", "id"),
)
