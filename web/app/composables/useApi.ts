import { lireAnneeChoisie, lireEtablissementChoisi } from '~/core/appareil/choix'
import type { ClientApi, Recuperateur } from '~/core/api/client'
import { creerClient } from '~/core/api/client'

/**
 * Le client d'API du rendu en cours (research.md R-09). Au rendu serveur, `useRequestFetch`
 * transmet les cookies de la requête entrante au relais, qui les transforme comme pour le
 * navigateur ; au client, c'est `$fetch`. Ni l'un ni l'autre ne voit jamais un jeton.
 *
 * Les deux en-têtes de périmètre viennent du choix mémorisé sur l'appareil (research.md R-21),
 * relu à chaque appel : changer d'établissement vaut dès la requête suivante. Au rendu serveur,
 * le stockage est indisponible et c'est le cookie `nelo_etablissement` que la source lit.
 */
export function useApi(): ClientApi {
  const { stockage } = usePlateforme()
  return creerClient(useRequestFetch() as unknown as Recuperateur, () => ({
    etablissement: lireEtablissementChoisi(stockage) ?? undefined,
    annee: lireAnneeChoisie(stockage) ?? undefined,
  }))
}
