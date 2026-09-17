import { describe, expect, it, vi } from 'vitest'
import en from '../../app/core/i18n/en.json'
import fr from '../../app/core/i18n/fr.json'
import { DICTIONNAIRES, estLangue, traduire } from '../../app/core/i18n/libelles'

describe('les dictionnaires', () => {
  it('portent exactement les mêmes clés en fr et en en', () => {
    expect(Object.keys(en).sort()).toEqual(Object.keys(fr).sort())
  })

  it('n’ont aucune valeur vide ni aucun tiret cadratin', () => {
    for (const dico of [fr, en]) {
      for (const [cle, valeur] of Object.entries(dico)) {
        expect(valeur.trim(), cle).not.toBe('')
        expect(valeur, cle).not.toContain('—')
      }
    }
  })

  it('nomment leurs clés en minuscules pointées, codes neutres permis en dernier segment', () => {
    for (const cle of Object.keys(fr)) {
      expect(cle).toMatch(/^[a-z_]+(\.[A-Za-z_]+)+$/)
    }
  })
})

describe('traduire', () => {
  const dico = { 'a.b': 'Bonjour {nom}', 'a.n': '{n} saisies', 'a.n.un': 'Une saisie' }

  it('remplace les paramètres', () => {
    expect(traduire(dico, 'a.b', { nom: 'Aline' })).toBe('Bonjour Aline')
    expect(traduire(dico, 'a.n', { n: 4 })).toBe('4 saisies')
  })

  it('emploie la variante « .un » quand n vaut 1', () => {
    expect(traduire(dico, 'a.n', { n: 1 })).toBe('Une saisie')
    expect(traduire(dico, 'a.b', { n: 1, nom: 'x' })).toBe('Bonjour x')
  })

  it('ne rend jamais une clé absente brute, et la signale', () => {
    const signaler = vi.fn()
    expect(traduire(dico, 'a.absente', undefined, signaler)).toBe('')
    expect(signaler).toHaveBeenCalledWith('a.absente')
  })

  it('résout une vraie clé dans les deux langues', () => {
    expect(traduire(DICTIONNAIRES.fr, 'ruban.hors_ligne')).toBe('Hors ligne')
    expect(traduire(DICTIONNAIRES.en, 'ruban.hors_ligne')).toBe('Offline')
    expect(estLangue('en')).toBe(true)
    expect(estLangue('de')).toBe(false)
  })
})
