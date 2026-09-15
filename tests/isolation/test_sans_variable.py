"""FR-017 — sans variable de tenant, zéro ligne visible et aucune écriture — jamais « toutes »."""

import uuid

import pytest
from sqlalchemy import column, insert, table
from sqlalchemy.exc import DBAPIError

from tests.isolation.schema import SCHEMA, compter, tables_du_schema

ECRITURES = {
    "tenant": {"id": uuid.uuid7(), "nom": "intrus", "pays_code": "XX", "country_pack_version": 1},
    "etablissement": {
        "id": uuid.uuid7(),
        "tenant_id": uuid.uuid7(),
        "nom": "intrus",
        "fuseau_horaire": "UTC",
    },
    "parametre_catalogue": {
        "cle": "intrus",
        "portee_la_plus_basse": "TENANT",
        "type": "ENTIER",
        "origine_defaut": "LITTERALE",
        "description_cle": "intrus",
    },
    "parametre_valeur": {
        "id": uuid.uuid7(),
        "tenant_id": uuid.uuid7(),
        "cle": "assistance.suspendue",
        "portee": "TENANT",
        "portee_id": uuid.uuid7(),
        "valeur": "true",
    },
    "evenement_outbox": {
        "id": uuid.uuid7(),
        "tenant_id": uuid.uuid7(),
        "type": "intrus",
        "charge": "{}",
    },
}


async def test_zero_ligne_sur_chaque_table(moteur_application, tenants_ab):
    async with moteur_application.begin() as connexion:
        noms = await tables_du_schema(connexion)
        for nom in noms:
            assert await connexion.scalar(compter(nom)) == 0, f"tenants.{nom} visible sans tenant"
    assert set(noms) == set(ECRITURES)


@pytest.mark.parametrize("nom", sorted(ECRITURES))
async def test_aucune_ecriture_sans_variable(moteur_application, nom):
    valeurs = ECRITURES[nom]
    cible = table(nom, *(column(c) for c in valeurs), schema=SCHEMA)
    with pytest.raises(DBAPIError) as refus:
        async with moteur_application.begin() as connexion:
            await connexion.execute(insert(cible).values(**valeurs))
    message = str(refus.value)
    assert "row-level security" in message or "permission denied" in message, message
