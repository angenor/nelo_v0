"""Les deux tables du schéma `annees`, déclarées une fois en SQLAlchemy Core.

Le noyau : de quoi vérifier l'en-tête d'année et composer le contexte. T2a pose les transitions et
le reste de docs/02-domaine.md § 4, sans renommer ni retirer (research.md R-02).
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID

metadata = MetaData(schema="annees")

ETATS = ("preparation", "active", "cloturee", "archivee")

annee_scolaire = Table(
    "annee_scolaire",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("tenant_id", UUID(as_uuid=True), nullable=False),
    # Identifiant vers `tenants.etablissement`, sans clé étrangère : aucune ne traverse un schéma.
    Column("etablissement_id", UUID(as_uuid=True), nullable=False),
    Column("libelle", Text, nullable=False),
    Column("debut", Date, nullable=False),
    Column("fin", Date, nullable=False),
    Column("etat", Text, nullable=False, server_default=text("'preparation'")),
    Column("cree_le", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    CheckConstraint(
        "etat IN ('preparation', 'active', 'cloturee', 'archivee')", name="ck_annee_etat"
    ),
    # L'invariant de docs/02-domaine.md § 4.5, posé dès maintenant pour que T2a le trouve : au
    # plus une année active et une en préparation par établissement.
    Index(
        "uq_annee_active",
        "tenant_id",
        "etablissement_id",
        unique=True,
        postgresql_where=text("etat = 'active'"),
    ),
    Index(
        "uq_annee_preparation",
        "tenant_id",
        "etablissement_id",
        unique=True,
        postgresql_where=text("etat = 'preparation'"),
    ),
    Index("ix_annee_etablissement", "tenant_id", "etablissement_id"),
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
