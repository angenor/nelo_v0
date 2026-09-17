/**
 * Une nouvelle version s'applique d'elle-même (FR-042) : quand un service worker attend, et
 * seulement quand aucune saisie n'est en attente ni en cours dans un champ, il prend la main et
 * l'application se recharge par la plateforme. Sinon, on attend ; à défaut, la prochaine
 * ouverture l'applique. Aucun message ne demande jamais de recharger la page.
 */
export function useMiseAJour() {
  const nuxtApp = useNuxtApp()
  const plateforme = usePlateforme()
  const { enAttente } = useSaisieDemonstration()
  const enCours = ref(false)

  async function appliquer() {
    const pwa = nuxtApp.$pwa
    if (!pwa?.needRefresh || enCours.value) return
    if (enAttente.value > 0 || plateforme.application.saisieEnCours()) return
    enCours.value = true
    await pwa.updateServiceWorker(false)
    plateforme.application.recharger()
  }

  onMounted(() => {
    const arreter = watch([() => nuxtApp.$pwa?.needRefresh, enAttente], appliquer, { immediate: true })
    const minuterie = setInterval(appliquer, 5_000)
    onBeforeUnmount(() => {
      arreter()
      clearInterval(minuterie)
    })
  })
}
