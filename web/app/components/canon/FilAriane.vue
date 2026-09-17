<script lang="ts">
import { COMPOSANTS } from '~/core/composants/etats'
export const ETATS_COMPOSANT = COMPOSANTS.FilAriane
</script>

<script setup lang="ts">
// La position dans une hiérarchie profonde. Les libellés sont déjà résolus (données ou clés
// traduites par l'appelant) ; le dernier segment est la position courante, non cliquable.
defineProps<{ segments: { libelle: string; route?: string }[] }>()
const { t } = useLibelles()
</script>

<template>
  <nav class="fil" :aria-label="t('fil.etiquette')" data-etat="lien courant">
    <ol>
      <li v-for="(segment, i) in segments" :key="i">
        <span v-if="i > 0" class="separateur" aria-hidden="true">/</span>
        <NuxtLink v-if="segment.route && i < segments.length - 1" :to="segment.route" class="lien">
          {{ segment.libelle }}
        </NuxtLink>
        <span v-else class="courant" aria-current="page">{{ segment.libelle }}</span>
      </li>
    </ol>
  </nav>
</template>

<style scoped>
ol {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0 6px;
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: 13px;
  color: var(--text-muted);
}
li {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.lien {
  display: inline-flex;
  align-items: center;
  min-height: var(--cible-plancher);
}
.courant {
  color: var(--text);
  font-weight: 500;
}
</style>
