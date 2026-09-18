// L'identifiant de requête (`X-Nelo-Requete`, 03-api.md § 1.2) : un UUID version 7, dont les
// quarante-huit premiers bits portent l'horloge en millisecondes. Deux identifiants tirés dans
// l'ordre se rangent dans l'ordre, ce qui rend le journal d'idempotence lisible.
//
// Aucune dépendance : le hasard vient de `crypto.getRandomValues`, présent au navigateur comme
// au serveur de rendu. La variante et la version sont posées à la main, selon la RFC 9562.

const OCTETS = 16
const HEXA = Array.from({ length: 256 }, (_, n) => n.toString(16).padStart(2, '0'))

/**
 * Un UUID version 7. `maintenant` n'existe que pour les tests : en usage, c'est l'horloge.
 */
export function uuid7(maintenant: number = Date.now()): string {
  const octets = new Uint8Array(OCTETS)
  crypto.getRandomValues(octets)
  let horloge = Math.trunc(maintenant)
  for (let rang = 5; rang >= 0; rang--) {
    octets[rang] = horloge % 256
    horloge = Math.floor(horloge / 256)
  }
  octets[6] = (octets[6]! & 0x0f) | 0x70
  octets[8] = (octets[8]! & 0x3f) | 0x80
  const chiffres = Array.from(octets, (octet) => HEXA[octet]!)
  return [
    chiffres.slice(0, 4).join(''),
    chiffres.slice(4, 6).join(''),
    chiffres.slice(6, 8).join(''),
    chiffres.slice(8, 10).join(''),
    chiffres.slice(10, 16).join(''),
  ].join('-')
}
