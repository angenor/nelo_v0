// Ce qu'une page déclare à la coquille : son contexte tactile, ou qu'elle s'en passe.
import type { ContexteTactile } from '~/core/composants/etats'

declare module '#app' {
  interface PageMeta {
    contexteTactile?: ContexteTactile
    sansCoquille?: boolean
  }
}

export {}
