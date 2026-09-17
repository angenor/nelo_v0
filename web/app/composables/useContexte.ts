import { composer } from '~/core/composition/composer'
import type { ContexteCapacites } from '~/core/contexte/types'

/** Le contexte chargé par le greffon, et la composition qui en dérive. */
export function useContexte() {
  const etat = useState<ContexteCapacites | null>('contexte', () => null)
  const contexte = computed(() => {
    if (!etat.value) throw new Error('contexte : le greffon ne l’a pas chargé')
    return etat.value
  })
  const composition = computed(() =>
    composer(contexte.value, (domaine) => {
      if (import.meta.dev) console.warn(`[composition] domaine inconnu du registre : ${domaine}`)
    }),
  )
  return { contexte, composition }
}
