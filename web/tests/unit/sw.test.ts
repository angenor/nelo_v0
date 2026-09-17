// FR-045 : le service worker est mince. Il précache les fichiers immuables, nettoie les anciens
// caches, accepte SKIP_WAITING, et rien d'autre : aucune donnée, aucune écriture, aucune file.
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const source = readFileSync(resolve(import.meta.dirname, '../../app/sw/sw.ts'), 'utf8')
const code = source.replace(/\/\/[^\n]*|\/\*[\s\S]*?\*\//g, '')

describe('app/sw/sw.ts', () => {
  it('précache, nettoie, et accepte SKIP_WAITING', () => {
    expect(code).toContain('precacheAndRoute(self.__WB_MANIFEST')
    expect(code).toContain('cleanupOutdatedCaches()')
    expect(code).toContain("'SKIP_WAITING'")
  })

  it('n’intercepte rien d’autre, ne lit aucun cache, ne touche aucune API ni aucune base', () => {
    expect(code).not.toMatch(/addEventListener\(\s*['"]fetch/)
    expect(code).not.toMatch(/caches\.(match|open|put)/)
    expect(code).not.toContain('/api/')
    expect(code).not.toMatch(/indexedDB|registerRoute|NetworkFirst|StaleWhileRevalidate|BackgroundSync|sync/)
  })

  it('tient en une quarantaine de lignes', () => {
    expect(source.split('\n').length).toBeLessThanOrEqual(40)
  })
})
