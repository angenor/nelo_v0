<script setup lang="ts">
// Une section de la page de style : le même contenu rendu deux fois, sur un conteneur en thème
// clair et un conteneur en thème sombre, côte à côte.
defineProps<{ composant: string; numero: number }>()
const { t } = useLibelles()
const THEMES = [
  { theme: 'light', cle: 'style.theme_clair' },
  { theme: 'dark', cle: 'style.theme_sombre' },
] as const
</script>

<template>
  <section class="section" :data-composant="composant" :aria-labelledby="`titre-${composant}`">
    <h2 :id="`titre-${composant}`" class="titre">
      <span class="numero">{{ String(numero).padStart(2, '0') }}</span>
      {{ t(`style.composant.${composant}`) }}
    </h2>
    <div class="paire">
      <div v-for="{ theme, cle } in THEMES" :key="theme" :data-theme="theme" class="theme">
        <p class="nom-theme">{{ t(cle) }}</p>
        <slot :theme="theme" />
      </div>
    </div>
  </section>
</template>

<style scoped>
.section {
  padding: 32px 0;
  border-top: var(--filet) solid var(--border);
}
.titre {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin: 0 0 16px;
  font-family: var(--font-titres);
  font-weight: 600;
  font-size: 26px;
  letter-spacing: -0.02em;
}
.numero {
  font-size: 14px;
  color: var(--text-muted);
}
.paire {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 520px), 1fr));
  gap: 16px;
}
.theme {
  min-width: 0;
  padding: 24px;
  border: var(--filet) solid var(--border);
  border-radius: var(--rayon-carte);
  background: var(--bg);
  color: var(--text);
}
.nom-theme {
  margin: 0 0 16px;
  font-size: 13px;
  font-weight: 600;
}
</style>
