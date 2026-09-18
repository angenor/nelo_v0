<script setup lang="ts">
// La définition du code personnel (US3, artboard US3 « Le pourquoi, puis deux saisies »).
//
// Trois choses le gouvernent :
//   - le pourquoi vient avant le quoi : on dit à quoi sert ce code avant de le demander ;
//   - le code se saisit deux fois, et la différence entre les deux dit la règle et le geste ;
//   - « Plus tard » n'est pas une pénalité : la personne retrouve le parcours par SMS, entier.
//
// Rien n'est jugé ici : le serveur seul décide (quatre chiffres, code courant exigé ou non).
// L'écran traduit sa réponse, et la vérification de forme évite un aller-retour inutile.
import { ErreurApi } from '~/core/api/client'
import { etatEcranPin, formePin } from '~/core/session/ecrans'

definePageMeta({ sansCoquille: true, contexteTactile: 'standard' })

const ACCUEIL = '/'

const { t } = useLibelles()
const { definirPin } = useSession()

const pin = ref('')
const confirmation = ref('')
const tentee = ref(false)
const refus = ref<string | null>(null)
const occupe = ref(false)

const ecran = computed(() =>
  etatEcranPin({
    pin: pin.value,
    confirmation: confirmation.value,
    tentee: tentee.value,
    refus: refus.value,
  }),
)

// Un refus porte sur le code qu'on a envoyé : dès qu'il change, il ne vaut plus.
watch([pin, confirmation], () => {
  refus.value = null
})

/**
 * Où l'on va, une fois le code défini ou remis à plus tard : l'accueil, par un vrai
 * chargement. Les jetons vivent dans des cookies qu'aucun script ne lit, et c'est le rendu du
 * serveur qui va chercher le contexte de la session.
 */
function versAccueil() {
  return navigateTo(ACCUEIL, { external: true })
}

async function enregistrer() {
  if (occupe.value) return
  tentee.value = true
  refus.value = null
  if (!formePin(pin.value) || confirmation.value !== pin.value) return
  occupe.value = true
  try {
    await definirPin(pin.value)
    await versAccueil()
  } catch (echec) {
    if (!(echec instanceof ErreurApi)) throw echec
    refus.value = echec.code
    tentee.value = false
  } finally {
    occupe.value = false
  }
}
</script>

<template>
  <article class="pin">
    <header class="barre">
      <span class="etape-faite">
        <InterneIcone nom="coche" :taille="16" />
        {{ t('session.pin.verifie') }}
      </span>
      <span class="etape">{{ t('session.pin.etape') }}</span>
    </header>

    <div class="corps">
      <div>
        <h1 class="titre">{{ t('session.pin.titre') }}</h1>
        <p class="pourquoi">{{ t('session.pin.pourquoi') }}</p>
      </div>

      <form class="formulaire" novalidate @submit.prevent="enregistrer">
        <CanonChamp
          v-model="pin"
          libelle="session.pin.champ"
          saisie="code"
          aide="session.pin.aide"
          :erreur="ecran.erreur ?? undefined"
        />
        <CanonChamp
          v-model="confirmation"
          libelle="session.pin.confirmation"
          saisie="code"
          :erreur="ecran.erreurConfirmation ?? undefined"
        />
        <CanonBouton
          variante="principal"
          type="submit"
          pleine-largeur
          libelle="session.pin.enregistrer"
        />
      </form>

      <p class="plus-tard">
        <CanonBouton variante="discret" libelle="session.pin.plus_tard" @appui="versAccueil" />
      </p>
    </div>
  </article>
</template>

<style scoped>
.pin {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 420px;
  min-height: 100dvh;
  margin: 0 auto;
  background: var(--bg);
}
.barre {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex: 0 0 auto;
  padding: 10px 16px;
  border-bottom: var(--filet) solid var(--border);
  background: var(--surface);
}
.etape-faite {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: var(--pastille);
  padding: 0 10px;
  border-radius: var(--rayon-pastille);
  background: var(--success-soft);
  color: var(--success);
  font-size: 13px;
  font-weight: 500;
}
.etape {
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-muted);
}
.corps {
  display: flex;
  flex-direction: column;
  gap: 22px;
  flex: 1;
  padding: 20px 16px 24px;
}
.titre {
  margin: 0;
  font-family: var(--font-titres);
  font-weight: 700;
  font-size: 24px;
  line-height: 1.2;
  letter-spacing: -0.02em;
}
.pourquoi {
  margin: 8px 0 0;
  font-size: 14px;
  color: var(--text-muted);
}
.formulaire {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.plus-tard {
  display: flex;
  justify-content: center;
  margin: auto 0 0;
}
</style>
