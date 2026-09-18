"""Les trois tables du schéma `habilitations`, déclarées une fois en SQLAlchemy Core.

Le compte, l'affectation et l'outbox du module. `compte.personne_id`, `affectation.annee_id` et
`affectation.etablissement_id` sont des identifiants sans clé étrangère : aucune ne traverse un
schéma (P-01). La seule clé étrangère est intra-schéma, de l'affectation vers le compte.
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID

metadata = MetaData(schema="habilitations")

STATUTS = ("invite", "actif", "suspendu")

compte = Table(
    "compte",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("tenant_id", UUID(as_uuid=True), nullable=False),
    # Identifiant vers `personnes.personne`, sans clé étrangère.
    Column("personne_id", UUID(as_uuid=True), nullable=False),
    # Le numéro normalisé E.164, jamais une autre forme. **Aucune unicité** : le partage
    # familial d'un numéro est permis (US8), et se déclare à la création.
    Column("identifiant", Text, nullable=False),
    Column("statut", Text, nullable=False, server_default=text("'invite'")),
    # Argon2id du code personnel ; NULL vaut absent. Jamais renvoyée par une route.
    Column("pin_empreinte", Text),
    Column("pin_verrouille_le", TIMESTAMP(timezone=True)),
    # SHA-256 du jeton du lien en cours ; NULL vaut aucun lien valide.
    Column("invitation_empreinte", Text),
    Column("invitation_expire_le", TIMESTAMP(timezone=True)),
    Column("invite_le", TIMESTAMP(timezone=True)),
    Column("derniere_connexion", TIMESTAMP(timezone=True)),
    Column("cree_le", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    CheckConstraint("statut IN ('invite', 'actif', 'suspendu')", name="ck_compte_statut"),
    UniqueConstraint("tenant_id", "personne_id", name="uq_compte_personne"),
    Index("ix_compte_tenant_identifiant", "tenant_id", "identifiant"),
    # Sans tenant : la résolution d'un numéro se fait avant de connaître le tenant.
    Index("ix_compte_identifiant", "identifiant"),
)

affectation = Table(
    "affectation",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("tenant_id", UUID(as_uuid=True), nullable=False),
    Column(
        "compte_id",
        UUID(as_uuid=True),
        ForeignKey("habilitations.compte.id"),
        nullable=False,
    ),
    # Identifiant vers `annees.annee_scolaire` : une affectation porte son année (règle 3).
    Column("annee_id", UUID(as_uuid=True), nullable=False),
    # Identifiant vers `tenants.etablissement`, copié de l'année (research.md R-03) : les deux
    # middlewares le lisent à chaque requête, sans traverser un module.
    Column("etablissement_id", UUID(as_uuid=True), nullable=False),
    Column("debut", Date, nullable=False),
    Column("fin", Date),
    Column("cree_le", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    Index(
        "ix_affectation_rattachement",
        "tenant_id",
        "compte_id",
        "etablissement_id",
        "annee_id",
    ),
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
