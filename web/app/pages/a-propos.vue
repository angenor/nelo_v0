<script setup lang="ts">
// « À propos » : le nom et la version du produit, et l'attribution de ce que l'application
// redistribue (FR-031, 01-stack.md § 9). Les avis de licence sont dans public/licences/.
import { NOM, VERSION } from '~/core/produit'

definePageMeta({ contexteTactile: 'standard' })

const { t } = useLibelles()
const POLICES = [
  { nom: 'Archivo', licence: '/licences/archivo.txt' },
  { nom: 'Public Sans', licence: '/licences/public-sans.txt' },
  { nom: 'IBM Plex Mono', licence: '/licences/ibm-plex-mono.txt' },
]
</script>

<template>
  <article class="a-propos">
    <header>
      <h1 class="titre">{{ t('apropos.titre', { nom: NOM }) }}</h1>
      <p class="version">{{ t('apropos.version', { version: VERSION }) }}</p>
      <p>{{ t('apropos.description') }}</p>
    </header>
    <section aria-labelledby="polices">
      <h2 id="polices" class="sous-titre">{{ t('apropos.polices') }}</h2>
      <ul class="liste">
        <li v-for="police in POLICES" :key="police.nom" class="element">
          <p>{{ t('apropos.police', { nom: police.nom }) }}</p>
          <a :href="police.licence" class="lien" :lang="'en'">{{ t('apropos.lire_licence', { nom: police.nom }) }}</a>
        </li>
      </ul>
    </section>
    <section aria-labelledby="icones">
      <h2 id="icones" class="sous-titre">{{ t('apropos.icones_titre') }}</h2>
      <p>{{ t('apropos.icones') }}</p>
    </section>
  </article>
</template>

<style scoped>
.a-propos {
  display: flex;
  flex-direction: column;
  gap: 24px;
  width: 100%;
  max-width: 640px;
  margin: 0 auto;
  padding: 20px 16px 40px;
  font-size: 14px;
}
.titre {
  margin: 0;
  font-family: var(--font-titres);
  font-weight: 700;
  font-size: 26px;
  letter-spacing: -0.02em;
}
.version {
  margin: 4px 0 12px;
  font-family: var(--font-mono);
  font-weight: 500;
  color: var(--text-muted);
}
.sous-titre {
  margin: 0 0 8px;
  font-family: var(--font-titres);
  font-weight: 600;
  font-size: 18px;
}
p {
  margin: 0;
}
.liste {
  display: flex;
  flex-direction: column;
  margin: 0;
  padding: 0;
  list-style: none;
}
.element {
  padding: 8px 0;
  border-top: var(--filet) solid var(--border);
}
.lien {
  display: inline-flex;
  align-items: center;
  min-height: var(--cible, var(--cible-standard));
}
</style>
