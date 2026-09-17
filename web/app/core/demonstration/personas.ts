// Les quatre personas de démonstration, typés par le contrat. Les fichiers JSON sont validés
// contre le schéma de contrat/openapi.json par web/tests/unit/personas.test.ts ; c'est ce qui
// autorise la conversion ci-dessous.
import type { Situation } from '../composants/etats'
import type { ContexteCapacites } from '../contexte/types'
import aucune from './personas/aucune-capacite.json'
import cinq from './personas/cinq-domaines.json'
import sept from './personas/sept-domaines.json'
import un from './personas/un-domaine.json'

export const NOMS_PERSONAS = ['un-domaine', 'cinq-domaines', 'sept-domaines', 'aucune-capacite'] as const
export type NomPersona = (typeof NOMS_PERSONAS)[number]

export const PERSONAS = {
  'un-domaine': un,
  'cinq-domaines': cinq,
  'sept-domaines': sept,
  'aucune-capacite': aucune,
} as unknown as Record<NomPersona, ContexteCapacites>

export const PERSONA_PAR_SITUATION: Record<Situation, NomPersona> = {
  AUCUNE_CAPACITE: 'aucune-capacite',
  MONO_DOMAINE: 'un-domaine',
  MULTI_PLAT: 'cinq-domaines',
  MULTI_FAMILLES: 'sept-domaines',
}

export function estPersona(valeur: unknown): valeur is NomPersona {
  return NOMS_PERSONAS.includes(valeur as NomPersona)
}
