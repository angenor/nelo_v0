import { describe, expect, it } from 'vitest'
import type { Stockage } from '../../app/core/plateforme/plateforme'
import { attributTheme, ecrireTheme, lireTheme } from '../../app/core/theme'

function stockageDeTest(): Stockage & { valeurs: Map<string, string> } {
  const valeurs = new Map<string, string>()
  return {
    valeurs,
    disponible: true,
    lire: (cle) => valeurs.get(cle) ?? null,
    ecrire: (cle, valeur) => void valeurs.set(cle, valeur),
    effacer: (cle) => void valeurs.delete(cle),
  }
}

describe('le thème mémorisé sur l’appareil', () => {
  it('suit l’appareil tant que rien n’est mémorisé, ou si la valeur est inconnue', () => {
    const s = stockageDeTest()
    expect(lireTheme(s)).toBe('systeme')
    s.valeurs.set('theme', 'violet')
    expect(lireTheme(s)).toBe('systeme')
  })

  it('mémorise un thème forcé et l’oublie au retour à l’appareil', () => {
    const s = stockageDeTest()
    ecrireTheme(s, 'dark')
    expect(lireTheme(s)).toBe('dark')
    ecrireTheme(s, 'systeme')
    expect(s.valeurs.has('theme')).toBe(false)
  })

  it('suit l’appareil en « systeme », et un thème forcé sinon', () => {
    expect(attributTheme('systeme', false)).toBe('light')
    expect(attributTheme('systeme', true)).toBe('dark')
    expect(attributTheme('light', true)).toBe('light')
    expect(attributTheme('dark', false)).toBe('dark')
  })
})
