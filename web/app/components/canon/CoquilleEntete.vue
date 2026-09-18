<script setup lang="ts">
import type { CodeEtat } from '~/core/composants/etats'
import type { AnneeContexte, ContexteCapacites } from '~/core/contexte/types'
import { estLangue } from '~/core/i18n/libelles'
import type { Theme } from '~/core/theme'
import { THEMES } from '~/core/theme'

// L'en-tête : l'établissement et son site, l'année de travail, la langue et son changement,
// le thème, « à propos », l'avatar (FR-027).
//
// L'avatar ouvre le **menu de compte** (écart E-05) : le nom du compte, l'établissement actif
// avec la liste des rattachés, l'année de travail avec la sienne, « Mon numéro » et « Fermer la
// session ». À 390 px, c'est le seul endroit où le geste tient sans rogner le nom de
// l'établissement ; dès `md`, « Fermer la session » est aussi directement dans l'en-tête, parce
// que FR-015 le veut visible et qu'un poste partagé se ferme d'un geste.
//
// Le choix d'établissement et d'année vit sur l'appareil : l'en-tête ne fait que l'émettre.
const props = defineProps<{
  contexte: ContexteCapacites
  accueil: string
  montrerMenu: boolean
  montrerRetour: boolean
  menuOuvert: boolean
  /** L'année choisie sur cet appareil, quand elle diffère de l'année active du contexte. */
  anneeChoisie?: string | null
}>()
const emit = defineEmits<{
  menu: []
  retour: []
  changerEtablissement: [identifiant: string]
  changerAnnee: [identifiant: string]
  deconnexion: []
}>()
const { t, langue, changer } = useLibelles()
const { theme, forcer } = useTheme()

const TELEPHONE = '/compte/telephone'

const etablissement = computed(
  () => props.contexte.etablissements.find((e) => e.id === props.contexte.etablissement_actif)!,
)
const site = computed(() => etablissement.value.sites[0]?.nom)
function sigleDe(nom: string): string {
  const mots = nom.split(/\s+/).filter(Boolean)
  return ((mots[0]?.[0] ?? '') + (mots.length > 1 ? (mots.at(-1)?.[0] ?? '') : '')).toUpperCase()
}
const sigle = computed(() => sigleDe(etablissement.value.nom))
const anneeActive = computed(() => props.anneeChoisie ?? props.contexte.annee_active)
const annee = computed(() => props.contexte.annees.find((a) => a.id === anneeActive.value))
const compte = computed(() => props.contexte.compte)
const nomCompte = computed(() => `${compte.value.prenoms} ${compte.value.nom}`.trim())
/** Le nom du compte, dit comme le lecteur d'écran l'annonce : c'est aussi le nom de l'avatar. */
const nomLu = computed(() => t('coquille.compte', { nom: nomCompte.value }))
const initiales = computed(() => `${compte.value.prenoms[0] ?? ''}${compte.value.nom[0] ?? ''}`.toUpperCase())
const langues = computed(() => props.contexte.country_pack.langues.filter(estLangue))

/** L'état d'une année, dit par son code de pastille : deux codes, deux mots (écart E-03). */
function codeAnnee(item: AnneeContexte): CodeEtat {
  return item.etat === 'PREPARATION' ? 'ANNEE_PREPARATION' : 'ANNEE_ACTIVE'
}
/** La pastille de l'en-tête ne paraît que pour l'attente : une année active ne se signale pas. */
const anneeEnPreparation = computed(() => annee.value?.etat === 'PREPARATION')

const compteOuvert = ref(false)
function basculerCompte() {
  compteOuvert.value = !compteOuvert.value
}
function fermerCompte() {
  compteOuvert.value = false
}
function choisirEtablissement(identifiant: string) {
  fermerCompte()
  if (identifiant !== props.contexte.etablissement_actif) emit('changerEtablissement', identifiant)
}
function choisirAnnee(identifiant: string) {
  fermerCompte()
  if (identifiant !== anneeActive.value) emit('changerAnnee', identifiant)
}
function fermerSession() {
  fermerCompte()
  emit('deconnexion')
}

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
    <span v-if="annee" class="annee" :title="t('coquille.annee')">
      <span class="annee-libelle">{{ annee.libelle }}</span>
      <CanonPastilleEtat v-if="anneeEnPreparation" code="ANNEE_PREPARATION" forme="rond" />
    </span>
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
      <button type="button" class="fermeture" data-fermer-session @click="fermerSession">
        <InterneIcone nom="retour" :taille="18" />
        <span>{{ t('session.fermer') }}</span>
      </button>
      <button
        type="button"
        class="avatar"
        data-menu-compte
        :aria-label="nomLu"
        :aria-expanded="compteOuvert"
        @click="basculerCompte"
      >
        <CanonAvatar :initiales="initiales" :nom="nomLu" taille="petite" />
      </button>
    </div>

    <!-- Le menu de compte (écart E-05). Le voile ferme au premier geste hors du panneau. -->
    <div v-if="compteOuvert" class="menu-compte">
      <div class="voile" aria-hidden="true" @click="fermerCompte" />
      <div class="panneau" data-panneau-compte>
        <p class="panneau-compte">
          <span class="panneau-nom">{{ nomCompte }}</span>
        </p>

        <section class="bloc" :aria-label="t('coquille.etablissement')">
          <h2 class="bloc-titre">{{ t('coquille.etablissement') }}</h2>
          <ul class="liste">
            <li v-for="item in contexte.etablissements" :key="item.id">
              <button
                type="button"
                class="ligne"
                :aria-current="item.id === contexte.etablissement_actif ? 'true' : undefined"
                @click="choisirEtablissement(item.id)"
              >
                <span class="sigle" aria-hidden="true">{{ sigleDe(item.nom) }}</span>
                <span class="ligne-texte">{{ item.nom }}</span>
                <InterneIcone
                  v-if="item.id === contexte.etablissement_actif"
                  nom="coche"
                  :taille="18"
                  class="ligne-coche"
                />
              </button>
            </li>
          </ul>
          <p class="note">{{ t('coquille.etablissement.rattaches') }}</p>
        </section>

        <section class="bloc" :aria-label="t('coquille.annee')">
          <h2 class="bloc-titre">{{ t('coquille.annee') }}</h2>
          <ul class="liste">
            <li v-for="item in contexte.annees" :key="item.id">
              <button
                type="button"
                class="ligne"
                :aria-current="item.id === anneeActive ? 'true' : undefined"
                @click="choisirAnnee(item.id)"
              >
                <span class="ligne-texte annee-texte">{{ item.libelle }}</span>
                <CanonPastilleEtat :code="codeAnnee(item)" forme="rond" />
                <InterneIcone
                  v-if="item.id === anneeActive"
                  nom="coche"
                  :taille="18"
                  class="ligne-coche"
                />
              </button>
            </li>
          </ul>
          <p class="note">{{ t('coquille.annee.appareil') }}</p>
        </section>

        <div class="gestes">
          <NuxtLink :to="TELEPHONE" class="geste" @click="fermerCompte">
            {{ t('coquille.mon_numero') }}
          </NuxtLink>
          <button type="button" class="geste" data-fermer-session-menu @click="fermerSession">
            {{ t('session.fermer') }}
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
@reference "../../assets/css/jetons.css";

.entete {
  position: relative;
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
.etablissement:focus-visible,
.avatar:focus-visible,
.fermeture:focus-visible,
.ligne:focus-visible,
.geste:focus-visible {
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
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 8px;
  white-space: nowrap;
  @variant max-md {
    display: none;
  }
}
.annee-libelle {
  font-variant-numeric: tabular-nums;
  font-weight: 500;
  font-size: 12px;
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
/* Le geste direct : il ne paraît que là où il y a la place de l'écrire (écart E-05). */
.fermeture {
  display: none;
  align-items: center;
  gap: 6px;
  min-height: var(--cible, var(--cible-standard));
  padding: 0 12px;
  border: var(--filet) solid var(--border-strong);
  border-radius: var(--rayon-champ);
  background: var(--surface);
  color: var(--text);
  font-family: inherit;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  @variant md {
    display: inline-flex;
  }
}
.fermeture:hover {
  border-color: var(--primary);
  color: var(--primary);
}
.avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: var(--cible, var(--cible-standard));
  min-height: var(--cible, var(--cible-standard));
  padding: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
  flex: 0 0 auto;
}
.menu-compte {
  position: absolute;
  inset: 100% 0 auto 0;
  z-index: 20;
}
.voile {
  position: fixed;
  inset: 0;
  background: var(--text);
  opacity: 0.4;
}
.panneau {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 14px;
  width: min(320px, calc(100% - 16px));
  margin: 0 8px 0 auto;
  padding: 14px;
  border: var(--filet) solid var(--border);
  border-radius: var(--rayon-carte);
  background: var(--surface);
  box-shadow: 0 8px 24px var(--border-strong);
}
.panneau-compte {
  margin: 0;
}
.panneau-nom,
.bloc-titre {
  font-family: var(--font-titres);
  font-weight: 700;
  font-size: 15px;
}
.bloc,
.liste,
.gestes {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.bloc-titre {
  font-family: inherit;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-muted);
}
.ligne,
.geste {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-height: var(--cible, var(--cible-standard));
  padding: 0 8px;
  border: var(--filet) solid transparent;
  border-radius: var(--rayon-champ);
  background: transparent;
  color: var(--text);
  font-family: inherit;
  font-size: 14px;
  text-align: start;
  cursor: pointer;
}
.ligne:hover,
.geste:hover {
  border-color: var(--border-strong);
  color: var(--text);
  text-decoration: none;
}
.ligne[aria-current='true'] {
  background: var(--primary-soft);
}
.ligne-texte {
  overflow: hidden;
  min-width: 0;
  flex: 1;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.annee-texte {
  font-variant-numeric: tabular-nums;
  font-weight: 500;
}
.ligne-coche {
  flex: 0 0 auto;
  color: var(--primary);
}
.note {
  margin: 0;
  font-size: 12px;
  color: var(--text-muted);
}
.gestes {
  padding-top: 10px;
  border-top: var(--filet) solid var(--border);
}
</style>
