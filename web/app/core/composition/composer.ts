// composer(contexte) : la coquille se décide ici, en fonction pure (contracts § 4). Elle ne lit
// que les codes de capacité ; le domaine est le premier segment (FR-021).
import type { ContexteCapacites } from '../contexte/types'
import { DOMAINES, FAMILLES, instancier } from './registre'
import { situationPour } from './situation'
import type { Composition } from './types'

export function domaineDe(code: string): string {
  return code.split('.')[0] ?? ''
}

export function composer(
  contexte: ContexteCapacites,
  signaler: (domaine: string) => void = () => {},
): Composition {
  const objets = new Map<string, Set<string>>()
  for (const { code } of contexte.capacites) {
    const domaine = domaineDe(code)
    if (!DOMAINES.some((d) => d.code === domaine)) {
      signaler(domaine)
      continue
    }
    const ensemble = objets.get(domaine) ?? new Set<string>()
    ensemble.add(code.split('.')[1] ?? '')
    objets.set(domaine, ensemble)
  }
  const domaines = DOMAINES.filter((d) => objets.has(d.code)).map((d) => instancier(d, objets.get(d.code)!))
  const situation = situationPour(domaines.length)
  const familles =
    situation === 'MULTI_FAMILLES'
      ? FAMILLES.map((famille) => ({ famille, domaines: domaines.filter((d) => d.famille === famille.code) })).filter(
          (f) => f.domaines.length > 0,
        )
      : []
  const accueil = { route: situation === 'MONO_DOMAINE' ? domaines[0]!.route : '/' }
  return { situation, domaines, familles, accueil }
}
