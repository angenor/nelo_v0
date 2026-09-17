// US3 : la coquille se compose depuis les capacités, jamais depuis un rôle (FR-021 à FR-026).
import { describe, expect, it, vi } from 'vitest'
import { composer, domaineDe } from '../../app/core/composition/composer'
import { DOMAINES } from '../../app/core/composition/registre'
import type { ContexteCapacites } from '../../app/core/contexte/types'
import { PERSONAS } from '../../app/core/demonstration/personas'

const un = PERSONAS['un-domaine']
const cinq = PERSONAS['cinq-domaines']
const sept = PERSONAS['sept-domaines']
const aucune = PERSONAS['aucune-capacite']

const avec = (codes: string[]): ContexteCapacites => ({
  ...sept,
  capacites: codes.map((code) => ({ code, perimetre: {} })),
})

describe('domaineDe', () => {
  it('rend le premier segment du code', () => {
    expect(domaineDe('vie_scolaire.appel.faire')).toBe('vie_scolaire')
    expect(domaineDe('finance.encaissement.saisir')).toBe('finance')
  })
})

describe('composer, sur les quatre personas', () => {
  it('un domaine : l’accueil est le domaine, ses entrées à plat, aucune famille', () => {
    const c = composer(un)
    expect(c.situation).toBe('MONO_DOMAINE')
    expect(c.domaines.map((d) => d.code)).toEqual(['vie_scolaire'])
    expect(c.domaines[0]!.entrees.map((e) => e.code)).toEqual(['appel_du_jour', 'absences', 'sanctions'])
    expect(c.familles).toEqual([])
    expect(c.accueil.route).toBe('/d/vie_scolaire')
  })

  it('cinq domaines : à plat, dans l’ordre du registre, accueil composé', () => {
    const c = composer(cinq)
    expect(c.situation).toBe('MULTI_PLAT')
    expect(c.domaines.map((d) => d.code)).toEqual([
      'scolarite',
      'vie_scolaire',
      'pedagogie',
      'evaluation',
      'communication',
    ])
    expect(c.familles).toEqual([])
    expect(c.accueil.route).toBe('/')
  })

  it('sept domaines : regroupés, familles non vides seulement, dans l’ordre', () => {
    const c = composer(sept)
    expect(c.situation).toBe('MULTI_FAMILLES')
    expect(c.familles.map((f) => [f.famille.code, f.domaines.map((d) => d.code)])).toEqual([
      ['ELEVES', ['scolarite', 'vie_scolaire']],
      ['ENSEIGNEMENT', ['pedagogie', 'evaluation', 'conseil']],
      ['GESTION', ['finance']],
      ['COMMUNICATION', ['communication']],
    ])
    expect(c.familles.every((f) => f.domaines.length > 0)).toBe(true)
  })

  it('aucune capacité : aucun domaine, aucune famille', () => {
    const c = composer(aucune)
    expect(c.situation).toBe('AUCUNE_CAPACITE')
    expect(c.domaines).toEqual([])
    expect(c.familles).toEqual([])
  })
})

describe('les règles de composition', () => {
  const cinqCodes = ['scolarite.a.b', 'vie_scolaire.a.b', 'pedagogie.a.b', 'evaluation.a.b', 'finance.a.b']

  it('reste à plat à cinq domaines et se regroupe à six', () => {
    expect(composer(avec(cinqCodes)).situation).toBe('MULTI_PLAT')
    expect(composer(avec([...cinqCodes, 'tenant.a.b'])).situation).toBe('MULTI_FAMILLES')
  })

  it('compte un domaine une fois, quel que soit son nombre de capacités', () => {
    const c = composer(avec(['finance.a.b', 'finance.c.d', 'finance.e.f']))
    expect(c.situation).toBe('MONO_DOMAINE')
    expect(c.domaines).toHaveLength(1)
  })

  it('ignore un domaine inconnu du registre, et le signale', () => {
    const signaler = vi.fn()
    const c = composer(avec(['inconnu.x.y', 'finance.encaissement.saisir']), signaler)
    expect(c.domaines.map((d) => d.code)).toEqual(['finance'])
    expect(signaler).toHaveBeenCalledWith('inconnu')
  })

  it('donne une entrée au domaine même quand l’objet de la capacité n’a pas d’écran connu', () => {
    const c = composer(avec(['finance.objet_inconnu.voir']))
    expect(c.domaines[0]!.entrees).toHaveLength(1)
    expect(c.domaines[0]!.entrees[0]!.route).toBe('/d/finance')
  })

  it('ne connaît aucun rôle et n’a aucun champ « désactivé »', () => {
    const c = composer(sept)
    const texte = JSON.stringify(c)
    expect(texte).not.toMatch(/\brole|desactive|disabled|grise/i)
    expect(JSON.stringify(DOMAINES)).not.toMatch(/\brole/i)
  })
})
