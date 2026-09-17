<script setup lang="ts">
// La racine : la coquille composée depuis le contexte, les alertes du contexte, l'écran.
// Les trois fichiers de police du premier affichage sont préchargés ; leur adresse porte
// l'empreinte de la construction, d'où l'import plutôt qu'une adresse écrite dans nuxt.config.ts.
import archivo700 from '@fontsource/archivo/files/archivo-latin-700-normal.woff2?url'
import publicSans400 from '@fontsource/public-sans/files/public-sans-latin-400-normal.woff2?url'
import publicSans500 from '@fontsource/public-sans/files/public-sans-latin-500-normal.woff2?url'
import { presenterAlerte } from '~/core/composition/alertes'
import { NOM } from '~/core/produit'

const route = useRoute()
const router = useRouter()
const { contexte, composition } = useContexte()
const { attribut, installer } = useTheme()

const accueil = computed(() => composition.value.accueil.route)
const surAccueil = computed(() => route.path === '/' || route.path === accueil.value)
const alertes = computed(() =>
  contexte.value.alertes.map((a) => presenterAlerte(a, composition.value.domaines.map((d) => d.code))),
)

function retour() {
  if (router.options.history.state.back) router.back()
  else navigateTo(accueil.value)
}

useMiseAJour()

const hydrate = ref(false)
let desabonner = () => {}
onMounted(() => {
  desabonner = installer()
  hydrate.value = true
})
onBeforeUnmount(() => desabonner())

useHead({
  title: NOM,
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
  <main v-if="route.meta.sansCoquille" id="principal">
    <NuxtPage />
  </main>
  <CanonCoquille
    v-else
    :composition="composition"
    :contexte="contexte"
    :route-active="route.fullPath"
    :contexte-tactile="route.meta.contexteTactile ?? 'standard'"
    :montrer-retour="!surAccueil"
    :sur-accueil="surAccueil"
    @retour="retour"
  >
    <div v-if="alertes.length" class="alertes">
      <CanonAlerte
        v-for="alerte in alertes"
        :key="alerte.type"
        :data-alerte="alerte.type"
        :niveau="alerte.niveau"
        :titre="alerte.titre"
        :corps="alerte.corps"
        :parametres="alerte.parametres"
        :action="alerte.action"
      />
    </div>
    <NuxtPage />
  </CanonCoquille>
  <NuxtPwaManifest />
  <span v-if="hydrate" data-hydrate hidden />
</template>

<style scoped>
.alertes {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  max-width: 760px;
  margin: 0 auto;
  padding: 16px 16px 0;
}
</style>
