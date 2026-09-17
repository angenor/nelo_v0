// La source de contexte de T0b : un persona de démonstration, choisi par `?persona=`, et le pack
// fictif par `?pack=fictif`. Toute la source est de démonstration, construction comprise
// (écart E-14) ; T1a la remplace par SourceApi (GET /moi/capacites) sans toucher à la coquille.
import type { SourceContexte } from './source'
import type { ContexteCapacites } from './types'

export class SourceDemonstration implements SourceContexte {
  constructor(
    private readonly persona: unknown,
    private readonly pack: unknown,
  ) {}

  async charger(): Promise<ContexteCapacites> {
    const { PERSONAS, estPersona } = await import('../demonstration/personas')
    const choisi = estPersona(this.persona) ? this.persona : 'un-domaine'
    const contexte = structuredClone(PERSONAS[choisi])
    if (this.pack === 'fictif') {
      const fictif = await import('../demonstration/pack-fictif.json')
      contexte.country_pack = structuredClone(fictif.default)
    }
    return contexte
  }
}

/** La langue de départ : celle du compte si le pack la porte, sinon la première du pack (FR-052). */
export function langueInitiale(contexte: ContexteCapacites): string {
  const { langues } = contexte.country_pack
  return langues.includes(contexte.compte.langue) ? contexte.compte.langue : langues[0]!
}
