// L'établissement et l'année de travail, choisis sur l'appareil (research.md R-21, FR-051).
// Le patron est celui de `core/theme.ts` : des fonctions pures qui prennent le `Stockage` de la
// plateforme, et rien d'autre.
//
// Le serveur ne retient jamais ce choix : aucune route ne s'y replie, aucun défaut n'y vit. Ce
// qui voyage vers l'API, ce sont les deux en-têtes que le client pose à chaque requête ; ce qui
// permet au rendu serveur de les poser dès le premier affichage, c'est le cookie
// `nelo_etablissement`, posé par la plateforme au moment du choix.
import type { Stockage } from '../plateforme/plateforme'

const CLE_ETABLISSEMENT = 'etablissement'
const CLE_ANNEE = 'annee'

/** Un identifiant mémorisé, ou rien : une chaîne vide n'est pas un choix. */
function lire(stockage: Stockage, cle: string): string | null {
  const valeur = stockage.lire(cle)
  return valeur === null || valeur === '' ? null : valeur
}

function ecrire(stockage: Stockage, cle: string, identifiant: string | null): void {
  if (identifiant === null || identifiant === '') stockage.effacer(cle)
  else stockage.ecrire(cle, identifiant)
}

export function lireEtablissementChoisi(stockage: Stockage): string | null {
  return lire(stockage, CLE_ETABLISSEMENT)
}

export function ecrireEtablissementChoisi(stockage: Stockage, identifiant: string | null): void {
  ecrire(stockage, CLE_ETABLISSEMENT, identifiant)
}

export function lireAnneeChoisie(stockage: Stockage): string | null {
  return lire(stockage, CLE_ANNEE)
}

export function ecrireAnneeChoisie(stockage: Stockage, identifiant: string | null): void {
  ecrire(stockage, CLE_ANNEE, identifiant)
}
