// Les navigateurs réels (research.md R-12 à R-14). Trois projets :
//   chromium : les scénarios e2e et P-05 ;
//   webkit   : P-05, le seul moteur d'iOS ;
//   p10      : la mesure du poids, service worker bloqué pour compter une première visite.
import { defineConfig, devices } from '@playwright/test'

const PORT = Number(process.env.NELO_WEB_PORT ?? 4310)

export default defineConfig({
  testDir: 'tests',
  testMatch: ['e2e/**/*.spec.ts', 'portes/**/*.spec.ts'],
  fullyParallel: true,
  forbidOnly: true,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: `http://localhost:${PORT}`,
    trace: 'off',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] }, testMatch: ['portes/p05.spec.ts'] },
    {
      name: 'p10',
      use: { ...devices['Desktop Chrome'], serviceWorkers: 'block' },
      testMatch: ['portes/p10.spec.ts'],
    },
  ],
  webServer: {
    command: 'node .output/server/index.mjs',
    port: PORT,
    reuseExistingServer: false,
    env: { PORT: String(PORT), NITRO_PORT: String(PORT) },
  },
})
