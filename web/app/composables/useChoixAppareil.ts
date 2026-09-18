// Le choix de l'établissement et de l'année, vu des écrans (research.md R-21, FR-051 à FR-054).
//
// Il vit sur l'appareil : `localStorage` pour le client, et le cookie `nelo_etablissement` pour
// que le rendu serveur pose le même en-tête dès le premier affichage. Rien n'en part vers le
// serveur comme une préférence : les deux en-têtes sont posés requête par requête.
import {
  ecrireAnneeChoisie,
  ecrireEtablissementChoisi,
  lireAnneeChoisie,
  lireEtablissementChoisi,
} from '~/core/appareil/choix'
import { COOKIE_ETABLISSEMENT } from '~/core/contexte/api'

export function useChoixAppareil() {
  const { stockage, cookies } = usePlateforme()
  const etablissement = useState<string | null>('choix-etablissement', () => null)
  const annee = useState<string | null>('choix-annee', () => null)

  /** Relit ce que l'appareil a mémorisé. Sans stockage, les choix restent ceux du rendu. */
  function relire(): void {
    if (!stockage.disponible) return
    etablissement.value = lireEtablissementChoisi(stockage)
    annee.value = lireAnneeChoisie(stockage)
  }

  /**
   * Choisit l'établissement. L'année mémorisée appartenait au précédent : elle est oubliée, et
   * le contexte relu rendra celle de l'établissement neuf.
   */
  function choisirEtablissement(identifiant: string): void {
    ecrireEtablissementChoisi(stockage, identifiant)
    cookies.ecrire(COOKIE_ETABLISSEMENT, identifiant)
    etablissement.value = identifiant
    ecrireAnneeChoisie(stockage, null)
    annee.value = null
  }

  function choisirAnnee(identifiant: string): void {
    ecrireAnneeChoisie(stockage, identifiant)
    annee.value = identifiant
  }

  return { etablissement, annee, relire, choisirEtablissement, choisirAnnee }
}
