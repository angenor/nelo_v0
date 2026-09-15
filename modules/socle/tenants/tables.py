"""Les cinq tables du schéma `tenants`, déclarées une fois en SQLAlchemy Core.

Cette déclaration sert aux requêtes de `acces.py` et à la comparaison de la porte P-12 contre le
schéma réellement migré. La migration, elle, écrit ses tables en toutes lettres : une migration
appliquée ne se modifie jamais, une déclaration si.
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
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

metadata = MetaData(schema="tenants")

PORTEES = ("TENANT", "ETABLISSEMENT", "SITE", "CYCLE")
TYPES = ("ENTIER", "DECIMAL", "BOOLEEN", "CHAINE", "PLAGE_HORAIRE")
ORIGINES = ("LITTERALE", "COUNTRY_PACK", "OBLIGATOIRE")
ETATS_EVENEMENT = ("en_attente", "pris", "traite", "en_echec")


def _dans(colonne: str, valeurs: tuple[str, ...]) -> str:
    return f"{colonne} IN ({', '.join(repr(v) for v in valeurs)})"


tenant = Table(
    "tenant",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("nom", Text, nullable=False),
    Column("raison_sociale", Text),
    Column("pays_code", Text, nullable=False),
    Column("country_pack_version", Integer, nullable=False),
    Column("statut_abonnement", Text, nullable=False, server_default=text("'ACTIF'")),
    Column("branding", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column("cree_le", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
)

etablissement = Table(
    "etablissement",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("tenant_id", UUID(as_uuid=True), ForeignKey("tenants.tenant.id"), nullable=False),
    Column("nom", Text, nullable=False),
    Column("code_officiel", Text),
    Column("agrement", Text),
    Column("fuseau_horaire", Text, nullable=False),
    Column("telephone", Text),
    Column("direction_regionale", Text),
    Column("cree_le", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    Index("ix_etablissement_tenant", "tenant_id"),
)

parametre_catalogue = Table(
    "parametre_catalogue",
    metadata,
    Column("cle", Text, primary_key=True),
    Column("portee_la_plus_basse", Text, nullable=False),
    Column("type", Text, nullable=False),
    Column("valeur_defaut", JSONB(none_as_null=True)),
    Column("origine_defaut", Text, nullable=False),
    Column("description_cle", Text, nullable=False),
    CheckConstraint(_dans("portee_la_plus_basse", PORTEES), name="ck_catalogue_portee"),
    CheckConstraint(_dans("type", TYPES), name="ck_catalogue_type"),
    CheckConstraint(_dans("origine_defaut", ORIGINES), name="ck_catalogue_origine"),
)

parametre_valeur = Table(
    "parametre_valeur",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("tenant_id", UUID(as_uuid=True), ForeignKey("tenants.tenant.id"), nullable=False),
    Column("cle", Text, ForeignKey("tenants.parametre_catalogue.cle"), nullable=False),
    Column("portee", Text, nullable=False),
    Column("portee_id", UUID(as_uuid=True), nullable=False),
    Column("valeur", JSONB, nullable=False),
    Column("pose_le", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    CheckConstraint(_dans("portee", PORTEES), name="ck_valeur_portee"),
    UniqueConstraint("tenant_id", "cle", "portee", "portee_id", name="uq_valeur_cle_naturelle"),
    Index("ix_valeur_tenant_cle", "tenant_id", "cle"),
)

evenement_outbox = Table(
    "evenement_outbox",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("tenant_id", UUID(as_uuid=True), ForeignKey("tenants.tenant.id"), nullable=False),
    Column("type", Text, nullable=False),
    Column("charge", JSONB, nullable=False),
    Column("ecrit_le", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    Column("etat", Text, nullable=False, server_default=text("'en_attente'")),
    Column("tentatives", Integer, nullable=False, server_default=text("0")),
    Column("pris_le", TIMESTAMP(timezone=True)),
    Column("traite_le", TIMESTAMP(timezone=True)),
    Column("derniere_erreur", Text),
    CheckConstraint(_dans("etat", ETATS_EVENEMENT), name="ck_evenement_etat"),
    Index("ix_evenement_file", "tenant_id", "etat", "ecrit_le", "id"),
)
