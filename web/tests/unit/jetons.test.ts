// La passerelle Tailwind ne porte aucune valeur de couleur (research.md R-02).
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const css = resolve(import.meta.dirname, '../../app/assets/css')
const jetons = readFileSync(resolve(css, 'jetons.css'), 'utf8')
const mesures = readFileSync(resolve(css, 'mesures.css'), 'utf8')
const theme = readFileSync(resolve(css, 'theme.css'), 'utf8')

function sansCommentaires(texte: string): string {
  return texte.replace(/\/\*[\s\S]*?\*\//g, '')
}

describe('jetons.css', () => {
  it('ne contient aucune valeur de couleur', () => {
    const code = sansCommentaires(jetons)
    expect(code).not.toMatch(/#[0-9a-f]{3,8}\b/i)
    expect(code).not.toMatch(/\b(rgba?|hsla?|oklch|oklab|lab|lch|color-mix)\(/i)
  })

  it('renvoie à chaque jeton de couleur du thème, et à rien d’autre', () => {
    const duTheme = new Set([...theme.matchAll(/(--[a-z-]+):#/g)].map((m) => m[1]))
    const references = [...jetons.matchAll(/--color-[a-z-]+:\s*var\((--[a-z-]+)\)/g)].map((m) => m[1])
    expect(new Set(references)).toEqual(duTheme)
  })

  it('répète les deux points de rupture de mesures.css, à l’identique', () => {
    const deux = mesures.match(/--rupture-deux-colonnes:\s*([0-9]+px)/)?.[1]
    const trois = mesures.match(/--rupture-trois-colonnes:\s*([0-9]+px)/)?.[1]
    expect(jetons).toContain(`--breakpoint-md: ${deux};`)
    expect(jetons).toContain(`--breakpoint-xl: ${trois};`)
    expect([...jetons.matchAll(/--breakpoint-[a-z0-9]+:\s*[0-9]/g)]).toHaveLength(2)
  })
})
