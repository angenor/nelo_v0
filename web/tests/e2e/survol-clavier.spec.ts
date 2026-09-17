// US8 : le survol ne révèle rien ; le clavier atteint chaque action, et le focus se voit.
import type { Page } from '@playwright/test'
import { expect, test } from '@playwright/test'
import { PORT_DEV } from '../portes/outils'

const visibles = (page: Page) =>
  page.evaluate(() => [...document.querySelectorAll('body *')].filter((e) => (e as HTMLElement).checkVisibility?.()).length)

for (const adresse of ['/?persona=sept-domaines', '/d/vie_scolaire', '/a-propos']) {
  test(`${adresse} : survoler chaque zone ne fait rien apparaître`, async ({ page }) => {
    await page.setViewportSize({ width: 1200, height: 900 })
    await page.goto(adresse)
    await expect(page.locator('[data-hydrate]')).toHaveCount(1)
    const avant = await visibles(page)
    for (const cible of await page.locator('a:visible, button:visible, input:visible, select:visible').all()) {
      await cible.hover({ trial: false }).catch(() => {})
      expect(await visibles(page), await cible.evaluate((e) => e.outerHTML.slice(0, 80))).toBe(avant)
    }
  })
}

for (const adresse of ['/?persona=sept-domaines', '/d/vie_scolaire', `http://localhost:${PORT_DEV}/style`]) {
  test(`${adresse} : la tabulation parcourt les actions dans l’ordre, le focus se voit`, async ({ page }) => {
    await page.setViewportSize({ width: 1200, height: 900 })
    await page.goto(adresse, { timeout: 60_000 })
    await expect(page.locator('[data-hydrate]')).toHaveCount(1, { timeout: 30_000 })
    const attendues = await page
      .locator('a:visible, button:visible:not([disabled]), input:visible:not([disabled]), select:visible:not([disabled])')
      .count()
    const vus: string[] = []
    for (let i = 0; i < Math.min(attendues, 40) + 5; i++) {
      await page.keyboard.press('Tab')
      const etat = await page.evaluate((rang) => {
        const actif = document.activeElement as HTMLElement | null
        if (!actif || actif === document.body) return null
        const deja = actif.dataset.parcours !== undefined
        actif.dataset.parcours ??= String(rang)
        const porteurs = [actif, actif.parentElement, actif.nextElementSibling].filter(Boolean) as Element[]
        const visible = porteurs.some((e) => {
          const s = getComputedStyle(e)
          return (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0) || s.boxShadow !== 'none'
        })
        return { cle: actif.outerHTML.slice(0, 80), deja, visible, focus: actif.matches(':focus-visible') }
      }, i)
      if (!etat) continue
      if (etat.deja) break
      vus.push(etat.cle)
      expect(etat.focus, etat.cle).toBe(true)
      expect(etat.visible, `focus invisible : ${etat.cle}`).toBe(true)
    }
    expect(vus.length).toBeGreaterThan(3)
    expect(vus.length).toBeGreaterThanOrEqual(Math.min(attendues, 40))
  })
}
