import type { Theme } from '~/core/theme'
import { attributTheme, ecrireTheme, lireTheme } from '~/core/theme'

/**
 * Le thème de l'application. Le rendu serveur ne le connaît pas (aucune valeur côté serveur) :
 * il se lit sur l'appareil au montage, et l'attribut suit.
 */
export function useTheme() {
  const plateforme = usePlateforme()
  const theme = useState<Theme>('theme', () => 'systeme')
  return {
    theme,
    charger: () => {
      theme.value = lireTheme(plateforme.stockage)
    },
    forcer: (nouveau: Theme) => {
      theme.value = nouveau
      ecrireTheme(plateforme.stockage, nouveau)
    },
    attribut: computed(() => attributTheme(theme.value)),
  }
}
