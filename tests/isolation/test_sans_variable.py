"""FR-017 : sans variable de tenant, zéro ligne visible et aucune écriture, jamais « toutes ».

Le parcours de lecture couvre les **quatre schémas**, énumérés depuis la base : une table ajoutée
demain sans politique s'y montrerait, et ce test tomberait. Les écritures, elles, sont écrites une
par une : il faut des valeurs plausibles pour qu'un refus prouve quelque chose, et un `INSERT` qui
échouerait sur une colonne manquante ne dirait rien de la sécurité.
"""

import uuid
from datetime import date

import pytest
from sqlalchemy import column, insert, table
from sqlalchemy.exc import DBAPIError

from tests.isolation.schema import SCHEMAS, compter, tables_du_schema

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
    "country_pack": {"pays_code": "XX", "version": 1, "contenu": "{}"},
}

# Les tables des trois schémas neufs, avec le schéma qui les porte. `evenement_outbox` existe dans
# chacun : la clé dit donc le schéma, et la valeur ce qu'on tente d'y écrire.
ECRITURES_DES_NOYAUX = {
    ("personnes", "personne"): {
        "id": uuid.uuid7(),
        "tenant_id": uuid.uuid7(),
        "nom": "intrus",
        "prenoms": "intrus",
        "langue_preferee": "fr",
    },
    ("annees", "annee_scolaire"): {
        "id": uuid.uuid7(),
        "tenant_id": uuid.uuid7(),
        "etablissement_id": uuid.uuid7(),
        "libelle": "intrus",
        "debut": date(2026, 9, 1),
        "fin": date(2027, 7, 31),
        "etat": "active",
    },
    ("habilitations", "compte"): {
        "id": uuid.uuid7(),
        "tenant_id": uuid.uuid7(),
        "personne_id": uuid.uuid7(),
        "identifiant": "+2250700000000",
        "statut": "actif",
    },
}


@pytest.mark.parametrize("schema", SCHEMAS)
async def test_zero_ligne_sur_chaque_table(moteur_application, tenants_ab, schema):
    async with moteur_application.begin() as connexion:
        noms = await tables_du_schema(connexion, schema)
        for nom in noms:
            visibles = await connexion.scalar(compter(nom, schema=schema))
            assert visibles == 0, f"{schema}.{nom} visible sans tenant"
    if schema == "tenants":
        # Le schéma doré est le seul dont chaque table est aussi exercée en écriture ci-dessous.
        assert set(noms) == set(ECRITURES)


async def refus_d_ecriture(moteur_application, schema: str, nom: str, valeurs: dict) -> None:
    cible = table(nom, *(column(c) for c in valeurs), schema=schema)
    with pytest.raises(DBAPIError) as refus:
        async with moteur_application.begin() as connexion:
            await connexion.execute(insert(cible).values(**valeurs))
    message = str(refus.value)
    assert "row-level security" in message or "permission denied" in message, message


@pytest.mark.parametrize("nom", sorted(ECRITURES))
async def test_aucune_ecriture_sans_variable(moteur_application, nom):
    await refus_d_ecriture(moteur_application, "tenants", nom, ECRITURES[nom])


@pytest.mark.parametrize(("schema", "nom"), sorted(ECRITURES_DES_NOYAUX))
async def test_aucune_ecriture_dans_les_schemas_neufs(moteur_application, schema, nom):
    await refus_d_ecriture(moteur_application, schema, nom, ECRITURES_DES_NOYAUX[(schema, nom)])
