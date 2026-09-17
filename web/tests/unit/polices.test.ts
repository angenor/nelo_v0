// Les polices servies existent, et l'on sait si elles portent l'espace fine insécable
// (research.md R-07, écart E-06).
import { execFileSync } from 'node:child_process'
import { existsSync, readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const web = resolve(import.meta.dirname, '../..')
const require = createRequire(resolve(web, 'package.json'))
const css = readFileSync(resolve(web, 'app/assets/css/polices.css'), 'utf8')
const references = [...css.matchAll(/url\('([^']+)'\)/g)].map((m) => m[1]!)
const fichiers = references.map((r) => require.resolve(r))

function fonttools(chemins: string[]): Record<string, boolean> | null {
  const script =
    'import json,sys\nfrom fontTools.ttLib import TTFont\n' +
    'print(json.dumps({p: 0x202F in TTFont(p).getBestCmap() for p in sys.argv[1:]}))'
  try {
    const sortie = execFileSync(
      'uvx',
      ['--offline', '--with', 'brotli', '--from', 'fonttools', 'python', '-c', script, ...chemins],
      { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] },
    )
    return JSON.parse(sortie)
  } catch {
    return null
  }
}

describe('polices.css', () => {
  it('référence quatre fichiers woff2 du sous-ensemble latin, tous présents', () => {
    expect(references).toHaveLength(4)
    for (const [i, f] of fichiers.entries()) {
      expect(references[i]).toMatch(/-latin-[0-9]{3}-normal\.woff2$/)
      expect(existsSync(f)).toBe(true)
    }
  })

  it('déclare chaque police en font-display: swap', () => {
    expect(css.match(/@font-face/g)).toHaveLength(4)
    expect(css.match(/font-display: swap/g)).toHaveLength(4)
  })

  it('dit quels fichiers portent U+202F, et laisse la police de repli le rendre sinon', () => {
    const jetons = readFileSync(resolve(web, 'app/assets/css/jetons.css'), 'utf8')
    for (const famille of ['--font-titres', '--font-texte', '--font-mono']) {
      expect(jetons).toMatch(new RegExp(`${famille}: [^;]+, (system-ui|ui-monospace), `))
    }
    const glyphes = fonttools(fichiers)
    if (glyphes === null) {
      console.warn('AVERTISSEMENT polices : fonttools indisponible, U+202F non vérifié')
      return
    }
    const sans = Object.entries(glyphes)
      .filter(([, present]) => !present)
      .map(([p]) => p.split('/').pop())
    if (sans.length > 0) {
      console.warn(
        `AVERTISSEMENT polices : U+202F absent de ${sans.length} fichier(s), rendu par la police de repli (E-06) : ${sans.join(', ')}`,
      )
    }
    expect(Object.keys(glyphes)).toHaveLength(4)
  })
})
