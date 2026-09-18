<script setup lang="ts">
// La racine : la coquille composée depuis le contexte, les alertes du contexte, l'écran.
// Les trois fichiers de police du premier affichage sont préchargés ; leur adresse porte
// l'empreinte de la construction, d'où l'import plutôt qu'une adresse écrite dans nuxt.config.ts.
import archivo700 from '@fontsource/archivo/files/archivo-latin-700-normal.woff2?url'
import publicSans400 from '@fontsource/public-sans/files/public-sans-latin-400-normal.woff2?url'
import publicSans500 from '@fontsource/public-sans/files/public-sans-latin-500-normal.woff2?url'
import { presenterAlerte } from '~/core/composition/alertes'
import { SourceApi } from '~/core/contexte/api'
import type { ContexteCapacites } from '~/core/contexte/types'
import { CLE_REPRISE, CONNEXION } from '~/middleware/session.global'
import { NOM } from '~/core/produit'

const route = useRoute()
const router = useRouter()
const { contexte, composition } = useContexte()
const { attribut, installer } = useTheme()
const { annee, relire, choisirEtablissement, choisirAnnee } = useChoixAppareil()
const { fermer } = useSession()
const { t } = useLibelles()
const { renouveler } = useSession()
const api = useApi()
const etatContexte = useState<ContexteCapacites | null>('contexte', () => null)
/** Le client a-t-il déjà demandé un jeton neuf ? La garde de route lit le même témoin. */
const repriseTentee = useState<boolean>(CLE_REPRISE, () => false)

/**
 * L'écran attend pendant que le client reprend la main : un contexte nul sur une page à
 * coquille ne veut pas dire « pas de session », il veut dire « on ne sait pas encore ». Le
 * rendu du serveur ne porte pas le cookie de rafraîchissement et ne peut pas trancher.
 */
const enReprise = computed(() => etatContexte.value === null && !route.meta.sansCoquille)

const accueil = computed(() => composition.value.accueil.route)
const surAccueil = computed(() => route.path === '/' || route.path === accueil.value)
const alertes = computed(() =>
  contexte.value.alertes.map((a) => presenterAlerte(a, composition.value.domaines.map((d) => d.code))),
)

function retour() {
  if (router.options.history.state.back) router.back()
  else navigateTo(accueil.value)
}

/**
 * Changer d'établissement ou d'année : le choix s'écrit sur l'appareil, puis le contexte est
 * relu. Le serveur ne retient rien (FR-051) ; c'est le client qui reposera les deux en-têtes.
 */
async function changerEtablissement(identifiant: string) {
  choisirEtablissement(identifiant)
  await relireContexte()
}
async function changerAnnee(identifiant: string) {
  choisirAnnee(identifiant)
  await relireContexte()
}

/** Le contexte, relu par sa source, et les données de l'écran avec lui. */
async function relireContexte() {
  etatContexte.value = await new SourceApi(api).charger()
  await refreshNuxtData()
}

/**
 * Fermer la session : les jetons tombent, le cookie du relais est effacé, et la personne
 * revient à l'écran de connexion par un vrai chargement, où l'appareil reste connu.
 */
async function deconnexion() {
  await fermer()
  await navigateTo(CONNEXION, { external: true })
}

/**
 * Reprendre la session, une fois, dès que le client a la main (FR-013). Le jeton d'accès vaut
 * une heure ; quand il expire, la personne ne doit rien voir. Le cookie de rafraîchissement
 * n'accompagne que les appels sous `/api/v1/auth`, donc seul le navigateur peut le demander.
 *
 * Si le renouvellement réussit, le contexte est relu et l'écran s'ouvre là où la personne
 * était. S'il échoue, la session est bien finie, et la connexion prend le relais.
 */
async function reprendreLaSession() {
  if (route.meta.sansCoquille || etatContexte.value !== null || repriseTentee.value) return
  if (await renouveler()) {
    etatContexte.value = await new SourceApi(api).charger()
    if (etatContexte.value !== null) await refreshNuxtData()
  }
  repriseTentee.value = true
  if (etatContexte.value === null) await navigateTo(CONNEXION, { replace: true })
}

useMiseAJour()

const hydrate = ref(false)
let desabonner = () => {}
onMounted(() => {
  desabonner = installer()
  // Le choix d'établissement et d'année vit sur l'appareil : le rendu du serveur ne le lit que
  // par le cookie, le client le relit entier dès qu'il s'hydrate.
  relire()
  hydrate.value = true
  void reprendreLaSession()
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
  <!-- La session se reprend : un mot sobre, jamais une coquille vide ni un écran qui saute. -->
  <main v-else-if="enReprise" id="principal" class="reprise" aria-live="polite">
    <p class="reprise-titre">{{ t('session.reprise.titre') }}</p>
    <p class="reprise-corps">{{ t('session.reprise.corps') }}</p>
  </main>
  <CanonCoquille
    v-else
    :composition="composition"
    :contexte="contexte"
    :route-active="route.fullPath"
    :contexte-tactile="route.meta.contexteTactile ?? 'standard'"
    :montrer-retour="!surAccueil"
    :sur-accueil="surAccueil"
    :annee-choisie="annee"
    @retour="retour"
    @changer-etablissement="changerEtablissement"
    @changer-annee="changerAnnee"
    @deconnexion="deconnexion"
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
.reprise {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 100dvh;
  padding: 24px 16px;
  background: var(--bg);
  text-align: center;
}
.reprise-titre {
  margin: 0;
  font-family: var(--font-titres);
  font-weight: 700;
  font-size: 18px;
}
.reprise-corps {
  margin: 0;
  font-size: 14px;
  color: var(--text-muted);
}
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
