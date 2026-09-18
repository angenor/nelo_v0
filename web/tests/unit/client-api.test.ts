// Le client d'API (research.md R-09) : les en-têtes de 03-api.md § 1.2, la traduction d'une
// EnveloppeErreur, et un seul rejeu après rafraîchissement, jamais une boucle.
import { describe, expect, it } from 'vitest'
import type { Recuperateur, RequeteRecuperee } from '../../app/core/api/client'
import { creerClient, ErreurApi } from '../../app/core/api/client'

interface Sortie {
  echec?: unknown
  valeur?: unknown
}

interface Trace {
  chemin: string
  requete: RequeteRecuperee
}

/** Un `$fetch` factice : il note ce qu'on lui demande et rend ce qu'on lui a mis en file. */
function doubler(sorties: Sortie[]) {
  const appels: Trace[] = []
  const recuperateur: Recuperateur = async (chemin, requete) => {
    appels.push({ chemin, requete })
    const sortie = sorties.shift() ?? { valeur: {} }
    if ('echec' in sortie) throw sortie.echec
    return sortie.valeur
  }
  return { appels, api: creerClient(recuperateur) }
}

function refus(statut: number, code: string, details: Record<string, unknown> = {}): Sortie {
  return {
    echec: {
      status: statut,
      data: { code, details, champ: null, message: '', requete_id: null },
    },
  }
}

const UUID7 = /^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/

describe('les en-têtes', () => {
  it('appelle une adresse relative au relais, sans clé de requête en lecture', async () => {
    const { appels, api } = doubler([{ valeur: { ok: true } }])
    await api.appeler('GET', '/moi/capacites', { etablissement: 'etab-1', annee: 'annee-1' })
    expect(appels[0]!.chemin).toBe('/api/v1/moi/capacites')
    expect(appels[0]!.requete.method).toBe('GET')
    expect(appels[0]!.requete.headers['X-Nelo-Etablissement']).toBe('etab-1')
    expect(appels[0]!.requete.headers['X-Nelo-Annee']).toBe('annee-1')
    expect(appels[0]!.requete.headers['X-Nelo-Requete']).toBeUndefined()
    expect(appels[0]!.requete.body).toBeUndefined()
  })

  it('pose une clé d’idempotence sur toute écriture, et le corps', async () => {
    const { appels, api } = doubler([{ valeur: null }])
    await api.appeler('POST', '/auth/otp', { corps: { identifiant: '+2250700000001' }, ecriture: true })
    expect(appels[0]!.requete.headers['X-Nelo-Requete']).toMatch(UUID7)
    expect(appels[0]!.requete.body).toEqual({ identifiant: '+2250700000001' })
  })
})

describe('les refus', () => {
  it('traduit une EnveloppeErreur en ErreurApi', async () => {
    const { api } = doubler([refus(403, 'TEN_ETABLISSEMENT_NON_AUTORISE')])
    const echec = await api.appeler('GET', '/parametres').catch((e: unknown) => e)
    expect(echec).toBeInstanceOf(ErreurApi)
    expect((echec as ErreurApi).code).toBe('TEN_ETABLISSEMENT_NON_AUTORISE')
    expect((echec as ErreurApi).statut).toBe(403)
  })

  it('laisse passer tel quel ce qui ne porte pas d’enveloppe', async () => {
    const panne = new Error('le réseau est absent')
    const { api } = doubler([{ echec: panne }])
    await expect(api.appeler('GET', '/parametres')).rejects.toBe(panne)
  })
})

describe('le jeton expiré', () => {
  it('rafraîchit une fois, rejoue, et garde la même clé de requête', async () => {
    const { appels, api } = doubler([
      refus(401, 'AUT_JETON_INVALIDE'),
      { valeur: null },
      { valeur: { fait: true } },
    ])
    const rendu = await api.appeler('POST', '/comptes', { corps: {}, ecriture: true })
    expect(rendu).toEqual({ fait: true })
    expect(appels.map((a) => a.chemin)).toEqual([
      '/api/v1/comptes',
      '/api/v1/auth/rafraichissement',
      '/api/v1/comptes',
    ])
    expect(appels[2]!.requete.headers['X-Nelo-Requete']).toBe(appels[0]!.requete.headers['X-Nelo-Requete'])
  })

  it('ne rejoue jamais deux fois : un second refus remonte', async () => {
    const { appels, api } = doubler([
      refus(401, 'AUT_JETON_INVALIDE'),
      { valeur: null },
      refus(401, 'AUT_JETON_INVALIDE'),
    ])
    const echec = await api.appeler('GET', '/moi/capacites').catch((e: unknown) => e)
    expect(echec).toBeInstanceOf(ErreurApi)
    expect(appels).toHaveLength(3)
  })

  it('remonte le refus quand le rafraîchissement échoue', async () => {
    const { appels, api } = doubler([
      refus(401, 'AUT_JETON_INVALIDE'),
      refus(401, 'AUT_SESSION_REVOQUEE'),
    ])
    const echec = await api.appeler('GET', '/moi/capacites').catch((e: unknown) => e)
    expect((echec as ErreurApi).code).toBe('AUT_JETON_INVALIDE')
    expect(appels).toHaveLength(2)
  })

  it('ne rafraîchit pas sur un autre refus de 401', async () => {
    const { appels, api } = doubler([refus(401, 'AUT_SESSION_REVOQUEE')])
    await api.appeler('GET', '/moi/capacites').catch(() => undefined)
    expect(appels).toHaveLength(1)
  })
})
