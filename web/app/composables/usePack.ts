import type { ContexteCapacites } from '~/core/contexte/types'
import packDemonstration from '~/core/demonstration/pack-demonstration.json'
import { creerPack } from '~/core/pack/pack'

/** Le pack du contexte, dans la langue courante ; le pack de démonstration tant qu'aucun contexte n'est chargé. */
export function usePack() {
  const contexte = useState<ContexteCapacites | null>('contexte', () => null)
  const { langue } = useLibelles()
  return computed(() => creerPack(contexte.value?.country_pack ?? packDemonstration, langue.value))
}
