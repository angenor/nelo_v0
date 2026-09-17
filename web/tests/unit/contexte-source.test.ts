// US5 et US3 : la source de démonstration choisit le persona et le pack ; la langue de départ
// est celle du compte si le pack la porte, sinon la première du pack (FR-052).
import { describe, expect, it } from 'vitest'
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
