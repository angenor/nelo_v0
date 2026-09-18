"""SC-003 : cent demandes alternées, et rien ne distingue un numéro connu d'un numéro inconnu.

La réponse est déjà la même, et `test_demande_code.py` le prouve. Il reste un canal par lequel le
serveur pourrait parler malgré lui : **le temps**. Le chemin d'un numéro connu écrit deux clés dans
l'éphémère et un événement en base ; celui d'un inconnu ne fait rien de tout cela. Si l'écart se
voyait, un balayage n'aurait qu'à chronométrer pour dresser la liste des numéros inscrits dans les
écoles du service, et la règle de la tranche tomberait sans qu'une seule réponse ait menti.

La mesure porte sur les **médianes** et non sur les moyennes : une seconde volée par le
ramasse-miettes ou par la base ne doit pas décider du verdict.

La suite est marquée `lent` : elle émet cent requêtes et les chronomètre. Elle tourne dans la
vérification parce que P-12 exécute la suite entière, sans désélectionner aucun marqueur.
"""

import statistics
import time

import pytest

from tests.authentification.outils import demander, evenements, semer_compte_neuf
from tests.conftest import numero_de_test

REPETITIONS = 100
ECART_TOLERE_MS = 50.0


async def lever_les_limites(valkey, *numeros: str) -> None:
    """Les compteurs de débit, remis à zéro **hors** du chronomètre.

    Sans cela, la vingt-et-unième demande serait refusée et la suite mesurerait la vitesse d'un
    refus, pas celle des deux chemins qu'elle compare.
    """
    cles = [f"{prefixe}{numero}" for numero in numeros for prefixe in ("otp_renvoi:", "otp_debit:")]
    cles += list(await valkey.keys("otp_debit_client:*"))
    if cles:
        await valkey.delete(*cles)


def sans_date(reponse) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted((nom, valeur) for nom, valeur in reponse.headers.items() if nom.lower() != "date")
    )


@pytest.mark.lent
async def test_cent_demandes_alternees_ne_se_distinguent_ni_par_la_reponse_ni_par_le_temps(
    client, tenants_ab, valkey
):
    connu, _ = await semer_compte_neuf(tenants_ab.a)
    inconnu = numero_de_test()

    durees: dict[str, list[float]] = {"connu": [], "inconnu": []}
    signatures: set[tuple] = set()

    for rang in range(REPETITIONS):
        cas = "connu" if rang % 2 == 0 else "inconnu"
        numero = connu if cas == "connu" else inconnu
        await lever_les_limites(valkey, connu, inconnu)

        debut = time.perf_counter()
        reponse = await demander(client, numero)
        durees[cas].append((time.perf_counter() - debut) * 1000)

        signatures.add((reponse.status_code, reponse.content, sans_date(reponse)))

    # Une seule signature : même statut, même corps, mêmes en-têtes, cent fois de suite.
    assert len(signatures) == 1, signatures
    assert signatures.pop()[:2] == (204, b"")

    # Le chemin du numéro connu a bien fait son travail : sans cela, l'égalité des temps ne
    # prouverait rien, elle dirait seulement que les deux chemins ne font rien.
    ecrits = await evenements(tenants_ab.tenant_a, "habilitations.otp.demande")
    assert len(ecrits) == REPETITIONS // 2

    median_connu = statistics.median(durees["connu"])
    median_inconnu = statistics.median(durees["inconnu"])
    ecart = abs(median_connu - median_inconnu)
    # La mesure se lit au journal de la tranche (SC-003) : elle est imprimée pour cela.
    print(
        f"SC-003 : connu {median_connu:.1f} ms, inconnu {median_inconnu:.1f} ms, "
        f"écart {ecart:.1f} ms (toléré {ECART_TOLERE_MS} ms)"
    )
    assert ecart < ECART_TOLERE_MS, (
        f"écart des médianes de {ecart:.1f} ms : connu {median_connu:.1f} ms, "
        f"inconnu {median_inconnu:.1f} ms"
    )
