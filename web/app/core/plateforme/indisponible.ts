// La plateforme telle que la voit le rendu serveur : tout est « indisponible », rien ne lève.
// Le réseau se dit bon par défaut ; le client le corrige dès qu'il s'hydrate.
import type { Plateforme } from './plateforme'

export const PLATEFORME_INDISPONIBLE: Plateforme = {
  reseau: { etat: 'bon', surChangement: () => () => {} },
  apparence: { sombre: false, surChangement: () => () => {} },
  clavier: { libelle: (touche) => `Ctrl ${touche.toUpperCase()}`, surRaccourci: () => () => {} },
  stockage: { disponible: false, lire: () => null, ecrire: () => {}, effacer: () => {} },
  camera: { disponible: false, capturer: async () => null },
  notifications: { disponible: false, demander: async () => 'refusee', afficher: () => {} },
}
