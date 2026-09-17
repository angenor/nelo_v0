import { describe, expect, it } from 'vitest'
import { ECRANS, valider } from '../../app/core/ecrans'

describe('ecrans.json', () => {
  it('se lit et déclare l’accueil avec ses deux plafonds', () => {
    const accueil = ECRANS.find((e) => e.nom === 'accueil')
    expect(accueil?.route).toBe('/')
    expect(accueil?.budgetKo).toBe(120)
    expect(accueil?.budgetPolicesKo).toBe(45)
  })

  it('refuse un budget qui n’est pas un entier positif', () => {
    expect(() => valider([{ nom: 'x', route: '/x', budgetKo: 0 }])).toThrow(/entier positif/)
    expect(() => valider([{ nom: 'x', route: '/x', budgetKo: 12.5 }])).toThrow(/entier positif/)
    expect(() => valider([{ nom: 'x', route: '/x', budgetKo: '120' }])).toThrow(/entier positif/)
  })

  it('refuse un écran de développement budgété', () => {
    expect(() => valider([{ nom: 's', route: '/s', budgetKo: 10, developpement: true }])).toThrow(
      /développement/,
    )
    expect(valider([{ nom: 's', route: '/s', budgetKo: null, developpement: true }])).toHaveLength(1)
  })

  it('refuse un doublon, une route sans barre et une liste vide', () => {
    const e = { nom: 'a', route: '/a', budgetKo: null }
    expect(() => valider([e, e])).toThrow(/deux fois/)
    expect(() => valider([{ ...e, route: 'a' }])).toThrow(/route/)
    expect(() => valider([])).toThrow(/vide/)
  })
})
