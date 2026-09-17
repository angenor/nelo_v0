// La configuration de l'application (specs/002-socle-interface/plan.md).
import tailwindcss from '@tailwindcss/vite'
import jetons from '../docs/design/tokens.json'
import { NOM, NOM_COURT } from './app/core/produit'

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
  telemetry: false,
  css: [
    '~/assets/css/theme.css',
    '~/assets/css/mesures.css',
    '~/assets/css/polices.css',
    '~/assets/css/jetons.css',
  ],
  vite: {
    plugins: [tailwindcss()],
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
