<script lang="ts">
// Les icônes de la tranche, dessinées ici en SVG (research.md R-20) : aucune bibliothèque,
// aucune attribution. Traits de 1,8 sur une grille de 24, couleur du texte courant.
const TRACES = {
  coche: ['M5 13l4 4L19 7'],
  lien_barre: ['M2 8.5a15 15 0 0 1 20 0', 'M5 12a10 10 0 0 1 9.5-2.6', 'M8.5 15.5a5 5 0 0 1 5.5-1', 'M12 19.5h.01', 'M3 3l18 18'],
  menu: ['M4 6h16', 'M4 12h16', 'M4 18h16'],
  retour: ['M15 18l-6-6 6-6'],
  recherche: ['M11 4a7 7 0 1 0 0 14a7 7 0 1 0 0-14', 'M20 20l-4.3-4.3'],
  fermer: ['M6 6l12 12', 'M18 6L6 18'],
  chevron: ['M6 9l6 6 6-6'],
  information: ['M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18', 'M12 11v5', 'M12 8h.01'],
  exclamation: ['M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18', 'M12 8v5', 'M12 16.5h.01'],
  triangle: ['M10.3 3.9L2.4 17.6A2 2 0 0 0 4.1 20.6h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z', 'M12 9v4', 'M12 17h.01'],
  fleche_haut: ['M12 19V5', 'M6 11l6-6 6 6'],
  fleche_bas: ['M12 5v14', 'M6 13l6 6 6-6'],
  egal: ['M5 10h14', 'M5 14h14'],
  soleil: ['M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0-8', 'M12 2v2', 'M12 20v2', 'M4.9 4.9l1.4 1.4', 'M17.7 17.7l1.4 1.4', 'M2 12h2', 'M20 12h2', 'M4.9 19.1l1.4-1.4', 'M17.7 6.3l1.4-1.4'],
  lune: ['M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z'],
  appareil: ['M4 5h16v11H4z', 'M9 20h6', 'M12 16v4'],
  apropos: ['M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18', 'M12 11v5', 'M12 8h.01'],
  inscription: ['M15 20v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2', 'M8.5 4a3.5 3.5 0 1 0 0 7a3.5 3.5 0 1 0 0-7', 'M19 8v6', 'M22 11h-6'],
  appel: ['M7 4h10a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z', 'M9 3h6v3H9z', 'M9 13l2 2 4-4'],
  horloge: ['M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18', 'M12 7v5l3 2'],
  sanction: ['M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6z', 'M12 8v5', 'M12 16h.01'],
  progression: ['M4 19h16', 'M7 15l4-4 3 3 5-6'],
  evaluation: ['M4 20h4L19 9l-4-4L4 16z', 'M13.5 6.5l4 4'],
  conseil: ['M9 11a3 3 0 1 0 0-6a3 3 0 1 0 0 6', 'M3 20v-1a5 5 0 0 1 10 0v1', 'M16 11a2.5 2.5 0 1 0 0-5', 'M21 20v-1a4 4 0 0 0-3-3.9'],
  finance: ['M21 12V7H5a2 2 0 0 1 0-4h14v4', 'M3 5v14a2 2 0 0 0 2 2h16v-5', 'M18 12a2 2 0 0 0 0 4h4v-4z'],
  personnel: ['M3 4h18v16H3z', 'M9 9a2.2 2.2 0 1 0 0 4.4a2.2 2.2 0 1 0 0-4.4', 'M5.5 17a3.5 3.5 0 0 1 7 0', 'M15 9h3', 'M15 13h3'],
  message: ['M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z'],
  reglage: ['M4 7h9', 'M19 7h1', 'M4 17h1', 'M11 17h9', 'M16 4.8a2.2 2.2 0 1 0 0 4.4a2.2 2.2 0 1 0 0-4.4', 'M8 14.8a2.2 2.2 0 1 0 0 4.4a2.2 2.2 0 1 0 0-4.4'],
} as const

export type NomIcone = keyof typeof TRACES
export const ICONES = Object.keys(TRACES) as NomIcone[]
</script>

<script setup lang="ts">
const props = withDefaults(defineProps<{ nom: NomIcone; taille?: number }>(), { taille: 16 })
const traces = computed(() => TRACES[props.nom])
</script>

<template>
  <svg
    class="icone"
    :width="taille"
    :height="taille"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <path v-for="(d, i) in traces" :key="i" :d="d" />
  </svg>
</template>

<style scoped>
.icone {
  flex: 0 0 auto;
}
</style>
