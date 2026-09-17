// Charge le contexte avant le premier rendu, une fois, au serveur ; le client le reçoit par la
// charge utile. Pose la langue de départ et l'attribut lang de <html>.
import type { ContexteCapacites } from '~/core/contexte/types'
import { langueInitiale, SourceDemonstration } from '~/core/contexte/demonstration'
import { estLangue } from '~/core/i18n/libelles'

export default defineNuxtPlugin({
  name: 'contexte',
  async setup() {
    const contexte = useState<ContexteCapacites | null>('contexte', () => null)
    const { langue } = useLibelles()
    if (!contexte.value) {
      const route = useRoute()
      contexte.value = await new SourceDemonstration(route.query.persona, route.query.pack).charger()
      const depart = langueInitiale(contexte.value)
      if (estLangue(depart)) langue.value = depart
    }
    useHead({ htmlAttrs: { lang: langue } })
  },
})
