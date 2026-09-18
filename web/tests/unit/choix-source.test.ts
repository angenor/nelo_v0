// La source de contexte se choisit par une fonction pure (research.md R-10) : la démonstration
// ne sert que si la construction la porte et que l'adresse demande un persona.
import { describe, expect, it } from 'vitest'
import { sourceDemandee } from '../../app/core/contexte/choix'

describe('sourceDemandee', () => {
  it('sert l’API dès que la construction ne porte pas la démonstration', () => {
    expect(sourceDemandee(false, 'un-domaine')).toBe('api')
    expect(sourceDemandee(false, undefined)).toBe('api')
  })

  it('sert l’API quand l’adresse ne demande aucun persona', () => {
    expect(sourceDemandee(true, undefined)).toBe('api')
    expect(sourceDemandee(true, null)).toBe('api')
    expect(sourceDemandee(true, '')).toBe('api')
    expect(sourceDemandee(true, [])).toBe('api')
  })

  it('sert la démonstration quand les deux conditions tiennent', () => {
    expect(sourceDemandee(true, 'un-domaine')).toBe('demonstration')
    expect(sourceDemandee(true, 'inconnu')).toBe('demonstration')
    expect(sourceDemandee(true, ['sept-domaines'])).toBe('demonstration')
  })
})
