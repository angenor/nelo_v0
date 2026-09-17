<script lang="ts">
import { COMPOSANTS } from '~/core/composants/etats'
export const ETATS_COMPOSANT = COMPOSANTS.Onglets
</script>

<script setup lang="ts">
// Les vues d'une même fiche, pas une navigation (rôle tablist, flèches du clavier).
const props = defineProps<{
  onglets: { cle: string; libelle: string; compte?: number }[]
  modelValue: string
}>()
const emit = defineEmits<{ 'update:modelValue': [cle: string] }>()
const { t } = useLibelles()
const boutons = ref<HTMLButtonElement[]>([])

function deplacer(depuis: number, pas: number) {
  const n = props.onglets.length
  const cible = (depuis + pas + n) % n
  emit('update:modelValue', props.onglets[cible]!.cle)
  boutons.value[cible]?.focus()
}
</script>

<template>
  <div class="onglets" role="tablist" data-etat="actif inactif avec_compte">
    <button
      v-for="(onglet, i) in onglets"
      :key="onglet.cle"
      ref="boutons"
      type="button"
      role="tab"
      class="onglet"
      :aria-selected="onglet.cle === modelValue"
      :tabindex="onglet.cle === modelValue ? 0 : -1"
      @click="emit('update:modelValue', onglet.cle)"
      @keydown.right.prevent="deplacer(i, 1)"
      @keydown.left.prevent="deplacer(i, -1)"
    >
      <span>{{ t(onglet.libelle) }}</span>
      <span v-if="onglet.compte !== undefined" class="compte">{{ onglet.compte }}</span>
    </button>
  </div>
</template>

<style scoped>
.onglets {
  display: flex;
  gap: 24px;
  overflow-x: auto;
  border-bottom: var(--filet) solid var(--border);
}
.onglet {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: var(--cible, var(--cible-standard));
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--text-muted);
  font-family: inherit;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  cursor: pointer;
}
.onglet[aria-selected='true'] {
  color: var(--text);
  font-weight: 500;
  box-shadow: inset 0 -2px 0 var(--primary);
}
.onglet:hover {
  color: var(--text);
}
.onglet:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: -2px;
  border-radius: var(--rayon-micro);
}
.compte {
  min-width: 18px;
  padding: 0 5px;
  border-radius: var(--rayon-pastille);
  background: var(--surface-sunken);
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: 12px;
  text-align: center;
}
</style>
