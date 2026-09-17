// D'où vient le contexte (contracts/interfaces-client.md § 3). T0b : les personas de
// démonstration ; T1a : GET /moi/capacites. Aucun écran ne sait lequel.
import type { ContexteCapacites } from './types'

export interface SourceContexte {
  charger(): Promise<ContexteCapacites>
}
