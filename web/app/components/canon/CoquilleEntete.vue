<script setup lang="ts">
import type { ContexteCapacites } from '~/core/contexte/types'
import { estLangue } from '~/core/i18n/libelles'
import type { Theme } from '~/core/theme'
import { THEMES } from '~/core/theme'

// L'en-tête : l'établissement et son site, l'année de travail, la langue et son changement,
// le thème, « à propos », l'avatar (FR-027). Ni cloche ni déconnexion : T1a.
const props = defineProps<{
  contexte: ContexteCapacites
  accueil: string
  montrerMenu: boolean
  montrerRetour: boolean
  menuOuvert: boolean
}>()
const emit = defineEmits<{ menu: []; retour: [] }>()
const { t, langue, changer } = useLibelles()
const { theme, forcer } = useTheme()

const etablissement = computed(
  () => props.contexte.etablissements.find((e) => e.id === props.contexte.etablissement_actif)!,
)
const site = computed(() => etablissement.value.sites[0]?.nom)
const sigle = computed(() => {
  const mots = etablissement.value.nom.split(/\s+/).filter(Boolean)
  return ((mots[0]?.[0] ?? '') + (mots.length > 1 ? (mots.at(-1)?.[0] ?? '') : '')).toUpperCase()
})
const annee = computed(() => props.contexte.annees.find((a) => a.id === props.contexte.annee_active))
const compte = computed(() => props.contexte.compte)
const initiales = computed(() => `${compte.value.prenoms[0] ?? ''}${compte.value.nom[0] ?? ''}`.toUpperCase())
const langues = computed(() => props.contexte.country_pack.langues.filter(estLangue))

const ICONES_THEME: Record<Theme, 'appareil' | 'soleil' | 'lune'> = { systeme: 'appareil', light: 'soleil', dark: 'lune' }
function themeSuivant() {
  forcer(THEMES[(THEMES.indexOf(theme.value) + 1) % THEMES.length]!)
}
</script>

<template>
  <header class="entete">
    <button v-if="montrerRetour" type="button" class="icone-seule" :aria-label="t('coquille.retour')" @click="emit('retour')">
      <InterneIcone nom="retour" />
    </button>
    <button
      v-if="montrerMenu"
      type="button"
      class="icone-seule menu"
      :aria-label="t(menuOuvert ? 'coquille.fermer_menu' : 'coquille.ouvrir_menu')"
      :aria-expanded="menuOuvert"
      @click="emit('menu')"
    >
      <InterneIcone :nom="menuOuvert ? 'fermer' : 'menu'" />
    </button>
    <NuxtLink :to="accueil" class="etablissement" :aria-label="`${t('coquille.accueil')} : ${etablissement.nom}`">
      <span class="sigle" aria-hidden="true">{{ sigle }}</span>
      <span class="nom">{{ etablissement.nom }}<template v-if="site"> · {{ site }}</template></span>
    </NuxtLink>
    <span v-if="annee" class="annee" :title="t('coquille.annee')">{{ annee.libelle }}</span>
    <div class="outils">
      <div class="langues" role="group" :aria-label="t('coquille.langue')">
        <button
          v-for="code in langues"
          :key="code"
          type="button"
          class="langue"
          :lang="code"
          :aria-pressed="code === langue"
          @click="changer(code)"
        >
          {{ code.toUpperCase() }}
        </button>
      </div>
      <button
        type="button"
        class="icone-seule"
        :aria-label="t('coquille.theme', { theme: t(`coquille.theme.${theme}`) })"
        :data-theme-choisi="theme"
        @click="themeSuivant"
      >
        <InterneIcone :nom="ICONES_THEME[theme]" />
      </button>
      <NuxtLink to="/a-propos" class="icone-seule" :aria-label="t('coquille.a_propos')">
        <InterneIcone nom="apropos" />
      </NuxtLink>
      <CanonAvatar :initiales="initiales" :nom="t('coquille.compte', { nom: `${compte.prenoms} ${compte.nom}` })" taille="petite" />
    </div>
  </header>
</template>

<style scoped>
@reference "../../assets/css/jetons.css";

.entete {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  min-height: calc(var(--cible, var(--cible-standard)) + 8px);
  padding: 4px 12px;
  border-bottom: var(--filet) solid var(--border);
  background: var(--surface);
  flex: 0 0 auto;
}
.icone-seule {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: var(--cible, var(--cible-standard));
  min-height: var(--cible, var(--cible-standard));
  padding: 0;
  border: var(--filet) solid var(--border);
  border-radius: var(--rayon-champ);
  background: var(--surface);
  color: var(--text-muted);
  cursor: pointer;
  flex: 0 0 auto;
}
.icone-seule:hover {
  border-color: var(--primary);
  color: var(--primary);
  text-decoration: none;
}
.icone-seule:focus-visible,
.langue:focus-visible,
.etablissement:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}
.menu {
  @variant md {
    display: none;
  }
}
.etablissement {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  min-height: var(--cible, var(--cible-standard));
  padding: 0 8px;
  border: var(--filet) solid var(--border);
  border-radius: var(--rayon-champ);
  color: var(--text);
  flex: 0 1 auto;
}
.etablissement:hover {
  border-color: var(--border-strong);
  color: var(--text);
  text-decoration: none;
}
.sigle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  flex: 0 0 auto;
  border-radius: var(--rayon-champ);
  background: var(--primary);
  color: var(--primary-ink);
  font-family: var(--font-titres);
  font-weight: 700;
  font-size: 11px;
}
.nom {
  overflow: hidden;
  font-size: 13px;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.annee {
  padding: 0 8px;
  font-variant-numeric: tabular-nums;
  font-weight: 500;
  font-size: 12px;
  white-space: nowrap;
  @variant max-md {
    display: none;
  }
}
.outils {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  min-width: 0;
  margin-left: auto;
  flex: 0 1 auto;
}
.langues {
  display: flex;
  overflow: hidden;
  border: var(--filet) solid var(--border-strong);
  border-radius: var(--rayon-champ);
}
.langue {
  min-width: var(--cible-plancher);
  min-height: var(--cible, var(--cible-standard));
  padding: 0 8px;
  border: 0;
  background: transparent;
  color: var(--text-muted);
  font-family: inherit;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
}
.langue[aria-pressed='true'] {
  background: var(--primary);
  color: var(--primary-ink);
  font-weight: 500;
}
</style>
