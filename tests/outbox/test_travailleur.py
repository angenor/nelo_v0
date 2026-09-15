"""US3 — le travailleur consomme l'outbox : jamais perdu, au moins une fois, dans l'ordre par tenant."""

import asyncio
from datetime import timedelta
from uuid import UUID

import pytest
from sqlalchemy import text

from api.configuration import Configuration
from api.travailleur import Travailleur
from modules.shared import Evenement, transaction
from modules.socle.tenants import acces


class Consommateur:
    def __init__(self, tenants: set[UUID]):
        self.tenants = tenants
        self.recus: dict[UUID, list[str]] = {t: [] for t in tenants}
        self.echouer = False

    async def __call__(self, tenant_id: UUID, evenement_id: UUID, evenement: Evenement) -> None:
        if tenant_id not in self.tenants:
            return
        if self.echouer:
            raise RuntimeError("consommateur en panne")
        self.recus[tenant_id].append(evenement.charge["n"])


async def ecrire(tenant_id: UUID, n: str) -> UUID:
    async with transaction(tenant_id) as connexion:
        return await acces.inserer_evenement(connexion, tenant_id, Evenement("essai", {"n": n}))


async def etat(tenant_id: UUID, evenement_id: UUID):
    async with transaction(tenant_id) as connexion:
        resultat = await connexion.execute(
            text(
                "SELECT etat, tentatives, derniere_erreur, traite_le FROM tenants.evenement_outbox "
                "WHERE id = :id"
            ),
            {"id": evenement_id},
        )
        return resultat.one()


@pytest.fixture
def configuration_rapide() -> Configuration:
    return Configuration(travailleur_intervalle_ms=20, travailleur_delai_orphelin_ms=1000)


async def test_consomme_et_marque_traite(tenants_ab, configuration_rapide):
    consommateur = Consommateur({tenants_ab.tenant_a})
    evenement_id = await ecrire(tenants_ab.tenant_a, "1")
    await Travailleur(configuration_rapide, consommateur).un_tour()
    ligne = await etat(tenants_ab.tenant_a, evenement_id)
    assert ligne.etat == "traite" and ligne.traite_le is not None
    assert consommateur.recus[tenants_ab.tenant_a] == ["1"]


async def test_echec_puis_reprise_jamais_perdu(tenants_ab, configuration_rapide):
    from modules.socle.tenants import service

    consommateur = Consommateur({tenants_ab.tenant_a})
    travailleur = Travailleur(configuration_rapide, consommateur)
    evenement_id = await ecrire(tenants_ab.tenant_a, "1")

    consommateur.echouer = True
    await travailleur.un_tour()
    ligne = await etat(tenants_ab.tenant_a, evenement_id)
    assert (ligne.etat, ligne.tentatives) == ("en_echec", 1)
    assert "consommateur en panne" in ligne.derniere_erreur

    await service.reprendre_evenements(
        tenants_ab.tenant_a, configuration_rapide.travailleur_delai_orphelin
    )
    assert (await etat(tenants_ab.tenant_a, evenement_id)).etat == "en_attente"

    consommateur.echouer = False
    await travailleur.un_tour()
    ligne = await etat(tenants_ab.tenant_a, evenement_id)
    assert (ligne.etat, ligne.tentatives) == ("traite", 1)
    assert consommateur.recus[tenants_ab.tenant_a] == ["1"]


async def test_ordre_par_tenant(tenants_ab, configuration_rapide):
    consommateur = Consommateur({tenants_ab.tenant_a, tenants_ab.tenant_b})
    for n in ("a1", "a2", "a3"):
        await ecrire(tenants_ab.tenant_a, n)
    for n in ("b1", "b2"):
        await ecrire(tenants_ab.tenant_b, n)
    await Travailleur(configuration_rapide, consommateur).un_tour()
    assert consommateur.recus[tenants_ab.tenant_a] == ["a1", "a2", "a3"]
    assert consommateur.recus[tenants_ab.tenant_b] == ["b1", "b2"]


async def test_un_echec_n_inverse_pas_l_ordre(tenants_ab, configuration_rapide):
    consommateur = Consommateur({tenants_ab.tenant_a})
    travailleur = Travailleur(configuration_rapide, consommateur)
    await ecrire(tenants_ab.tenant_a, "1")
    await ecrire(tenants_ab.tenant_a, "2")
    consommateur.echouer = True
    await travailleur.un_tour()
    consommateur.echouer = False
    await travailleur.un_tour()
    assert consommateur.recus[tenants_ab.tenant_a] == ["1", "2"]


async def test_la_prise_ne_depasse_jamais_n(tenants_ab):
    ids = [await ecrire(tenants_ab.tenant_a, str(n)) for n in range(5)]
    async with transaction(tenants_ab.tenant_a) as connexion:
        pris = await acces.prendre_evenements(connexion, tenants_ab.tenant_a, 2)
        assert [e["id"] for e in pris] == ids[:2]
        etats = await connexion.execute(
            text(
                "SELECT etat, count(*) FROM tenants.evenement_outbox WHERE id = ANY(:ids) GROUP BY etat"
            ),
            {"ids": ids},
        )
        assert dict(etats.all()) == {"pris": 2, "en_attente": 3}


async def test_pris_orphelin_repris(tenants_ab, configuration_rapide):
    consommateur = Consommateur({tenants_ab.tenant_a})
    evenement_id = await ecrire(tenants_ab.tenant_a, "1")
    async with transaction(tenants_ab.tenant_a) as connexion:
        pris = await acces.prendre_evenements(connexion, tenants_ab.tenant_a, 10)
        assert evenement_id in [e["id"] for e in pris]
        await connexion.execute(
            text(
                "UPDATE tenants.evenement_outbox SET pris_le = now() - interval '1 hour' WHERE id = :id"
            ),
            {"id": evenement_id},
        )
    await Travailleur(configuration_rapide, consommateur).un_tour()
    assert (await etat(tenants_ab.tenant_a, evenement_id)).etat == "traite"
    assert consommateur.recus[tenants_ab.tenant_a] == ["1"]


async def test_arrete_accumule_relance_consomme(tenants_ab, configuration_rapide):
    consommateur = Consommateur({tenants_ab.tenant_a})
    travailleur = Travailleur(configuration_rapide, consommateur)
    ids = [await ecrire(tenants_ab.tenant_a, str(n)) for n in range(3)]
    assert {(await etat(tenants_ab.tenant_a, i)).etat for i in ids} == {"en_attente"}

    await travailleur.demarrer()
    # Un tour parcourt tous les tenants de la base de test : l'attente est bornée, pas serrée.
    for _ in range(1000):
        if len(consommateur.recus[tenants_ab.tenant_a]) == 3:
            break
        await asyncio.sleep(0.02)
    await travailleur.arreter()
    assert consommateur.recus[tenants_ab.tenant_a] == ["0", "1", "2"]
    assert {(await etat(tenants_ab.tenant_a, i)).etat for i in ids} == {"traite"}
    assert timedelta(milliseconds=20) == configuration_rapide.travailleur_intervalle
