// Suit l'état du réseau par la plateforme, à partir du montage (pour ne rien désaccorder à
// l'hydratation) et jusqu'à la fermeture.
export default defineNuxtPlugin({
  name: 'reseau',
  dependsOn: ['plateforme'],
  setup(nuxtApp) {
    const plateforme = usePlateforme()
    const reseau = useReseau()
    nuxtApp.hook('app:mounted', () => {
      reseau.value = plateforme.reseau.etat
      plateforme.reseau.surChangement((etat) => {
        reseau.value = etat
      })
    })
  },
})
