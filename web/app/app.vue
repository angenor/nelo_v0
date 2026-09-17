<script setup lang="ts">
// Les trois fichiers du premier affichage sont préchargés ; leur adresse porte l'empreinte de
// la construction, d'où l'import plutôt qu'une adresse écrite dans nuxt.config.ts.
import publicSans400 from '@fontsource/public-sans/files/public-sans-latin-400-normal.woff2?url'
import publicSans500 from '@fontsource/public-sans/files/public-sans-latin-500-normal.woff2?url'
import archivo700 from '@fontsource/archivo/files/archivo-latin-700-normal.woff2?url'

const { attribut, installer } = useTheme()
let desabonner = () => {}
onMounted(() => {
  desabonner = installer()
})
onBeforeUnmount(() => desabonner())

useHead({
  htmlAttrs: { 'data-theme': attribut },
  link: [publicSans400, publicSans500, archivo700].map((href) => ({
    rel: 'preload',
    as: 'font',
    type: 'font/woff2',
    href,
    crossorigin: '',
  })),
})
</script>

<template>
  <main id="principal">
    <NuxtPage />
  </main>
</template>
