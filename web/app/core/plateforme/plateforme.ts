// L'interface unique de plateforme (contracts/interfaces-client.md § 5, ADR 002). Aucun écran,
// aucun composant n'appelle une API du navigateur : ils passent par cette interface, dont
// web.ts est l'unique implémentation. Chaque capacité sait dire « indisponible » sans lever.

export const ETATS_RESEAU = ['bon', 'faible', 'absent'] as const
export type EtatReseau = (typeof ETATS_RESEAU)[number]

export interface Reseau {
  readonly etat: EtatReseau
  surChangement(rappel: (etat: EtatReseau) => void): () => void
}

export interface Stockage {
  readonly disponible: boolean
  lire(cle: string): string | null
  ecrire(cle: string, valeur: string): void
  effacer(cle: string): void
}

export interface Camera {
  readonly disponible: boolean
  capturer(): Promise<Blob | null>
}

export interface Notifications {
  readonly disponible: boolean
  demander(): Promise<'accordee' | 'refusee'>
  afficher(titre: string, corps: string): void
}

export interface Plateforme {
  reseau: Reseau
  stockage: Stockage
  camera: Camera
  notifications: Notifications
}
