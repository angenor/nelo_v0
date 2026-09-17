// PORTE P-05 : chaque écran déclaré s'atteint dans un vrai navigateur, sur deux moteurs et deux
// thèmes, sans erreur de page ni de console (research.md R-12). Monter un composant dans un test
// ne prouve pas qu'une page s'atteint.
import { readdirSync } from 'node:fs'
import { join, relative } from 'node:path'
import { expect, test } from '@playwright/test'
import { ECRANS, THEMES, scriptTheme, visites } from './outils'

const PAGES = join(import.meta.dirname, '../../app/pages')

function routesDesPages(dossier = PAGES): string[] {
  return readdirSync(dossier, { withFileTypes: true }).flatMap((entree) => {
    const chemin = join(dossier, entree.name)
    if (entree.isDirectory()) return routesDesPages(chemin)
    if (!entree.name.endsWith('.vue')) return []
    const route = '/' + relative(PAGES, chemin).replace(/\.vue$/, '').replace(/(^|\/)index$/, '')
    return [route.replace(/\/$/, '') || '/']
  })
}

function correspond(motif: string, route: string): boolean {
  const expression = motif.replace(/\[[^\]]+\]/g, '[^/]+')
  return new RegExp(`^${expression}$`).test(route)
}

test('P-05 : chaque page de web/app/pages est déclarée dans ecrans.json', () => {
  for (const motif of routesDesPages()) {
    const declare = ECRANS.some((e) => correspond(motif, e.route))
    if (!declare) throw new Error(`PORTE P-05 ÉCHOUÉE : écran non déclaré ${motif}`)
  }
})

for (const visite of visites()) {
  for (const theme of THEMES) {
    test(`P-05 : ${visite.nom}, thème ${theme}`, async ({ page, browserName }) => {
      const erreurs: string[] = []
      page.on('pageerror', (e) => erreurs.push(`erreur de page : ${e.message}`))
      page.on('console', (m) => {
        if (m.type() === 'error') erreurs.push(`console : ${m.text()}`)
      })
      const echec = (motif: string) =>
        `PORTE P-05 ÉCHOUÉE : écran ${visite.nom}, moteur ${browserName}, thème ${theme} : ${motif}`

      await page.addInitScript(scriptTheme(theme))
      const reponse = await page.goto(visite.adresse, { timeout: 60_000 })
      expect(reponse?.status(), echec(`statut ${reponse?.status()}`)).toBeLessThan(400)
      await expect(page.locator('main#principal'), echec('repère main#principal absent')).toBeVisible()
      await expect(page.locator('html'), echec('thème non appliqué')).toHaveAttribute('data-theme', theme)
      await page.waitForLoadState('networkidle')
      expect(erreurs, echec(erreurs.join(' | '))).toEqual([])
    })
  }
}
