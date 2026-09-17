// Fournit l'unique implémentation de la plateforme au client (research.md R-09). Capacitor ou
// Tauri fourniront demain la leur ici, sans toucher un écran.
import { creerPlateformeWeb } from '~/core/plateforme/web'

export default defineNuxtPlugin({
  name: 'plateforme',
  setup: () => ({ provide: { plateforme: creerPlateformeWeb() } }),
})
