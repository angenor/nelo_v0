// Ouvre une fois chaque écran de développement dans Chromium, jusqu'à l'hydratation : Vite y
// compile et optimise ses dépendances avant que les tests ne comptent le temps.
import { chromium } from '@playwright/test'

const port = process.env.NELO_WEB_PORT_DEV ?? '4311'
const navigateur = await chromium.launch({ channel: 'chromium' })
try {
  const page = await navigateur.newPage()
  for (const route of ['/style']) {
    await page.goto(`http://localhost:${port}${route}`, { timeout: 120_000 })
    await page.locator('[data-hydrate]').waitFor({ state: 'attached', timeout: 120_000 })
  }
} finally {
  await navigateur.close()
}
