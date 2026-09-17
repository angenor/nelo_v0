// FR-092 : la page de style, le document et le composant lisent la même énumération.
// docs/design/composants.md est la source ; chaque composant la réexporte depuis
// core/composants/etats.ts, et ses valeurs sont exactement celles du document.
import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { COMPOSANTS } from '../../app/core/composants/etats'

const racine = resolve(import.meta.dirname, '../../..')
const canon = resolve(racine, 'web/app/components/canon')
const document = readFileSync(resolve(racine, 'docs/design/composants.md'), 'utf8')

interface Section {
  titre: string
  fichier: string
  enumerations: Record<string, string[]>
}

function lireSections(texte: string): Section[] {
  return texte
    .split(/^### /m)
    .slice(1)
    .filter((bloc) => /^\d+\. /.test(bloc))
    .map((bloc) => {
      const titre = bloc.split('\n')[0]!.trim()
      const fichier = /Fichier : `([A-Za-z]+\.vue)`/.exec(bloc)?.[1] ?? ''
      const enumerations: Record<string, string[]> = {}
      let dansLeTableau = false
      for (const ligne of bloc.split('\n')) {
        if (/^\| Énumération \| Valeurs \|/.test(ligne)) dansLeTableau = true
        else if (!ligne.startsWith('|')) dansLeTableau = false
        const m = dansLeTableau ? /^\| `([A-Z_]+)` \| (.+?) \|$/.exec(ligne) : null
        if (m) enumerations[m[1]!] = [...m[2]!.matchAll(/`([^`]+)`/g)].map((v) => v[1]!)
      }
      return { titre, fichier, enumerations }
    })
}

const sections = lireSections(document)

describe('docs/design/composants.md', () => {
  it('décrit quatorze composants numérotés, chacun avec son fichier', () => {
    expect(sections.map((s) => s.titre.split('.')[0])).toEqual(
      Array.from({ length: 14 }, (_, i) => String(i + 1)),
    )
    for (const s of sections) expect(s.fichier, s.titre).not.toBe('')
  })

  it('ne porte aucun tiret cadratin', () => {
    expect(document).not.toContain('—')
  })
})

describe.each(sections)('$titre', ({ fichier, enumerations }) => {
  it('existe dans components/canon et réexporte ses énumérations', () => {
    const chemin = resolve(canon, fichier)
    expect(existsSync(chemin), fichier).toBe(true)
    const source = readFileSync(chemin, 'utf8')
    const nom = fichier.replace('.vue', '')
    if (Object.keys(enumerations).length > 0) {
      expect(source).toMatch(new RegExp(`export const ETATS_COMPOSANT = COMPOSANTS\\.${nom}\\b`))
    }
  })

  it('a exactement les énumérations et les valeurs du document', () => {
    const nom = fichier.replace('.vue', '') as keyof typeof COMPOSANTS
    const exportees = Object.fromEntries(
      Object.entries(COMPOSANTS[nom] ?? {}).map(([k, v]) => [k, [...(v as readonly string[])]]),
    )
    expect(exportees).toEqual(enumerations)
  })
})
