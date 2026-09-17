import { PLATEFORME_INDISPONIBLE } from '~/core/plateforme/indisponible'
import type { Plateforme } from '~/core/plateforme/plateforme'

/** La plateforme du client ; au rendu serveur, une plateforme où tout est indisponible. */
export function usePlateforme(): Plateforme {
  const fournie = useNuxtApp().$plateforme as Plateforme | undefined
  return fournie ?? PLATEFORME_INDISPONIBLE
}
