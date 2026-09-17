// Le thème et les mesures sont copiés tel quel : aucune seconde vérité (research.md R-02, R-17).
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const racine = resolve(import.meta.dirname, '../../..')

describe('les copies du système de design', () => {
  for (const nom of ['theme.css', 'mesures.css']) {
    it(`${nom} est identique octet pour octet à docs/design/${nom}`, () => {
      const source = readFileSync(resolve(racine, 'docs/design', nom))
      const copie = readFileSync(resolve(racine, 'web/app/assets/css', nom))
      expect(copie.equals(source)).toBe(true)
    })
  }
})
