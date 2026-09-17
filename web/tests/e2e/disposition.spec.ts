// US8 : 390 px d'abord ; aucun défilement horizontal ; le tableau se transforme en cartes ;
// l'action principale est en bas, pleine largeur ; 125 % ne casse rien (05-design.md § 9.2).
import type { Page } from '@playwright/test'
import { expect, test } from '@playwright/test'
import { PORT_DEV } from '../portes/outils'

const ECRANS = ['/?persona=sept-domaines', '/d/vie_scolaire', '/a-propos', `http://localhost:${PORT_DEV}/style`]

async function debordement(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const fautifs: string[] = []
    if (document.documentElement.scrollWidth > window.innerWidth + 1) fautifs.push('document')
    const principal = document.querySelector('main')
    if (principal && principal.scrollWidth > principal.clientWidth + 1) fautifs.push('main')
    return fautifs
  })
}

for (const largeur of [390, 768, 1200]) {
  for (const ecran of ECRANS) {
    test(`${largeur} px, ${ecran} : aucun défilement horizontal, à 100 % et à 125 %`, async ({ page }) => {
      await page.setViewportSize({ width: largeur, height: 844 })
      await page.goto(ecran, { timeout: 60_000 })
      await expect(page.locator('main')).toBeVisible()
      expect(await debordement(page)).toEqual([])
      await page.evaluate(() => {
        document.documentElement.style.zoom = '1.25'
      })
      expect(await debordement(page)).toEqual([])
    })
  }
}

test('le tableau suit la largeur : cartes à 390 px, lignes à 768 px', async ({ page }) => {
  const affichage = () =>
    page.locator('[data-mode-demande="auto"] tbody tr').first().evaluate((e) => getComputedStyle(e).display)
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto(`http://localhost:${PORT_DEV}/style`, { timeout: 60_000 })
  expect(await affichage()).toBe('block')
  await expect(page.locator('[data-mode-demande="auto"] thead').first()).toHaveCSS('position', 'absolute')
  await page.setViewportSize({ width: 768, height: 844 })
  expect(await affichage()).toBe('table-row')
})

test('à 390 px, l’action principale de l’appel est en bas et pleine largeur', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/d/vie_scolaire')
  const bouton = (await page.locator('.bouton--principal').boundingBox())!
  expect(bouton.width).toBeGreaterThanOrEqual(390 - 32 - 1)
  expect(bouton.y).toBeGreaterThan(844 / 2)
})
