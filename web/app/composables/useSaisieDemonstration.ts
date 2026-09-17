import type { CodeEtat } from '~/core/composants/etats'

export interface SaisieDemonstration {
  id: number
  texte: string
  etat: Extract<CodeEtat, 'EN_ATTENTE' | 'ENREGISTRE'>
}

/** Le délai avant l'envoi d'un lot, selon la qualité du lien : une simulation, rien de plus. */
const DELAIS = { bon: 600, faible: 1500 } as const

/**
 * La source de saisie de démonstration (research.md R-04) : chaque saisie attend, un lot part
 * quand le lien existe, et le lot repart de lui-même au retour du lien. Les tranches de saisie
 * la remplaceront par la file d'écritures idempotentes ; le ruban ne changera pas.
 */
export function useSaisieDemonstration() {
  const saisies = useState<SaisieDemonstration[]>('saisies-demonstration', () => [])
  const dernier = useState<string | null>('dernier-enregistrement', () => null)
  const reseau = useReseau()
  const enAttente = computed(() => saisies.value.filter((s) => s.etat === 'EN_ATTENTE').length)
  const dernierEnregistrement = computed(() => (dernier.value ? new Date(dernier.value) : null))
  let minuterie: ReturnType<typeof setTimeout> | undefined

  function envoyer() {
    minuterie = undefined
    if (reseau.value === 'absent' || enAttente.value === 0) return
    saisies.value = saisies.value.map((s) => ({ ...s, etat: 'ENREGISTRE' }))
    dernier.value = new Date().toISOString()
  }

  function planifier() {
    clearTimeout(minuterie)
    minuterie = undefined
    if (reseau.value === 'absent' || enAttente.value === 0) return
    minuterie = setTimeout(envoyer, DELAIS[reseau.value])
  }

  function saisir(texte: string) {
    const propre = texte.trim()
    if (!propre) return
    saisies.value = [{ id: Date.now() + saisies.value.length, texte: propre, etat: 'EN_ATTENTE' }, ...saisies.value]
    planifier()
  }

  /** À appeler une fois par l'écran de saisie : suit le réseau et relance l'envoi. */
  function demarrer() {
    const arreter = watch(reseau, planifier)
    onBeforeUnmount(() => {
      arreter()
      clearTimeout(minuterie)
    })
  }

  return { saisies, enAttente, dernierEnregistrement, saisir, demarrer }
}
