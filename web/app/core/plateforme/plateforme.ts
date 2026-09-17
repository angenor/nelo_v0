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

/** L'apparence demandée par l'appareil : theme.css ne la lit pas, le thème la suit par ici. */
export interface Apparence {
  readonly sombre: boolean
  surChangement(rappel: (sombre: boolean) => void): () => void
}

/** Les raccourcis du poste : une touche avec Ctrl, ou Commande sur les appareils qui l'emploient. */
export interface Clavier {
  libelle(touche: string): string
  surRaccourci(touche: string, rappel: () => void): () => void
}

export interface Plateforme {
  reseau: Reseau
  apparence: Apparence
  clavier: Clavier
  stockage: Stockage
  camera: Camera
  notifications: Notifications
}
