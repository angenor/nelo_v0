/// <reference lib="webworker" />
// Le service worker mince (FR-045, ADR 002, contracts § 8). Il précache les fichiers statiques
// immuables que la construction liste, nettoie les caches périmés, et applique une nouvelle
// version quand l'application le lui demande. Rien d'autre : les navigations et les requêtes
// vont au réseau, aucune donnée n'est conservée, aucune écriture ne le traverse.
import { cleanupOutdatedCaches, precacheAndRoute } from 'workbox-precaching'

declare const self: ServiceWorkerGlobalScope

precacheAndRoute(self.__WB_MANIFEST)
cleanupOutdatedCaches()

self.addEventListener('message', (evenement) => {
  if (evenement.data?.type === 'SKIP_WAITING') void self.skipWaiting()
})
