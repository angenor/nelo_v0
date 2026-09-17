// US5 : docs/design/lexique.md fige les mots ; les dictionnaires les portent. Chaque mot « On dit »
// existe là où le lexique dit qu'il vit, aucun mot « On ne dit jamais » n'apparaît dans fr.json,
// et chaque mot de la tranche est exactement la valeur de sa clé.
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import pack from '../../app/core/demonstration/pack-demonstration.json'
import fr from '../../app/core/i18n/fr.json'

const lexique = readFileSync(resolve(import.meta.dirname, '../../../docs/design/lexique.md'), 'utf8')
const valeurs = Object.values(fr as Record<string, string>)
const motsDuPack = Object.values(pack.vocabulaire).map((v) => v.fr)
const minuscule = (s: string) => s.toLocaleLowerCase('fr')

function tableau(titre: string): string[][] {
  const bloc = lexique.split(/^## /m).find((b) => b.startsWith(titre))
  if (!bloc) throw new Error(`lexique.md : section « ${titre} » absente`)
  return bloc
    .split('\n')
    .filter((l) => l.startsWith('|') && !/^\|\s*-/.test(l))
    .map((l) => l.split('|').slice(1, -1).map((c) => c.trim()))
    .filter((cellules) => !['On dit', 'Mot'].includes(cellules[0]!))
}

function contient(texte: string, mot: string): boolean {
  const echappe = mot.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return new RegExp(`(^|[^\\p{L}])${echappe}($|[^\\p{L}])`, 'iu').test(texte)
}

describe('docs/design/lexique.md', () => {
  const canonique = tableau('1.')

  it('porte les dix lignes du vocabulaire canonique de 05-design.md § 8.1', () => {
    expect(canonique).toHaveLength(10)
  })

  it.each(canonique)('« %s » vit là où le lexique le dit', (dit, _jamais, source) => {
    const mot = dit!.replace(/\*/g, '')
    if (source!.startsWith('`fr.json`')) expect(valeurs.some((v) => contient(v, mot)), mot).toBe(true)
    else if (source!.startsWith('pack')) expect(motsDuPack.map(minuscule)).toContain(minuscule(mot))
    else expect(source).toMatch(/^à venir/)
  })

  it('aucun mot « On ne dit jamais » n’apparaît dans fr.json', () => {
    const interdits = [...canonique.map((l) => l[1]!), ...tableau('2.').map((l) => l[1]!)]
      .flatMap((c) => c.replace(/\*\([^)]*\)\*/g, '').split(','))
      .map((m) => m.trim())
      .filter((m) => m && !m.includes('('))
    expect(interdits.length).toBeGreaterThan(10)
    for (const interdit of interdits) {
      const fautives = Object.entries(fr).filter(([, v]) => contient(v, interdit))
      expect(fautives, `« ${interdit} »`).toEqual([])
    }
  })

  it.each(tableau('3.'))('le mot « %s » est la valeur exacte de %s', (mot, cle) => {
    const nom = cle!.replace(/`/g, '')
    expect((fr as Record<string, string>)[nom], nom).toBe(mot)
  })

  it('ne porte aucun tiret cadratin', () => {
    expect(lexique).not.toContain('—')
  })
})
