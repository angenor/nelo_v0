import type { EtatReseau } from '~/core/plateforme/plateforme'

/**
 * L'état du réseau, réactif, lu par la plateforme et par elle seule (FR-016). Le rendu serveur
 * le dit bon ; le greffon client le corrige après l'hydratation et le suit.
 */
export function useReseau() {
  return useState<EtatReseau>('reseau', () => 'bon')
}
