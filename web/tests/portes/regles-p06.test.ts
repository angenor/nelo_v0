// Chaque règle de P-06 mord, et laisse passer ce qui est permis (research.md R-11).
import { describe, expect, it } from 'vitest'
import * as p06 from '../../../scripts/portes/p06_interface.mjs'

const vue = (gabarit: string, script = '') =>
  `<script setup lang="ts">\n${script}\n</script>\n<template>\n${gabarit}\n</template>\n`

describe('règle 1 : chaînes en dur', () => {
  it('refuse un texte et un attribut visibles écrits en dur', () => {
    const trouvees = p06.regleChaines('A.vue', vue('<p>Bonjour</p><input placeholder="Nom">'))
    expect(trouvees.map((v: { regle: string }) => v.regle)).toEqual(['chaîne en dur', 'attribut en dur'])
    expect(trouvees[0].ligne).toBe(5)
  })

  it('laisse passer une clé, une interpolation, un séparateur et un attribut lié', () => {
    const source = vue(`<p>{{ t('a.b') }} · {{ nom }}</p><input :placeholder="t('a.c')" type="text">`)
    expect(p06.regleChaines('A.vue', source)).toEqual([])
  })
})

describe('règle 2 : clés', () => {
  it('refuse une clé présente dans une seule langue, et une clé appelée inconnue', () => {
    const trouvees = p06.regleCles({ 'a.b': 'x', 'a.c': 'y' }, { 'a.b': 'x' }, [
      ['A.vue', `{{ t('a.b') }} {{ t('a.inconnue') }}`],
      ['B.ts', `const titre = 'a.absente'`],
    ])
    expect(trouvees.map((v: { detail: string }) => v.detail)).toEqual(['a.c', 'a.inconnue', 'a.absente'])
  })

  it('laisse passer les clés connues, les chaînes pointées d’un autre espace et les expressions liées', () => {
    const trouvees = p06.regleCles({ 'a.b': 'x' }, { 'a.b': 'y' }, [
      ['A.ts', `t('a.b'); const f = 'fichier.css'; const c = 'vie_scolaire.appel.faire'`],
      ['B.vue', `<span :data-voix="a.voix" @click="a.fermer" v-if="a.ouvert" />`],
    ])
    expect(trouvees).toEqual([])
  })
})

describe('règle 3 : couleurs', () => {
  it('refuse une valeur hexadécimale, une fonction, un nom et une classe de palette', () => {
    expect(p06.regleCouleurs('a.css', '.x { color: #12503F; }')).toHaveLength(1)
    expect(p06.regleCouleurs('a.ts', `const c = 'rgb(0 0 0)'`)).toHaveLength(1)
    expect(p06.regleCouleurs('A.vue', vue('<p />') + '<style>\n.x { border-color: white }\n</style>')).toHaveLength(1)
    expect(p06.regleCouleurs('A.vue', vue('<p class="bg-red-500" />'))).toHaveLength(1)
  })

  it('laisse passer les jetons, les ancres et les deux copies du système de design', () => {
    expect(p06.regleCouleurs('a.css', '.x { color: var(--primary); white-space: nowrap }')).toEqual([])
    expect(p06.regleCouleurs('A.vue', vue('<a href="#principal" class="bg-primary text-text" />'))).toEqual([])
    expect(p06.regleCouleurs('web/app/assets/css/theme.css', ':root { --bg:#F6F7F4 }')).toEqual([])
  })
})

describe('règle 4 : plateforme', () => {
  it('refuse navigator, window, localStorage et location hors de la plateforme', () => {
    expect(p06.reglePlateforme('web/app/components/A.vue', vue('<p />', 'const x = navigator.onLine'))).toHaveLength(1)
    expect(p06.reglePlateforme('web/app/pages/b.ts', 'window.addEventListener("x", f)')).toHaveLength(1)
    expect(p06.reglePlateforme('web/app/pages/b.ts', 'localStorage.getItem("x")')).toHaveLength(1)
    expect(p06.reglePlateforme('web/app/pages/b.ts', 'location.reload()')).toHaveLength(1)
  })

  it('laisse passer la plateforme web, le service worker et un commentaire', () => {
    expect(p06.reglePlateforme('web/app/core/plateforme/web.ts', 'navigator.onLine')).toEqual([])
    expect(p06.reglePlateforme('web/app/sw/sw.ts', 'self.skipWaiting()')).toEqual([])
    expect(p06.reglePlateforme('web/app/pages/b.ts', '// jamais window.x ici\nconst n = 1')).toEqual([])
    expect(p06.reglePlateforme('web/app/core/plateforme/plateforme.ts', 'interface Notifications {}')).toEqual([])
  })
})

describe('règle 5 : rôles', () => {
  it('refuse un identifiant de rôle, une clé « role » et une liste de rôles', () => {
    expect(p06.regleRoles('a.ts', `if (compte.role === 'x') {}`)).toHaveLength(1)
    expect(p06.regleRoles('p.json', `{ "role": "DIRECTEUR" }`)).toHaveLength(1)
    expect(p06.regleRoles('a.ts', 'const ROLES = []')).toHaveLength(1)
  })

  it('laisse passer l’attribut ARIA d’un gabarit et le mot français « rôle »', () => {
    expect(p06.regleRoles('A.vue', vue('<button role="switch" />'))).toEqual([])
    expect(p06.regleRoles('a.ts', '// jamais un rôle\nconst carole = 1')).toEqual([])
  })
})
