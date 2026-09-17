import type { Theme } from '~/core/theme'
import { attributTheme, ecrireTheme, lireTheme } from '~/core/theme'

/**
 * Le thème de l'application. Le rendu serveur ne le connaît pas (aucune valeur côté serveur) :
 * `installer` le lit sur l'appareil au montage, suit l'apparence demandée, et l'attribut suit.
 */
export function useTheme() {
  const plateforme = usePlateforme()
  const theme = useState<Theme>('theme', () => 'systeme')
  const sombre = useState('apparence-sombre', () => false)
  const monte = useState('theme-monte', () => false)
  return {
    theme,
    attribut: computed(() => (monte.value ? attributTheme(theme.value, sombre.value) : undefined)),
    installer: () => {
      theme.value = lireTheme(plateforme.stockage)
      sombre.value = plateforme.apparence.sombre
      monte.value = true
      return plateforme.apparence.surChangement((valeur) => {
        sombre.value = valeur
      })
    },
    forcer: (nouveau: Theme) => {
      theme.value = nouveau
      ecrireTheme(plateforme.stockage, nouveau)
    },
  }
}
