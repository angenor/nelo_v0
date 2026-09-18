// L'unique implémentation de la plateforme : le navigateur (research.md R-09). C'est le seul
// fichier de l'application, avec le service worker, qui touche navigator, window et document ;
// P-06 (règle 4) refuse ces appels partout ailleurs.
import type { Apparence, Application, Clavier, Cookies, EtatReseau, Plateforme, Reseau, Stockage } from './plateforme'

const TYPES_FAIBLES = new Set(['slow-2g', '2g', '3g'])

interface Connexion extends EventTarget {
  readonly effectiveType?: string
}

function connexion(): Connexion | undefined {
  try {
    return (navigator as Navigator & { connection?: Connexion }).connection
  } catch {
    return undefined
  }
}

function lireEtat(): EtatReseau {
  try {
    if (typeof navigator !== 'undefined' && navigator.onLine === false) return 'absent'
  } catch {
    return 'bon'
  }
  const type = connexion()?.effectiveType
  return type !== undefined && TYPES_FAIBLES.has(type) ? 'faible' : 'bon'
}

function creerReseau(): Reseau {
  return {
    get etat() {
      return lireEtat()
    },
    surChangement(rappel) {
      if (typeof window === 'undefined') return () => {}
      const signaler = () => rappel(lireEtat())
      const lien = connexion()
      window.addEventListener('online', signaler)
      window.addEventListener('offline', signaler)
      lien?.addEventListener('change', signaler)
      return () => {
        window.removeEventListener('online', signaler)
        window.removeEventListener('offline', signaler)
        lien?.removeEventListener('change', signaler)
      }
    },
  }
}

function preferenceSombre(): MediaQueryList | null {
  try {
    return window.matchMedia('(prefers-color-scheme: dark)')
  } catch {
    return null
  }
}

function creerApparence(): Apparence {
  return {
    get sombre() {
      return preferenceSombre()?.matches ?? false
    },
    surChangement(rappel) {
      const requete = preferenceSombre()
      if (!requete) return () => {}
      const signaler = (evenement: MediaQueryListEvent) => rappel(evenement.matches)
      requete.addEventListener('change', signaler)
      return () => requete.removeEventListener('change', signaler)
    },
  }
}

function creerApplication(): Application {
  return {
    recharger() {
      try {
        window.location.reload()
      } catch {
        // Hors navigateur : rien à recharger.
      }
    },
    saisieEnCours() {
      try {
        const actif = document.activeElement
        return actif instanceof HTMLInputElement || actif instanceof HTMLTextAreaElement || actif instanceof HTMLSelectElement
      } catch {
        return false
      }
    },
  }
}

function appareilApple(): boolean {
  try {
    return /Mac|iPhone|iPad/.test(navigator.userAgent)
  } catch {
    return false
  }
}

function creerClavier(): Clavier {
  return {
    libelle(touche) {
      return `${appareilApple() ? '⌘' : 'Ctrl'} ${touche.toUpperCase()}`
    },
    surRaccourci(touche, rappel) {
      if (typeof window === 'undefined') return () => {}
      const ecouter = (evenement: KeyboardEvent) => {
        if ((evenement.ctrlKey || evenement.metaKey) && evenement.key.toLowerCase() === touche) {
          evenement.preventDefault()
          rappel()
        }
      }
      window.addEventListener('keydown', ecouter)
      return () => window.removeEventListener('keydown', ecouter)
    },
  }
}

function stockageLocal(): globalThis.Storage | null {
  try {
    const stockage = globalThis.localStorage
    if (!stockage) return null
    const sonde = '__nelo_sonde__'
    stockage.setItem(sonde, sonde)
    stockage.removeItem(sonde)
    return stockage
  } catch {
    return null
  }
}

function creerStockage(): Stockage {
  const local = stockageLocal()
  return {
    disponible: local !== null,
    lire(cle) {
      try {
        return local?.getItem(cle) ?? null
      } catch {
        return null
      }
    },
    ecrire(cle, valeur) {
      try {
        local?.setItem(cle, valeur)
      } catch {
        // Quota dépassé ou stockage refusé : la préférence n'est pas mémorisée, rien ne casse.
      }
    },
    effacer(cle) {
      try {
        local?.removeItem(cle)
      } catch {
        // Idem.
      }
    },
  }
}

/**
 * Les cookies sans secret de l'appareil (research.md R-21). `SameSite=Strict` et le chemin de
 * l'application ; jamais `HttpOnly`, puisque c'est la page qui l'écrit, et jamais un jeton :
 * les trois cookies de session appartiennent au relais, qui est seul à les connaître.
 */
function creerCookies(): Cookies {
  const AN = 60 * 60 * 24 * 365
  function poser(nom: string, valeur: string, duree: number): void {
    try {
      const sur = document.location.protocol === 'https:' ? '; Secure' : ''
      document.cookie = `${nom}=${encodeURIComponent(valeur)}; Path=/; Max-Age=${duree}; SameSite=Strict${sur}`
    } catch {
      // Cookies refusés : le rendu serveur retombera sur le premier rattachement, rien ne casse.
    }
  }
  return {
    get disponible() {
      try {
        return typeof document !== 'undefined'
      } catch {
        return false
      }
    },
    ecrire(nom, valeur) {
      poser(nom, valeur, AN)
    },
    effacer(nom) {
      poser(nom, '', 0)
    },
  }
}

async function capturer(): Promise<Blob | null> {
  let flux: MediaStream | null = null
  try {
    flux = await navigator.mediaDevices.getUserMedia({ video: true })
    const video = document.createElement('video')
    video.srcObject = flux
    video.muted = true
    await video.play()
    const toile = document.createElement('canvas')
    toile.width = video.videoWidth
    toile.height = video.videoHeight
    toile.getContext('2d')?.drawImage(video, 0, 0)
    return await new Promise<Blob | null>((resoudre) => toile.toBlob(resoudre, 'image/jpeg'))
  } catch {
    return null
  } finally {
    flux?.getTracks().forEach((piste) => piste.stop())
  }
}

function notificationsDisponibles(): boolean {
  try {
    return typeof Notification !== 'undefined'
  } catch {
    return false
  }
}

export function creerPlateformeWeb(): Plateforme {
  let cameraDisponible = false
  try {
    cameraDisponible = typeof navigator.mediaDevices?.getUserMedia === 'function'
  } catch {
    cameraDisponible = false
  }
  const notifications = notificationsDisponibles()
  return {
    application: creerApplication(),
    reseau: creerReseau(),
    apparence: creerApparence(),
    clavier: creerClavier(),
    stockage: creerStockage(),
    cookies: creerCookies(),
    camera: {
      disponible: cameraDisponible,
      capturer: () => (cameraDisponible ? capturer() : Promise.resolve(null)),
    },
    notifications: {
      disponible: notifications,
      async demander() {
        if (!notifications) return 'refusee'
        try {
          return (await Notification.requestPermission()) === 'granted' ? 'accordee' : 'refusee'
        } catch {
          return 'refusee'
        }
      },
      afficher(titre, corps) {
        if (!notifications) return
        try {
          if (Notification.permission === 'granted') new Notification(titre, { body: corps })
        } catch {
          // Le navigateur refuse l'affichage : rien ne remonte vers l'écran.
        }
      },
    },
  }
}
