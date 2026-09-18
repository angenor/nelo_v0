// La configuration de l'application (specs/002-socle-interface/plan.md).
import { readdirSync } from 'node:fs'
import tailwindcss from '@tailwindcss/vite'
import jetons from '../docs/design/tokens.json'
import { NOM, NOM_COURT } from './app/core/produit'

/**
 * Les modules de la démonstration, lus dans leur dossier : aucune liste écrite à la main, et un
 * module ajouté là est couvert sans qu'on y pense (research.md R-10).
 */
const MODULES_DEMONSTRATION = new Set(
  readdirSync(new URL('app/core/demonstration', import.meta.url)).map((f) => f.replace(/\.[a-z]+$/, '')),
)

export default defineNuxtConfig({
  compatibilityDate: '2026-09-01',
  modules: [
    '@vite-pwa/nuxt',
    // La page de style n'existe que sur le serveur de développement (research.md R-12).
    (_options, nuxt) => {
      nuxt.hook('pages:extend', (pages) => {
        if (nuxt.options.dev) return
        const style = pages.findIndex((page) => page.path === '/style')
        if (style >= 0) pages.splice(style, 1)
      })
    },
  ],
  devtools: { enabled: false },
  hooks: {
    /**
     * Rien de la démonstration ne voyage tant qu'aucune adresse ne demande un persona
     * (research.md R-10). Ses morceaux sont des imports dynamiques : en production, la constante
     * les élague ; dans une construction d'essai ils existent, et le préchargement d'office les
     * ferait transférer à chaque premier affichage, contre la règle du premier affichage qui ne
     * transfère que ce qu'il montre (P-10).
     */
    'build:manifest'(manifeste) {
      for (const [cle, entree] of Object.entries(manifeste)) {
        const chemin = `${cle} ${entree.src ?? ''}`
        const nom = entree.name ?? ''
        if (chemin.includes('core/demonstration/') || MODULES_DEMONSTRATION.has(nom)) {
          entree.prefetch = false
        }
      }
    },
  },
  telemetry: false,
  // Ce que le déploiement pose, jamais le code (research.md R-09, R-14). `apiBase` est l'adresse
  // de l'API derrière le relais ; `cookiesSecure` se lève sur http://localhost, jamais ailleurs ;
  // l'indicatif par défaut est une donnée de déploiement, et n'a pas de valeur ici (principe V).
  runtimeConfig: {
    apiBase: 'http://localhost:8000',
    cookiesSecure: true,
    public: {
      indicatifDefaut: '',
    },
  },
  css: [
    '~/assets/css/theme.css',
    '~/assets/css/mesures.css',
    '~/assets/css/polices.css',
    '~/assets/css/jetons.css',
  ],
  vite: {
    plugins: [tailwindcss()],
    // La démonstration ne vit que dans les constructions d'essai (research.md R-10) : la
    // constante vaut false en production, la branche qui charge les personas est morte, et
    // l'empaqueteur l'élague avec eux.
    define: {
      __NELO_DEMONSTRATION__: JSON.stringify(process.env.NELO_DEMONSTRATION === '1'),
    },
  },
  nitro: {
    compressPublicAssets: true,
  },
  app: {
    head: {
      meta: [
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'theme-color', content: jetons.clair['--primary'] },
        { name: 'apple-mobile-web-app-capable', content: 'yes' },
        { name: 'mobile-web-app-capable', content: 'yes' },
        { name: 'apple-mobile-web-app-title', content: NOM_COURT },
      ],
      link: [
        { rel: 'apple-touch-icon', href: '/icones/180.png' },
        { rel: 'icon', type: 'image/png', sizes: '32x32', href: '/icones/32.png' },
      ],
    },
  },
  // L'application installable (research.md R-08) : le service worker est le nôtre, le module
  // n'y injecte que la liste des fichiers immuables ; le manifeste vient des jetons et du nom.
  pwa: {
    strategies: 'injectManifest',
    srcDir: 'sw',
    filename: 'sw.ts',
    registerType: 'prompt',
    injectManifest: {
      globPatterns: ['**/*.{js,css,html,woff2,png}'],
      globIgnores: ['**/*.woff'],
    },
    manifest: {
      id: '/',
      name: NOM,
      short_name: NOM_COURT,
      lang: 'fr',
      start_url: '/',
      scope: '/',
      display: 'standalone',
      theme_color: jetons.clair['--primary'],
      background_color: jetons.clair['--bg'],
      icons: [
        { src: '/icones/192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
        { src: '/icones/512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
        { src: '/icones/512-maskable.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
      ],
    },
    pwaAssets: { disabled: true },
    client: { installPrompt: false, periodicSyncForUpdates: 0 },
    devOptions: { enabled: false },
  },
  // Une page voisine se précharge quand on s'apprête à la suivre, pas dès que son lien est visible :
  // le premier affichage ne transfère que ce qu'il montre (P-10).
  experimental: {
    defaults: {
      nuxtLink: { prefetchOn: { visibility: false, interaction: true } },
    },
  },
  typescript: {
    strict: true,
    typeCheck: false,
  },
})
