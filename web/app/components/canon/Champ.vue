<script lang="ts">
import { COMPOSANTS } from '~/core/composants/etats'
export const ETATS_COMPOSANT = COMPOSANTS.Champ
</script>

<script setup lang="ts">
import type { EtatChamp, TypeChamp } from '~/core/composants/etats'
import type { Parametres } from '~/core/i18n/libelles'

const props = withDefaults(
  defineProps<{
    /** Clé de l'étiquette, toujours visible au-dessus du champ. */
    libelle: string
    type?: TypeChamp
    modelValue?: string | boolean
    /** Clé de l'aide, sous le champ. */
    aide?: string
    /** Unité déjà mise en forme par le pack (« F », « / 20 »). */
    unite?: string
    /** Clé du message d'erreur : la règle et ce qu'il faut faire. */
    erreur?: string
    parametresErreur?: Parametres
    inactif?: boolean
    /** Chiffres en IBM Plex Mono tabulaire (matricule, montant, note). */
    mono?: boolean
    /** Pour un choix : les options, libellés déjà résolus (données). */
    options?: { valeur: string; libelle: string }[]
    /** Page de style seulement. */
    etatMontre?: EtatChamp
  }>(),
  {
    type: 'texte',
    modelValue: '',
    aide: undefined,
    unite: undefined,
    erreur: undefined,
    parametresErreur: undefined,
    inactif: false,
    mono: false,
    options: () => [],
    etatMontre: undefined,
  },
)
const emit = defineEmits<{ 'update:modelValue': [valeur: string | boolean] }>()
const { t } = useLibelles()
const id = useId()
const idAide = `${id}-aide`
const idErreur = `${id}-erreur`

const etat = computed<EtatChamp>(() => {
  if (props.inactif) return 'inactif'
  if (props.erreur) return 'erreur'
  return props.etatMontre ?? 'repos'
})
const decrit = computed(
  () => [props.erreur ? idErreur : '', props.aide ? idAide : ''].filter(Boolean).join(' ') || undefined,
)
const complements = computed(() => [props.aide ? 'aide' : '', props.unite ? 'unite' : ''].filter(Boolean))

function saisir(evenement: Event) {
  const cible = evenement.target as HTMLInputElement | HTMLSelectElement
  emit('update:modelValue', cible instanceof HTMLInputElement && cible.type === 'checkbox' ? cible.checked : cible.value)
}
</script>

<template>
  <div class="champ" :data-etat="[type, etat, ...complements].join(' ')" :data-voix="etat === 'erreur' ? 'danger' : undefined">
    <label v-if="type === 'case'" :for="id" class="case">
      <input
        :id="id"
        type="checkbox"
        class="case-native"
        :checked="modelValue === true"
        :disabled="inactif"
        :aria-describedby="decrit"
        :aria-invalid="etat === 'erreur' || undefined"
        @change="saisir"
      >
      <span class="case-dessin" aria-hidden="true"><InterneIcone nom="coche" :taille="12" /></span>
      <span class="case-libelle">{{ t(libelle) }}</span>
    </label>
    <template v-else>
      <label :for="id" class="etiquette">{{ t(libelle) }}</label>
      <div class="boite" :class="{ focus: etatMontre === 'focus' }">
        <select
          v-if="type === 'choix'"
          :id="id"
          class="saisie"
          :value="modelValue"
          :disabled="inactif"
          :aria-describedby="decrit"
          :aria-invalid="etat === 'erreur' || undefined"
          @change="saisir"
        >
          <option v-for="option in options" :key="option.valeur" :value="option.valeur">{{ option.libelle }}</option>
        </select>
        <input
          v-else
          :id="id"
          class="saisie"
          :class="{ mono: mono || type === 'nombre' }"
          type="text"
          :inputmode="type === 'nombre' ? 'decimal' : undefined"
          :value="modelValue"
          :disabled="inactif"
          :aria-describedby="decrit"
          :aria-invalid="etat === 'erreur' || undefined"
          @input="saisir"
        >
        <InterneIcone v-if="type === 'choix'" nom="chevron" class="chevron" />
        <span v-if="unite" class="unite" aria-hidden="true">{{ unite }}</span>
      </div>
    </template>
    <p v-if="erreur" :id="idErreur" class="erreur" data-forme="icone">
      <InterneIcone nom="exclamation" :taille="14" />
      <span>{{ t(erreur, parametresErreur) }}</span>
    </p>
    <p v-if="aide" :id="idAide" class="aide">{{ t(aide) }}</p>
  </div>
</template>

<style scoped>
.champ {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}
.etiquette {
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
}
/* Le filet est une ombre intérieure : il ne rogne pas la cible, que le champ occupe en entier. */
.boite {
  position: relative;
  display: flex;
  align-items: center;
  min-height: var(--cible, var(--cible-standard));
  border-radius: var(--rayon-champ);
  background: var(--surface);
  box-shadow: inset 0 0 0 var(--filet) var(--border-strong);
}
.boite:focus-within,
.boite.focus {
  box-shadow:
    inset 0 0 0 var(--filet) var(--primary),
    0 0 0 3px var(--primary-soft);
}
.saisie {
  flex: 1;
  min-width: 0;
  min-height: var(--cible, var(--cible-standard));
  align-self: stretch;
  padding: 0 10px;
  border: 0;
  border-radius: var(--rayon-champ);
  background: transparent;
  color: var(--text);
  font-family: inherit;
  font-size: 16px;
  outline: none;
  appearance: none;
}
select.saisie {
  padding-right: 32px;
  cursor: pointer;
}
.saisie.mono {
  font-family: var(--font-mono);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}
.chevron {
  position: absolute;
  right: 10px;
  color: var(--text-muted);
  pointer-events: none;
}
.unite {
  padding: 0 10px 0 4px;
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: 14px;
  color: var(--text-muted);
}
[data-voix='danger'] .boite {
  box-shadow: inset 0 0 0 var(--filet) var(--danger);
}
[data-voix='danger'] .boite:focus-within {
  box-shadow:
    inset 0 0 0 var(--filet) var(--danger),
    0 0 0 3px var(--danger-soft);
}
.champ[data-etat~='inactif'] .boite {
  background: var(--surface-sunken);
  box-shadow: inset 0 0 0 var(--filet) var(--border);
}
.champ[data-etat~='inactif'] .saisie {
  color: var(--text-muted);
  cursor: not-allowed;
}
.erreur {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin: 0;
  font-size: 12px;
  color: var(--danger);
}
.erreur :deep(.icone) {
  margin-top: 1px;
}
.aide {
  margin: 0;
  font-size: 12px;
  color: var(--text-muted);
}
.case {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: var(--cible, var(--cible-standard));
  cursor: pointer;
}
.case-native {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  margin: 0;
  opacity: 0;
  cursor: pointer;
}
.case-dessin {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  flex: 0 0 auto;
  border: var(--filet) solid var(--border-strong);
  border-radius: var(--rayon-micro);
  background: var(--surface);
  color: transparent;
}
.case-native:checked + .case-dessin {
  border-color: var(--primary);
  background: var(--primary);
  color: var(--primary-ink);
}
.case-native:focus-visible + .case-dessin {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}
.case-libelle {
  font-size: 14px;
}
</style>
