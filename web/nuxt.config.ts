// La configuration de l'application (specs/002-socle-interface/plan.md).
import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  compatibilityDate: '2026-09-01',
  modules: [
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
      meta: [{ name: 'viewport', content: 'width=device-width, initial-scale=1' }],
    },
  },
  typescript: {
    strict: true,
    typeCheck: false,
  },
})
