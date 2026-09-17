// Les quatre situations de la coquille et leur seuil : à plat jusqu'à cinq domaines inclus,
// regroupée dès six (FR-025 ; 02-domaine.md § 3.4 l'emporte sur la planche).
import type { Situation } from '../composants/etats'
import { COMPOSANTS } from '../composants/etats'

export const SITUATIONS = COMPOSANTS.Coquille.SITUATIONS
export const SEUIL_A_PLAT = 5

export function situationPour(nombreDeDomaines: number): Situation {
  if (nombreDeDomaines === 0) return 'AUCUNE_CAPACITE'
  if (nombreDeDomaines === 1) return 'MONO_DOMAINE'
  return nombreDeDomaines <= SEUIL_A_PLAT ? 'MULTI_PLAT' : 'MULTI_FAMILLES'
}
