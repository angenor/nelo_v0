<script setup lang="ts">
import { libelleDomaine } from '~/core/composition/libelle'
import type { Composition, Domaine, Entree } from '~/core/composition/types'

// La navigation composée : les entrées du domaine en mono-domaine, les domaines à plat jusqu'à
// cinq, par famille dès six. Rien d'autre n'existe, rien n'est grisé.
const props = defineProps<{
  composition: Composition
  routeActive: string
  disposition: 'laterale' | 'basse' | 'tiroir'
}>()
const { t } = useLibelles()
const pack = usePack()

interface Lien {
  code: string
  libelle: string
  route: string
  icone: Entree['icone']
  compte: number | null
  domaine: string
}

function depuisDomaine(d: Domaine): Lien {
  return { code: d.code, libelle: libelleDomaine(d.libelle, t, pack.value), route: d.route, icone: d.icone, compte: d.compte, domaine: d.code }
}

const groupes = computed<{ titre: string | null; liens: Lien[] }[]>(() => {
  const c = props.composition
  if (c.situation === 'MONO_DOMAINE') {
    const d = c.domaines[0]!
    return [{ titre: null, liens: d.entrees.map((e) => ({ ...e, libelle: libelleDomaine(e.libelle, t, pack.value), domaine: d.code })) }]
  }
  if (c.situation === 'MULTI_FAMILLES') {
    return c.familles.map((f) => ({ titre: t(f.famille.libelleCle), liens: f.domaines.map(depuisDomaine) }))
  }
  return [{ titre: null, liens: c.domaines.map(depuisDomaine) }]
})

function actif(route: string): boolean {
  const [chemin, requete] = route.split('?')
  const [cheminActif, requeteActive] = props.routeActive.split('?')
  return chemin === cheminActif && (requete ?? '') === (requeteActive ?? '')
}
</script>

<template>
  <nav class="navigation" :class="`disposition-${disposition}`" :aria-label="t('coquille.navigation')">
    <div v-for="(groupe, i) in groupes" :key="i" class="groupe" :data-famille="groupe.titre ? '' : undefined">
      <p v-if="groupe.titre" class="famille">{{ groupe.titre }}</p>
      <ul>
        <li v-for="lien in groupe.liens" :key="lien.route">
          <NuxtLink
            :to="lien.route"
            class="lien"
            :data-domaine="lien.domaine"
            :data-entree="lien.code"
            :aria-current="actif(lien.route) ? 'page' : undefined"
          >
            <InterneIcone :nom="lien.icone" :taille="18" />
            <span class="mot">{{ lien.libelle }}</span>
            <span v-if="lien.compte !== null" class="compte">{{ lien.compte }}</span>
          </NuxtLink>
        </li>
      </ul>
    </div>
  </nav>
</template>

<style scoped>
.navigation {
  padding: 8px;
}
ul {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.famille {
  margin: 0;
  padding: 12px 10px 4px;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.04em;
}
.lien {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: var(--cible, var(--cible-standard));
  padding: 0 10px;
  border-radius: var(--rayon-champ);
  color: var(--text-muted);
  font-size: 14px;
  font-weight: 500;
}
.lien:hover {
  background: var(--surface-sunken);
  color: var(--text);
  text-decoration: none;
}
.lien:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: -2px;
}
.lien[aria-current='page'] {
  background: var(--primary-soft);
  color: var(--primary);
  font-weight: 500;
}
.mot {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.compte {
  min-width: 18px;
  padding: 0 5px;
  border-radius: var(--rayon-pastille);
  background: var(--surface-sunken);
  color: var(--text);
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: 11px;
  text-align: center;
}

/* La barre basse : les entrées côte à côte, l'icône au-dessus du mot. */
.disposition-basse {
  padding: 0 4px;
}
.disposition-basse ul {
  flex-direction: row;
  gap: 0;
}
.disposition-basse li {
  flex: 1 1 0;
  min-width: 0;
}
.disposition-basse .lien {
  flex-direction: column;
  justify-content: center;
  gap: 2px;
  padding: 4px 2px;
  font-size: 11px;
  text-align: center;
}
.disposition-basse .lien[aria-current='page'] {
  background: transparent;
  box-shadow: inset 0 2px 0 var(--primary);
}
.disposition-basse .mot {
  max-width: 100%;
}
.disposition-basse .compte {
  display: none;
}
</style>
