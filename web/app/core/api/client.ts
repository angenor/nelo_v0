// Le client d'API (research.md R-09). Il appelle des adresses relatives : le relais de Nitro
// est sous la même origine que l'application, et c'est lui qui connaît le jeton. Le client,
// lui, n'en voit jamais un.
//
// Il pose les en-têtes de 03-api.md § 1.2, traduit une EnveloppeErreur en ErreurApi, et, sur un
// jeton expiré, rafraîchit une fois puis rejoue. Le rejeu garde le même `X-Nelo-Requete` : sans
// cela, une écriture rejouée compterait deux fois.
//
// Aucune règle métier ici : le client transporte, il ne décide pas.
import type { components } from '../../../../contrat/client'
import { uuid7 } from './uuid7'

export type EnveloppeErreur = components['schemas']['EnveloppeErreur']

export type Methode = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

/** La racine que le relais sert, sous l'origine de l'application. */
export const RACINE = '/api/v1'
/**
 * Le chemin du renouvellement. Le cookie de rafraîchissement est borné à `/api/v1/auth`
 * (data-model.md) : il ne part **que** pour les requêtes du navigateur sous ce chemin, jamais
 * avec une requête de page. C'est pourquoi un renouvellement se demande depuis le client, et
 * jamais au rendu du serveur.
 */
export const RAFRAICHISSEMENT = '/auth/rafraichissement'
/** Les deux refus qu'un rafraîchissement peut lever : le jeton a expiré, ou son cookie a expiré. */
const JETONS_A_RENOUVELER = new Set(['AUT_JETON_INVALIDE', 'AUT_JETON_MANQUANT'])

export interface OptionsAppel {
  corps?: unknown
  etablissement?: string
  annee?: string
  /** Une écriture porte sa clé d'idempotence (règle 10). */
  ecriture?: boolean
}

export interface RequeteRecuperee {
  method: Methode
  headers: Record<string, string>
  body?: unknown
}

/** Ce que le client attend : la signature utile de `$fetch`, pour qu'un double serve aux tests. */
export type Recuperateur = (chemin: string, requete: RequeteRecuperee) => Promise<unknown>

/**
 * L'établissement et l'année choisis sur l'appareil (research.md R-21). Ils sont lus à chaque
 * appel, jamais figés à la construction : un changement d'établissement vaut sur-le-champ.
 */
export type ChoixAppareil = () => { etablissement?: string; annee?: string }

/** Un refus du serveur, tel que 03-api.md § 1.6 le décrit. */
export class ErreurApi extends Error {
  constructor(
    readonly code: string,
    readonly statut: number,
    readonly details: Record<string, unknown> = {},
    readonly champ: string | null = null,
    readonly requeteId: string | null = null,
  ) {
    super(code)
    this.name = 'ErreurApi'
  }
}

interface EchecRecupere {
  status?: number
  statusCode?: number
  data?: unknown
  response?: { status?: number; _data?: unknown }
}

/** L'enveloppe du refus, quand la réponse en porte une ; sinon rien, et l'échec brut remonte. */
function traduire(echec: unknown): ErreurApi | null {
  if (echec === null || typeof echec !== 'object') return null
  const recupere = echec as EchecRecupere
  const statut = recupere.statusCode ?? recupere.status ?? recupere.response?.status
  const corps = (recupere.data ?? recupere.response?._data) as Partial<EnveloppeErreur> | undefined
  if (typeof statut !== 'number' || !corps || typeof corps.code !== 'string') return null
  return new ErreurApi(
    corps.code,
    statut,
    corps.details ?? {},
    corps.champ ?? null,
    corps.requete_id ?? null,
  )
}

export interface ClientApi {
  appeler<T>(methode: Methode, chemin: string, options?: OptionsAppel): Promise<T>
}

export function creerClient(
  recuperateur: Recuperateur,
  choix: ChoixAppareil = () => ({}),
): ClientApi {
  async function brut(methode: Methode, chemin: string, entetes: Record<string, string>, corps?: unknown) {
    const requete: RequeteRecuperee = { method: methode, headers: entetes }
    if (corps !== undefined) requete.body = corps
    return await recuperateur(`${RACINE}${chemin}`, requete)
  }

  /** Une tentative de rafraîchissement ; un échec n'est pas une erreur à remonter, c'est un refus. */
  async function rafraichir(): Promise<boolean> {
    try {
      await brut('POST', RAFRAICHISSEMENT, { 'X-Nelo-Requete': uuid7() })
      return true
    } catch {
      return false
    }
  }

  async function appeler<T>(methode: Methode, chemin: string, options: OptionsAppel = {}): Promise<T> {
    const appareil = choix()
    const etablissement = options.etablissement ?? appareil.etablissement
    const annee = options.annee ?? appareil.annee
    const entetes: Record<string, string> = {}
    if (etablissement) entetes['X-Nelo-Etablissement'] = etablissement
    if (annee) entetes['X-Nelo-Annee'] = annee
    if (options.ecriture) entetes['X-Nelo-Requete'] = uuid7()

    for (let tentative = 0; ; tentative++) {
      try {
        return (await brut(methode, chemin, entetes, options.corps)) as T
      } catch (echec) {
        const erreur = traduire(echec)
        if (!erreur) throw echec
        // Un renouvellement ne se renouvelle pas lui-même : son refus est la réponse.
        const renouvelable = chemin !== RAFRAICHISSEMENT
        const expire = erreur.statut === 401 && JETONS_A_RENOUVELER.has(erreur.code)
        if (!renouvelable || !expire || tentative > 0 || !(await rafraichir())) throw erreur
      }
    }
  }

  return { appeler }
}
