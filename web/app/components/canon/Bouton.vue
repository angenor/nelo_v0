<script lang="ts">
import { COMPOSANTS } from '~/core/composants/etats'
export const ETATS_COMPOSANT = COMPOSANTS.Bouton
</script>

<script setup lang="ts">
import type { EtatBouton, VarianteBouton } from '~/core/composants/etats'
import type { Parametres } from '~/core/i18n/libelles'

const props = withDefaults(
  defineProps<{
    /** Clé du libellé. */
    libelle: string
    parametres?: Parametres
    variante?: VarianteBouton
    type?: 'button' | 'submit'
    /** Inactif : la raison est dite sous le bouton, avec son versant positif (clé). */
    inactif?: { raison: string } | null
    pleineLargeur?: boolean
    /** Page de style seulement : montre un état qui dépend de l'interaction. */
    etatMontre?: EtatBouton
  }>(),
  { variante: 'secondaire', type: 'button', inactif: null, pleineLargeur: false, etatMontre: undefined, parametres: undefined },
)
const emit = defineEmits<{ appui: [] }>()
const { t } = useLibelles()
const idRaison = useId()
const etat = computed<EtatBouton>(() => (props.inactif ? 'inactif' : (props.etatMontre ?? 'repos')))
</script>

<template>
  <span class="conteneur" :class="{ large: pleineLargeur }">
    <button
      :type="type"
      class="bouton"
      :class="`bouton--${variante}`"
      :data-variante="variante"
      :data-etat="`${variante} ${etat}`"
      :disabled="inactif !== null"
      :aria-describedby="inactif ? idRaison : undefined"
      @click="emit('appui')"
    >
      <slot name="icone" />
      <span>{{ t(libelle, parametres) }}</span>
    </button>
    <span v-if="inactif" :id="idRaison" class="raison">{{ t(inactif.raison) }}</span>
  </span>
</template>

<style scoped>
.conteneur {
  display: inline-flex;
  flex-direction: column;
  gap: 4px;
  max-width: 100%;
}
.conteneur.large {
  display: flex;
  width: 100%;
}
.bouton {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: var(--cible, var(--cible-standard));
  min-width: var(--cible-plancher);
  padding: 0 16px;
  border: var(--filet) solid transparent;
  border-radius: var(--rayon-champ);
  font-family: inherit;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.2;
  text-align: center;
  cursor: pointer;
}
.bouton::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  height: var(--cible-plancher);
  transform: translateY(-50%);
}
.large .bouton {
  width: 100%;
}
.bouton--principal {
  background: var(--primary);
  border-color: var(--primary);
  color: var(--primary-ink);
}
.bouton--principal:hover,
.bouton--principal[data-etat~='presse'] {
  background: var(--primary-hover);
  border-color: var(--primary-hover);
}
.bouton--secondaire {
  background: var(--surface);
  border-color: var(--border-strong);
  color: var(--text);
}
.bouton--secondaire:hover,
.bouton--secondaire[data-etat~='presse'] {
  border-color: var(--primary);
  color: var(--primary);
}
.bouton--discret {
  background: transparent;
  color: var(--text-muted);
}
.bouton--discret:hover,
.bouton--discret[data-etat~='presse'] {
  background: var(--surface-sunken);
  color: var(--text);
}
.bouton--danger {
  background: var(--danger);
  border-color: var(--danger);
  color: var(--danger-ink);
}
.bouton--danger:hover,
.bouton--danger[data-etat~='presse'] {
  filter: brightness(0.92);
}
.bouton:focus-visible,
.bouton[data-etat~='focus'] {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
  box-shadow: 0 0 0 3px var(--primary-soft);
}
.bouton:disabled {
  background: var(--surface-sunken);
  border-color: var(--border);
  color: var(--text-muted);
  filter: none;
  cursor: not-allowed;
}
.raison {
  font-size: 12px;
  color: var(--text-muted);
  max-width: 40ch;
}
</style>
