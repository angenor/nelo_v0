<script setup lang="ts">
// Le lien d'activation (US6, artboard US6). La personne ouvre le message court reçu : le compte
// s'active, la session s'ouvre, l'appareil devient connu, et l'étape du code personnel s'enchaîne
// sans écran intermédiaire.
//
// L'appel se fait au montage, dans le navigateur : c'est lui qui doit recevoir les cookies de
// session, et un appel au rendu du serveur ne les lui donnerait pas.
//
// Un lien consommé, expiré ou remplacé n'est pas une faute : c'est une information, avec ses
// deux issues. Il n'identifie plus sûrement son tenant, et la personne n'a pas de session :
// l'écran ne peut donc nommer aucun secrétariat ni écrire aucun numéro (écart E-01).
import { ErreurApi } from '~/core/api/client'
import { REFUS } from '~/core/session/etat'

definePageMeta({ sansCoquille: true, contexteTactile: 'standard' })

const PIN = '/connexion/pin'
const NUMERO = '/connexion'

const route = useRoute()
const { t } = useLibelles()
const { activerParInvitation } = useSession()

const refus = ref<string | null>(null)
const jeton = computed(() => String(route.params.jeton ?? ''))

onMounted(async () => {
  try {
    await activerParInvitation(jeton.value)
    await navigateTo(PIN, { external: true })
  } catch (echec) {
    if (!(echec instanceof ErreurApi)) throw echec
    refus.value = echec.code
  }
})

/** Un compte suspendu dit ce qui reste ouvert ; tout autre refus du lien dit ses deux issues. */
const suspendu = computed(() => refus.value === REFUS.compteSuspendu)
</script>

<template>
  <article class="activation">
    <header class="barre">
      <p class="barre-titre">{{ t('session.activation.entete') }}</p>
    </header>

    <div class="corps">
      <p v-if="refus === null" class="attente" aria-live="polite">
        {{ t('session.activation.en_cours') }}
      </p>

      <template v-else-if="suspendu">
        <h1 class="titre">{{ t('session.suspendu.titre') }}</h1>
        <p class="texte">{{ t('session.suspendu.corps') }}</p>
      </template>

      <template v-else>
        <div>
          <h1 class="titre">{{ t('session.activation.invalide.titre') }}</h1>
          <p class="texte">{{ t('session.activation.invalide.corps') }}</p>
        </div>

        <CanonAlerte
          niveau="information"
          titre="session.activation.deux_facons"
          corps="session.activation.deux_facons_corps"
        />

        <div class="issues">
          <NuxtLink :to="NUMERO" class="principale">
            <InterneIcone nom="message" :taille="18" />
            {{ t('session.activation.numero') }}
          </NuxtLink>
          <p class="secretariat">{{ t('session.activation.secretariat') }}</p>
        </div>
      </template>
    </div>
  </article>
</template>

<style scoped>
.activation {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 420px;
  min-height: 100dvh;
  margin: 0 auto;
  background: var(--bg);
}
.barre {
  flex: 0 0 auto;
  padding: 14px 16px;
  border-bottom: var(--filet) solid var(--border);
  background: var(--surface);
}
.barre-titre {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}
.corps {
  display: flex;
  flex-direction: column;
  gap: 18px;
  flex: 1;
  padding: 20px 16px 24px;
}
.attente {
  margin: 0;
  font-size: 14px;
  color: var(--text-muted);
}
.titre {
  margin: 0;
  font-family: var(--font-titres);
  font-weight: 700;
  font-size: 24px;
  line-height: 1.2;
  letter-spacing: -0.02em;
}
.texte {
  margin: 8px 0 0;
  font-size: 14px;
  color: var(--text-muted);
}
.issues {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: auto;
}
.principale {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: var(--cible, var(--cible-standard));
  padding: 0 16px;
  border-radius: var(--rayon-champ);
  background: var(--primary);
  color: var(--primary-ink);
  font-size: 15px;
  font-weight: 500;
}
.principale:hover {
  background: var(--primary-hover);
  color: var(--primary-ink);
  text-decoration: none;
}
.principale:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}
.secretariat {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
  text-align: center;
}
</style>
