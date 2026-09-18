// Laquelle des deux sources sert ce rendu (research.md R-10). Une fonction pure, pour que le
// choix se lise et se teste sans monter l'application.
//
// La démonstration ne sert que si la construction la porte (`__NELO_DEMONSTRATION__`, posée à la
// construction par NELO_DEMONSTRATION=1) et que l'adresse demande un persona. En production la
// constante vaut false : la branche est morte, les personas sont élagués.

export const SOURCES = ['demonstration', 'api'] as const
export type NomSource = (typeof SOURCES)[number]

export function sourceDemandee(demonstration: boolean, persona: unknown): NomSource {
  if (!demonstration) return 'api'
  const demande = Array.isArray(persona) ? persona[0] : persona
  return typeof demande === 'string' && demande !== '' ? 'demonstration' : 'api'
}
