// FR-092 : la page de style, le document et le composant lisent la même énumération.
// docs/design/composants.md est la source ; chaque composant la réexporte depuis
// core/composants/etats.ts, et ses valeurs sont exactement celles du document.
import { existsSync, readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
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

// E-02 de T1a : la saisie de code n'est ni un type ni un état, c'est une prop qui pose trois
// attributs sur le champ de texte. Le gabarit est lu tel que le compilateur le voit.
describe('Champ : la saisie de code', () => {
  const { parse } = createRequire(resolve(racine, 'web/package.json'))('@vue/compiler-sfc') as {
    parse: (source: string, options: { filename: string }) => { descriptor: { template?: { ast?: Noeud } } }
  }
  const fichier = resolve(canon, 'Champ.vue')
  const { descriptor } = parse(readFileSync(fichier, 'utf8'), { filename: fichier })

  interface Noeud {
    type: number
    tag?: string
    props?: { type: number; name?: string; arg?: { content?: string }; exp?: { content?: string } }[]
    children?: Noeud[]
    branches?: Noeud[]
  }

  function elements(noeud: Noeud, tag: string): Noeud[] {
    const trouves = noeud.tag === tag ? [noeud] : []
    for (const enfant of [...(noeud.children ?? []), ...(noeud.branches ?? [])]) {
      trouves.push(...elements(enfant, tag))
    }
    return trouves
  }

  function liaison(noeud: Noeud, nom: string): string | undefined {
    return noeud.props?.find((p) => p.type === 7 && p.arg?.content === nom)?.exp?.content
  }

  const saisies = elements(descriptor.template!.ast!, 'input')
  const texte = saisies.find((noeud) => liaison(noeud, 'inputmode') !== undefined)

  it('rend un champ de texte, jamais un composant neuf', () => {
    expect(texte, 'aucun <input> avec un inputmode lié dans Champ.vue').toBeDefined()
  })

  it('pose le clavier numérique, le remplissage du code reçu et le motif de chiffres', () => {
    expect(liaison(texte!, 'inputmode')).toBe('mode')
    expect(liaison(texte!, 'autocomplete')).toContain("'one-time-code'")
    expect(liaison(texte!, 'pattern')).toContain("'[0-9]*'")
    expect(liaison(texte!, 'class')).toContain('code')
  })

  it('n’ajoute aucun état : la prop vaut texte ou code, et rien de plus', () => {
    expect([...COMPOSANTS.Champ.SAISIES]).toEqual(['texte', 'code'])
    expect([...COMPOSANTS.Champ.ETATS]).toEqual(['repos', 'focus', 'erreur', 'inactif'])
  })
})
