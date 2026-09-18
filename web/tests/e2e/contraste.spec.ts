// US8 : le contraste AA, en clair et en sombre (FR-085, 05-design.md § 9.4).
import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'
import { PORT_DEV } from '../portes/outils'
import { scriptTheme } from '../portes/outils'

const ECRANS = [`http://localhost:${PORT_DEV}/style`, '/?persona=sept-domaines', '/d/vie_scolaire?persona=un-domaine', '/?persona=aucune-capacite']

for (const theme of ['light', 'dark']) {
  for (const adresse of ECRANS) {
    test(`${adresse}, thème ${theme} : aucun contraste sous AA`, async ({ page }) => {
      await page.addInitScript(scriptTheme(theme))
      await page.goto(adresse, { timeout: 60_000 })
      await expect(page.locator('html')).toHaveAttribute('data-theme', theme, { timeout: 30_000 })
      await page.emulateMedia({ reducedMotion: 'reduce' })
      const resultat = await new AxeBuilder({ page }).withRules(['color-contrast']).analyze()
      const fautes = resultat.violations.flatMap((v) =>
        v.nodes.map((n) => `${n.target.join(' ')} : ${n.any[0]?.message ?? v.help}`),
      )
      expect(fautes).toEqual([])
    })
  }
}
