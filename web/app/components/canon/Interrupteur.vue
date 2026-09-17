<script lang="ts">
import { COMPOSANTS } from '~/core/composants/etats'
export const ETATS_COMPOSANT = COMPOSANTS.Interrupteur
</script>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    /** Clé du libellé. */
    libelle: string
    modelValue: boolean
    /** Inactif : la raison est dite (clé). */
    inactif?: { raison: string } | null
  }>(),
  { inactif: null },
)
const emit = defineEmits<{ 'update:modelValue': [valeur: boolean] }>()
const { t } = useLibelles()
const idRaison = useId()
const etat = computed(() => (props.inactif ? 'inactif' : props.modelValue ? 'active' : 'desactive'))
</script>

<template>
  <div class="interrupteur" :data-etat="etat">
    <button
      type="button"
      role="switch"
      class="commande"
      :aria-checked="modelValue"
      :disabled="inactif !== null"
      :aria-describedby="inactif ? idRaison : undefined"
      @click="emit('update:modelValue', !modelValue)"
    >
      <span class="libelle">{{ t(libelle) }}</span>
      <span class="droite">
        <span class="mot">{{ t(modelValue ? 'interrupteur.active' : 'interrupteur.desactive') }}</span>
        <span class="piste" :class="{ allume: modelValue }" data-forme="position">
          <span class="bouton" />
        </span>
      </span>
    </button>
    <span v-if="inactif" :id="idRaison" class="raison">{{ t(inactif.raison) }}</span>
  </div>
</template>

<style scoped>
.interrupteur {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.commande {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
  min-height: var(--cible, var(--cible-standard));
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--text);
  font-family: inherit;
  font-size: 14px;
  text-align: left;
  cursor: pointer;
}
.commande:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
  border-radius: var(--rayon-micro);
}
.droite {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex: 0 0 auto;
}
.mot {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
}
.piste {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  width: 36px;
  height: 20px;
  padding: 0 2px;
  border: var(--filet) solid var(--border-strong);
  border-radius: var(--rayon-pastille);
  background: var(--surface-sunken);
}
.piste .bouton {
  width: 14px;
  height: 14px;
  border-radius: var(--rayon-pastille);
  background: var(--border-strong);
}
.piste.allume {
  justify-content: flex-end;
  border-color: var(--primary);
  background: var(--primary);
}
.piste.allume .bouton {
  background: var(--surface);
}
.allume + .mot,
.commande[aria-checked='true'] .mot {
  color: var(--primary);
}
.commande:disabled {
  cursor: not-allowed;
  color: var(--text-muted);
}
.commande:disabled .piste {
  opacity: 0.6;
}
.raison {
  font-size: 12px;
  color: var(--text-muted);
}
</style>
