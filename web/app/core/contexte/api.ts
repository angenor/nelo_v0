// La source de contexte réelle (research.md R-09, R-19) : GET /moi/capacites, par le relais.
//
// Le middleware d'établissement refuse toute route sans `X-Nelo-Etablissement` : demander le
// contexte « sans établissement » n'existe pas. La source part donc de celui que l'appareil a
// mémorisé (cookie `nelo_etablissement`, lu de l'en-tête au rendu serveur) ; sans lui, le refus
// `TEN_ETABLISSEMENT_REQUIS` porte les rattachements du compte, et elle relit sur le premier.
//
// Un `401` n'est pas une panne : c'est l'absence de session. La source rend `null`, et la garde
// de route conduit vers la connexion.
import type { ClientApi } from '../api/client'
import { ErreurApi } from '../api/client'
import type { SourceContexte } from './source'
import type { ContexteCapacites } from './types'

/** Un identifiant d'établissement, sans secret : le compte a le droit de le voir. */
export const COOKIE_ETABLISSEMENT = 'nelo_etablissement'
const CONTEXTE = '/moi/capacites'
const ETABLISSEMENT_REQUIS = 'TEN_ETABLISSEMENT_REQUIS'

/** L'établissement mémorisé sur l'appareil, lu de l'en-tête `Cookie` de la requête entrante. */
export function etablissementDuCookie(entete: string | undefined | null): string | null {
  for (const morceau of (entete ?? '').split(';')) {
    const separateur = morceau.indexOf('=')
    if (separateur < 0) continue
    if (morceau.slice(0, separateur).trim() !== COOKIE_ETABLISSEMENT) continue
    const valeur = decodeURIComponent(morceau.slice(separateur + 1).trim())
    return valeur === '' ? null : valeur
  }
  return null
}

/** Le premier rattachement que le refus du middleware rend, quand il en rend. */
export function premierRattachement(details: Record<string, unknown>): string | null {
  const rattaches = details.etablissements
  if (!Array.isArray(rattaches)) return null
  const premier = rattaches.find((valeur) => typeof valeur === 'string' && valeur !== '')
  return typeof premier === 'string' ? premier : null
}

export class SourceApi implements SourceContexte {
  constructor(
    private readonly client: ClientApi,
    private readonly etablissementConnu: string | null = null,
  ) {}

  async charger(): Promise<ContexteCapacites | null> {
    try {
      return await this.lire(this.etablissementConnu)
    } catch (echec) {
      if (!(echec instanceof ErreurApi)) throw echec
      if (echec.statut === 401) return null
      if (echec.code !== ETABLISSEMENT_REQUIS) throw echec
      const premier = premierRattachement(echec.details)
      if (premier === null) throw echec
      return await this.relire(premier)
    }
  }

  private async relire(etablissement: string): Promise<ContexteCapacites | null> {
    try {
      return await this.lire(etablissement)
    } catch (echec) {
      if (echec instanceof ErreurApi && echec.statut === 401) return null
      throw echec
    }
  }

  private lire(etablissement: string | null): Promise<ContexteCapacites> {
    return this.client.appeler<ContexteCapacites>('GET', CONTEXTE, {
      etablissement: etablissement ?? undefined,
    })
  }
}
