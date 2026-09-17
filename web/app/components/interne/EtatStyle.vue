<script setup lang="ts">
// Un état montré sur la page de style, avec son nom technique en légende (une valeur
// d'énumération, pas un mot d'interface).
defineProps<{ etats: string }>()
</script>

<template>
  <div class="etat" :data-etat="etats">
    <span class="legende">{{ etats }}</span>
    <slot />
  </div>
</template>

<style scoped>
.etat {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  min-width: 0;
}
.legende {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}
</style>
