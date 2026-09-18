// US5 et US3 : la source de démonstration choisit le persona et le pack ; la langue de départ
// est celle du compte si le pack la porte, sinon la première du pack (FR-052).
// T1a : la source réelle lit GET /moi/capacites, part de l'établissement mémorisé, et rend
// `null` quand aucune session n'existe (research.md R-09).
import { describe, expect, it } from 'vitest'
import type { ClientApi, Methode, OptionsAppel } from '../../app/core/api/client'
import { ErreurApi } from '../../app/core/api/client'
import { etablissementDuCookie, premierRattachement, SourceApi } from '../../app/core/contexte/api'
import { langueInitiale, SourceDemonstration } from '../../app/core/contexte/demonstration'

describe('SourceDemonstration', () => {
  it('rend le persona demandé, ou le persona à un domaine', async () => {
    expect((await new SourceDemonstration('sept-domaines', undefined).charger()).capacites).toHaveLength(7)
    expect((await new SourceDemonstration('inconnu', undefined).charger()).capacites).toHaveLength(2)
    expect((await new SourceDemonstration(['x'], undefined).charger()).capacites).toHaveLength(2)
  })

  it('substitue le pack fictif sans toucher au reste', async () => {
    const contexte = await new SourceDemonstration('un-domaine', 'fictif').charger()
    expect(contexte.country_pack.vocabulaire.CLASSE!.fr).toBe('Form')
    expect(contexte.country_pack.devise.exposant).toBe(2)
    expect(contexte.compte.nom).toBe('Kacou')
  })

  it('rend une copie : charger deux fois ne partage rien', async () => {
    const a = await new SourceDemonstration('un-domaine', undefined).charger()
    a.compte.nom = 'modifié'
    expect((await new SourceDemonstration('un-domaine', undefined).charger()).compte.nom).toBe('Kacou')
  })
})

describe('langueInitiale', () => {
  it('prend la langue du compte si le pack la porte, la première du pack sinon', async () => {
    const contexte = await new SourceDemonstration('un-domaine', undefined).charger()
    expect(langueInitiale(contexte)).toBe('fr')
    contexte.compte.langue = 'en'
    expect(langueInitiale(contexte)).toBe('en')
    contexte.compte.langue = 'de'
    expect(langueInitiale(contexte)).toBe('fr')
    contexte.country_pack.langues = ['en', 'fr']
    expect(langueInitiale(contexte)).toBe('en')
  })
})

interface Demande {
  methode: Methode
  chemin: string
  options: OptionsAppel
}

function doubler(sorties: unknown[]) {
  const demandes: Demande[] = []
  const client: ClientApi = {
    async appeler<T>(methode: Methode, chemin: string, options: OptionsAppel = {}): Promise<T> {
      demandes.push({ methode, chemin, options })
      const sortie = sorties.shift()
      if (sortie instanceof ErreurApi) throw sortie
      return sortie as T
    },
  }
  return { demandes, client }
}

const CONTEXTE = { compte: { nom: 'Kacou' } }

describe('etablissementDuCookie', () => {
  it('lit l’établissement mémorisé, et rien d’autre', () => {
    expect(etablissementDuCookie('theme=dark; nelo_etablissement=etab-1; autre=x')).toBe('etab-1')
    expect(etablissementDuCookie('nelo_etablissement=etab-1')).toBe('etab-1')
    expect(etablissementDuCookie('nelo_acces=secret')).toBe(null)
    expect(etablissementDuCookie('nelo_etablissement=')).toBe(null)
    expect(etablissementDuCookie(undefined)).toBe(null)
  })
})

describe('premierRattachement', () => {
  it('prend le premier identifiant que le refus rend, ou rien', () => {
    expect(premierRattachement({ etablissements: ['a', 'b'] })).toBe('a')
    expect(premierRattachement({ etablissements: [] })).toBe(null)
    expect(premierRattachement({})).toBe(null)
    expect(premierRattachement({ etablissements: 'a' })).toBe(null)
  })
})

describe('SourceApi', () => {
  it('lit le contexte avec l’établissement mémorisé', async () => {
    const { demandes, client } = doubler([CONTEXTE])
    const contexte = await new SourceApi(client, 'etab-1').charger()
    expect(contexte).toEqual(CONTEXTE)
    expect(demandes).toEqual([
      { methode: 'GET', chemin: '/moi/capacites', options: { etablissement: 'etab-1' } },
    ])
  })

  it('sans établissement mémorisé, relit sur le premier rattachement que le refus rend', async () => {
    const { demandes, client } = doubler([
      new ErreurApi('TEN_ETABLISSEMENT_REQUIS', 400, { etablissements: ['etab-9', 'etab-8'] }),
      CONTEXTE,
    ])
    expect(await new SourceApi(client).charger()).toEqual(CONTEXTE)
    expect(demandes[0]!.options.etablissement).toBeUndefined()
    expect(demandes[1]!.options.etablissement).toBe('etab-9')
  })

  it('rend null sans session, à la première lecture comme à la seconde', async () => {
    const { client } = doubler([new ErreurApi('AUT_JETON_MANQUANT', 401)])
    expect(await new SourceApi(client, 'etab-1').charger()).toBe(null)
    const second = doubler([
      new ErreurApi('TEN_ETABLISSEMENT_REQUIS', 400, { etablissements: ['etab-9'] }),
      new ErreurApi('AUT_SESSION_REVOQUEE', 401),
    ])
    expect(await new SourceApi(second.client).charger()).toBe(null)
  })

  it('laisse remonter un refus qui n’est ni l’absence de session ni l’en-tête manquant', async () => {
    const { client } = doubler([new ErreurApi('API_ERREUR_INTERNE', 500)])
    await expect(new SourceApi(client, 'etab-1').charger()).rejects.toBeInstanceOf(ErreurApi)
  })

  it('laisse remonter un refus d’en-tête qui ne nomme aucun rattachement', async () => {
    const { client } = doubler([new ErreurApi('TEN_ETABLISSEMENT_REQUIS', 400, {})])
    await expect(new SourceApi(client).charger()).rejects.toBeInstanceOf(ErreurApi)
  })
})
