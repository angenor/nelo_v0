"""Environnement Alembic du module `annees`.

La table de version vit **dans le schéma du module**, `annees.alembic_version` : aucun module ne
partage la sienne (research.md R-08). Le schéma est donc créé ici, avant la table de version, et
la migration `0001` n'en crée que le contenu.
"""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.engine import Connection, make_url
from sqlalchemy.ext.asyncio import create_async_engine

from modules.socle.annees import tables

SCHEMA = "annees"

configuration = context.config
if configuration.config_file_name is not None:
    fileConfig(configuration.config_file_name, disable_existing_loggers=False)


def url_proprietaire() -> str:
    """NELO_BD_URL_PROPRIETAIRE, dont la base est surchargée par NELO_BD_NOM s'il est posé."""
    if "NELO_BD_URL_PROPRIETAIRE" not in os.environ:
        from api.configuration import Configuration

        url = make_url(Configuration().bd_url_proprietaire)
    else:
        url = make_url(os.environ["NELO_BD_URL_PROPRIETAIRE"])
    if nom := os.environ.get("NELO_BD_NOM"):
        url = url.set(database=nom)
    return url.render_as_string(hide_password=False)


def _inclure(objet, nom, type_, reflechi, compare_a) -> bool:
    if type_ == "table":
        return objet.schema == SCHEMA and nom != "alembic_version"
    return True


def executer(connexion: Connection) -> None:
    connexion.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))
    context.configure(
        connection=connexion,
        target_metadata=tables.metadata,
        version_table_schema=SCHEMA,
        include_schemas=True,
        include_object=_inclure,
    )
    with context.begin_transaction():
        context.run_migrations()


async def executer_en_ligne() -> None:
    moteur = create_async_engine(url_proprietaire(), poolclass=pool.NullPool)
    async with moteur.begin() as connexion:
        await connexion.run_sync(executer)
    await moteur.dispose()


if context.is_offline_mode():
    raise RuntimeError("les migrations de Nelo s'appliquent en ligne, contre une base réelle")

asyncio.run(executer_en_ligne())
