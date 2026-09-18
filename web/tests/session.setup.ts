// La session semée des portes (research.md R-11). Un projet Playwright « setup » ouvre une
// vraie session, par le vrai chemin : demander un code, le lire dans le journal des messages
// simulés, le vérifier. Aucun raccourci de test côté serveur : un chemin d'ouverture qui
// n'existe pas en production ne prouverait rien.
//
// Les requêtes passent par le relais de Nitro, sous l'origine de l'application : l'état
// enregistré porte donc les cookies que le navigateur aurait, `nelo_acces` compris.
//
// Ce que le tour attend de son environnement, posé par scripts/avec-serveur-dev.sh :
//   NELO_SMS_JOURNAL : le fichier où la passerelle simulée écrit une ligne JSON par envoi ;
//   NUMERO_A         : le numéro du compte du jeu d'essai.
// Tant qu'US1 n'a livré aucune route d'authentification, ce projet échoue : il n'est déclaré
// que si NELO_SESSION_SEMEE vaut 1 (voir playwright.config.ts).
import { existsSync, mkdirSync, readFileSync } from 'node:fs'
import { dirname } from 'node:path'
import { expect, request, test as setup } from '@playwright/test'
import { uuid7 } from '../app/core/api/uuid7'
import { ETAT_SESSION } from './portes/outils'

const JOURNAL = process.env.NELO_SMS_JOURNAL ?? ''
const NUMERO = process.env.NUMERO_A ?? ''
const CODE = /(?<!\d)(\d{6})(?!\d)/
/**
 * Le code personnel de la session semée (US3). Il est défini dans les dix minutes qui suivent
 * l'ouverture par code reçu : le serveur en dispense alors le code courant. L'état enregistré
 * porte ainsi `nelo_appareils`, et les écrans d'ouverture par code personnel se visitent.
 */
const PIN = '4242'
const ATTENTE_MS = 100
const ESSAIS = 100

interface EnvoiJournalise {
  destinataire: string
  texte: string
}

function envoisVers(numero: string): EnvoiJournalise[] {
  if (!existsSync(JOURNAL)) return []
  return readFileSync(JOURNAL, 'utf8')
    .split('\n')
    .filter((ligne) => ligne.trim() !== '')
    .map((ligne) => JSON.parse(ligne) as EnvoiJournalise)
    .filter((envoi) => envoi.destinataire === numero)
}

async function attendreCode(numero: string, deja: number): Promise<string> {
  for (let essai = 0; essai < ESSAIS; essai++) {
    const envois = envoisVers(numero)
    const dernier = envois.length > deja ? envois[envois.length - 1] : undefined
    const trouve = dernier ? CODE.exec(dernier.texte)?.[1] : undefined
    if (trouve) return trouve
    await new Promise((resoudre) => setTimeout(resoudre, ATTENTE_MS))
  }
  throw new Error(`session semée : aucun code pour ${numero} dans ${JOURNAL}`)
}

setup('la session semée est ouverte et son état enregistré', async ({ baseURL }) => {
  expect(JOURNAL, 'session semée : NELO_SMS_JOURNAL n’est pas posé').not.toBe('')
  expect(NUMERO, 'session semée : NUMERO_A n’est pas posé').not.toBe('')

  const contexte = await request.newContext({ baseURL })
  try {
    const avant = envoisVers(NUMERO).length
    const demande = await contexte.post('/api/v1/auth/otp', {
      headers: { 'X-Nelo-Requete': uuid7() },
      data: { identifiant: NUMERO },
    })
    expect(demande.status(), 'session semée : la demande de code').toBe(204)

    const code = await attendreCode(NUMERO, avant)
    const verification = await contexte.post('/api/v1/auth/otp/verification', {
      headers: { 'X-Nelo-Requete': uuid7() },
      data: { identifiant: NUMERO, code },
    })
    expect(verification.status(), 'session semée : la vérification du code').toBe(200)

    const definition = await contexte.post('/api/v1/auth/pin/definition', {
      headers: { 'X-Nelo-Requete': uuid7() },
      data: { pin: PIN },
    })
    expect(definition.status(), 'session semée : la définition du code personnel').toBe(204)

    mkdirSync(dirname(ETAT_SESSION), { recursive: true })
    await contexte.storageState({ path: ETAT_SESSION })
  } finally {
    await contexte.dispose()
  }
})
