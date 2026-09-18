// Charge le contexte avant le premier rendu, une fois, au serveur ; le client le reçoit par la
// charge utile. Pose la langue de départ et l'attribut lang de <html>.
//
// Deux sources possibles (research.md R-10) : les personas de démonstration quand la
// construction les porte et que l'adresse en demande un, GET /moi/capacites sinon. Un contexte
// nul veut dire « aucune session » : le greffon ne lève pas, la garde de route conduit vers la
// connexion.
import type { ContexteCapacites } from '~/core/contexte/types'
import { etablissementDuCookie, SourceApi } from '~/core/contexte/api'
import { sourceDemandee } from '~/core/contexte/choix'
import { langueInitiale, SourceDemonstration } from '~/core/contexte/demonstration'
import type { SourceContexte } from '~/core/contexte/source'
import { estLangue } from '~/core/i18n/libelles'

export default defineNuxtPlugin({
  name: 'contexte',
  async setup() {
    const contexte = useState<ContexteCapacites | null>('contexte', () => null)
    // Un contexte nul est un résultat, pas une absence de résultat : sans ce témoin, le client
    // redemanderait au serveur ce que le rendu vient de lui dire.
    const charge = useState<boolean>('contexte-charge', () => false)
    const { langue } = useLibelles()
    if (!charge.value) {
      const route = useRoute()
      let source: SourceContexte
      if (sourceDemandee(__NELO_DEMONSTRATION__, route.query.persona) === 'demonstration') {
        source = new SourceDemonstration(route.query.persona, route.query.pack)
      } else {
        source = new SourceApi(useApi(), etablissementDuCookie(useRequestHeaders(['cookie']).cookie))
      }
      contexte.value = await source.charger()
      charge.value = true
      if (contexte.value) {
        const depart = langueInitiale(contexte.value)
        if (estLangue(depart)) langue.value = depart
      }
    }
    useHead({ htmlAttrs: { lang: langue } })
  },
})
