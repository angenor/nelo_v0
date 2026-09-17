// Suit l'état du réseau par la plateforme, une fois l'hydratation entièrement terminée (pages
// asynchrones comprises), pour ne rien désaccorder avec le rendu serveur, et jusqu'à la fermeture.
export default defineNuxtPlugin({
  name: 'reseau',
  dependsOn: ['plateforme'],
  setup() {
    const plateforme = usePlateforme()
    const reseau = useReseau()
    onNuxtReady(() => {
      reseau.value = plateforme.reseau.etat
      plateforme.reseau.surChangement((etat) => {
        reseau.value = etat
      })
    })
  },
})
