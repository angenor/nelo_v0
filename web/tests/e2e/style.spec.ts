// US1 : la page de style montre les quatorze composants, chaque état en clair et en sombre,
// et elle n'existe que sur le serveur de développement.
import { existsSync, readdirSync } from 'node:fs'
import { join } from 'node:path'
import { expect, test } from '@playwright/test'
import { COMPOSANTS } from '../../app/core/composants/etats'
import { PORT_DEV } from '../portes/outils'

const STYLE = `http://localhost:${PORT_DEV}/style`

test('la page de style porte quatorze sections, chaque état dans les deux thèmes', async ({ page }) => {
  await page.goto(STYLE, { timeout: 60_000 })
  const sections = page.locator('section[data-composant]')
  await expect(sections).toHaveCount(14)
  for (const [nom, enumerations] of Object.entries(COMPOSANTS)) {
    const section = page.locator(`section[data-composant="${nom}"]`)
    await expect(section, nom).toHaveCount(1)
    const valeurs = new Set(Object.values(enumerations).flat() as string[])
    for (const theme of ['light', 'dark']) {
      const conteneur = section.locator(`[data-theme="${theme}"]`)
      await expect(conteneur, `${nom} ${theme}`).toHaveCount(1)
      const rendus = await conteneur
        .locator('[data-etat]')
        .evaluateAll((els) => els.flatMap((e) => (e.getAttribute('data-etat') ?? '').split(' ')))
      for (const valeur of valeurs) {
        expect(rendus, `${nom} ${theme} : état « ${valeur} » absent`).toContain(valeur)
      }
    }
  }
})

test('les deux thèmes sont côte à côte, clair à gauche', async ({ page }) => {
  await page.setViewportSize({ width: 1200, height: 900 })
  await page.goto(STYLE, { timeout: 60_000 })
  const section = page.locator('section[data-composant="Bouton"]')
  const clair = await section.locator('[data-theme="light"]').boundingBox()
  const sombre = await section.locator('[data-theme="dark"]').boundingBox()
  expect(clair && sombre && clair.x < sombre.x && Math.abs(clair.y - sombre.y) < 2).toBe(true)
})

test('la construction ne contient aucune route de style', () => {
  const sortie = join(import.meta.dirname, '../../.output')
  expect(existsSync(sortie)).toBe(true)
  const fichiers = readdirSync(sortie, { recursive: true }).map(String)
  expect(fichiers.filter((f) => /(^|\/)style(\.|\/)/.test(f) || /style-[A-Za-z0-9_-]+\.m?js$/.test(f))).toEqual([])
})
