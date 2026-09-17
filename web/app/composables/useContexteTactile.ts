import type { InjectionKey, Ref } from 'vue'
import type { ContexteTactile } from '~/core/composants/etats'

/**
 * Le contexte tactile d'un écran (contracts § 2) : l'écran le déclare par definePageMeta, la
 * coquille le fournit, tout composant peut le lire. Il se traduit par la variable --cible, que
 * les composants interactifs emploient ; un contrôle de poste se dessine à 36 px et garde une
 * zone de --cible-plancher par un pseudo-élément.
 */
export const CLE_CONTEXTE_TACTILE: InjectionKey<Ref<ContexteTactile>> = Symbol('contexte-tactile')

export const CIBLES: Record<ContexteTactile, string> = {
  classe: 'var(--cible-classe)',
  standard: 'var(--cible-standard)',
  poste: 'var(--controle-poste)',
}

export function fournirContexteTactile(contexte: Ref<ContexteTactile>) {
  provide(CLE_CONTEXTE_TACTILE, contexte)
  return computed(() => ({ '--cible': CIBLES[contexte.value] }))
}

export function useContexteTactile(): Ref<ContexteTactile> {
  return inject(CLE_CONTEXTE_TACTILE, ref<ContexteTactile>('standard'))
}
