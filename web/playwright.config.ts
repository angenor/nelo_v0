// Les navigateurs réels (research.md R-12 à R-14). Quatre projets :
//   setup    : ouvre la session semée et enregistre son état (T1a, research.md R-11) ;
//   chromium : les scénarios e2e et P-05 ;
//   webkit   : P-05, le seul moteur d'iOS ;
//   p10      : la mesure du poids, service worker bloqué pour compter une première visite.
// Chromium tourne en version complète, sans tête (channel « chromium ») : le navigateur réel.
//
// La session semée exige une API qui serve /auth/otp : tant qu'US1 ne l'a pas livrée, le projet
// « setup » échouerait. Il n'est donc déclaré que si NELO_SESSION_SEMEE vaut 1, et
// scripts/avec-serveur-dev.sh lit la même variable pour lancer l'API de test avec sa base semée.
// US1 la posera par défaut ; d'ici là, aucun code n'est commenté, une variable décide.
import { defineConfig, devices } from '@playwright/test'

const PORT = Number(process.env.NELO_WEB_PORT ?? 4310)
const SESSION_SEMEE = process.env.NELO_SESSION_SEMEE === '1'
const AVANT = SESSION_SEMEE ? ['setup'] : []

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
    ...(SESSION_SEMEE ? [{ name: 'setup', testMatch: ['session.setup.ts'] }] : []),
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'], channel: 'chromium' },
      dependencies: AVANT,
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
      testMatch: ['portes/p05.spec.ts'],
      dependencies: AVANT,
    },
    {
      name: 'p10',
      use: { ...devices['Desktop Chrome'], channel: 'chromium', serviceWorkers: 'block' },
      testMatch: ['portes/p10.spec.ts'],
      dependencies: AVANT,
    },
  ],
  webServer: {
    command: 'node .output/server/index.mjs',
    port: PORT,
    reuseExistingServer: false,
    env: {
      PORT: String(PORT),
      NITRO_PORT: String(PORT),
      // L'adresse de l'API que le relais joint, posée par scripts/avec-serveur-dev.sh.
      NUXT_API_BASE: process.env.NUXT_API_BASE ?? 'http://localhost:8000',
      // Sur http://localhost, un cookie Secure ne serait pas gardé par le navigateur.
      NUXT_COOKIES_SECURE: process.env.NUXT_COOKIES_SECURE ?? 'false',
    },
  },
})
