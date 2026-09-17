// Les icônes de l'application, générées depuis les jetons (research.md R-08, écart E-01).
//
// La lettre initiale de NOM_COURT (core/produit.ts), en Archivo 700 (Fontsource, fichier woff lu
// par opentype.js), encre --primary-ink sur fond --primary du thème clair (docs/design/tokens.json).
// Le contour est rempli ici, règle non nulle, suréchantillonné, puis encodé en PNG par zlib :
// aucun navigateur, aucune bibliothèque d'image. Sortie : web/public/icones/, ignorée par git.
//
//   192.png, 512.png         coins arrondis, lettre au format « any »
//   512-maskable.png          fond plein, lettre dans la zone sûre (« maskable »)
//   180.png                   apple-touch-icon, fond plein
//   32.png                    favicon, la plus légère
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { deflateSync } from 'node:zlib'
import opentype from 'opentype.js'

const WEB = join(dirname(fileURLToPath(import.meta.url)), '..')
const RACINE = join(WEB, '..')
const require = createRequire(join(WEB, 'package.json'))
const SORTIE = join(WEB, 'public/icones')
const SOUS = 4 // échantillons par pixel, sur chaque axe

const jetons = JSON.parse(readFileSync(join(RACINE, 'docs/design/tokens.json'), 'utf8'))
const produit = readFileSync(join(WEB, 'app/core/produit.ts'), 'utf8')
const nomCourt = /NOM_COURT\s*=\s*'([^']+)'/.exec(produit)?.[1]
if (!nomCourt) throw new Error('icones : NOM_COURT introuvable dans app/core/produit.ts')
const lettre = nomCourt[0].toUpperCase()

function rvb(hexa) {
  const m = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(hexa)
  if (!m) throw new Error(`icones : couleur illisible ${hexa}`)
  return m.slice(1).map((c) => Number.parseInt(c, 16))
}
const FOND = rvb(jetons.clair['--primary'])
const ENCRE = rvb(jetons.clair['--primary-ink'])

const fichierPolice = readFileSync(require.resolve('@fontsource/archivo/files/archivo-latin-700-normal.woff'))
const police = opentype.parse(
  fichierPolice.buffer.slice(fichierPolice.byteOffset, fichierPolice.byteOffset + fichierPolice.byteLength),
)

/** Le contour de la lettre, aplati en polygones, centré dans un carré de côté `cote`. */
function contours(cote, proportion) {
  const glyphe = police.charToGlyph(lettre)
  const brut = glyphe.getPath(0, 0, 1000)
  const boite = brut.getBoundingBox()
  const echelle = (cote * proportion) / Math.max(boite.x2 - boite.x1, boite.y2 - boite.y1)
  const dx = (cote - (boite.x2 - boite.x1) * echelle) / 2 - boite.x1 * echelle
  const dy = (cote - (boite.y2 - boite.y1) * echelle) / 2 - boite.y1 * echelle
  const polygones = []
  let courant = []
  let [px, py] = [0, 0]
  const point = (x, y) => courant.push([x * echelle + dx, y * echelle + dy])
  for (const c of brut.commands) {
    if (c.type === 'M') {
      if (courant.length) polygones.push(courant)
      courant = []
      point(c.x, c.y)
    } else if (c.type === 'L') {
      point(c.x, c.y)
    } else if (c.type === 'Q') {
      for (let i = 1; i <= 12; i++) {
        const t = i / 12
        const u = 1 - t
        point(u * u * px + 2 * u * t * c.x1 + t * t * c.x, u * u * py + 2 * u * t * c.y1 + t * t * c.y)
      }
    } else if (c.type === 'C') {
      for (let i = 1; i <= 16; i++) {
        const t = i / 16
        const u = 1 - t
        point(
          u ** 3 * px + 3 * u * u * t * c.x1 + 3 * u * t * t * c.x2 + t ** 3 * c.x,
          u ** 3 * py + 3 * u * u * t * c.y1 + 3 * u * t * t * c.y2 + t ** 3 * c.y,
        )
      }
    } else if (c.type === 'Z') {
      if (courant.length) polygones.push(courant)
      courant = []
    }
    if ('x' in c) [px, py] = [c.x, c.y]
  }
  if (courant.length) polygones.push(courant)
  return polygones
}

/** Couverture de chaque pixel par les polygones, règle non nulle, par balayage suréchantillonné. */
function couverture(cote, polygones) {
  const cases = new Float32Array(cote * cote)
  const aretes = polygones.flatMap((p) =>
    p.map((a, i) => {
      const b = p[(i + 1) % p.length]
      return { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }
    }),
  )
  for (let ligne = 0; ligne < cote * SOUS; ligne++) {
    const y = (ligne + 0.5) / SOUS
    const croisements = []
    for (const e of aretes) {
      if (e.y1 === e.y2) continue
      const monte = e.y1 < e.y2
      const [ya, yb] = monte ? [e.y1, e.y2] : [e.y2, e.y1]
      if (y < ya || y >= yb) continue
      croisements.push({ x: e.x1 + ((y - e.y1) * (e.x2 - e.x1)) / (e.y2 - e.y1), sens: monte ? 1 : -1 })
    }
    croisements.sort((a, b) => a.x - b.x)
    let enroulement = 0
    const rangee = Math.floor(ligne / SOUS) * cote
    for (let i = 0; i < croisements.length - 1; i++) {
      enroulement += croisements[i].sens
      if (enroulement === 0) continue
      const debut = Math.max(0, croisements[i].x)
      const fin = Math.min(cote, croisements[i + 1].x)
      for (let x = Math.floor(debut); x < Math.ceil(fin); x++) {
        const part = Math.min(fin, x + 1) - Math.max(debut, x)
        if (part > 0) cases[rangee + x] += part / SOUS
      }
    }
  }
  return cases
}

/** Couverture d'un carré aux coins arrondis de rayon `rayon`. */
function carreArrondi(cote, rayon) {
  const cases = new Float32Array(cote * cote)
  for (let y = 0; y < cote; y++) {
    for (let x = 0; x < cote; x++) {
      let somme = 0
      for (let sy = 0; sy < SOUS; sy++) {
        for (let sx = 0; sx < SOUS; sx++) {
          const px = x + (sx + 0.5) / SOUS
          const py = y + (sy + 0.5) / SOUS
          const cx = Math.min(Math.max(px, rayon), cote - rayon)
          const cy = Math.min(Math.max(py, rayon), cote - rayon)
          if ((px - cx) ** 2 + (py - cy) ** 2 <= rayon * rayon) somme++
        }
      }
      cases[y * cote + x] = somme / (SOUS * SOUS)
    }
  }
  return cases
}

const TABLE_CRC = Array.from({ length: 256 }, (_, n) => {
  let c = n
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1
  return c >>> 0
})
function crc32(tampon) {
  let c = 0xffffffff
  for (const octet of tampon) c = TABLE_CRC[(c ^ octet) & 0xff] ^ (c >>> 8)
  return (c ^ 0xffffffff) >>> 0
}
function bloc(type, donnees) {
  const longueur = Buffer.alloc(4)
  longueur.writeUInt32BE(donnees.length)
  const corps = Buffer.concat([Buffer.from(type, 'ascii'), donnees])
  const somme = Buffer.alloc(4)
  somme.writeUInt32BE(crc32(corps))
  return Buffer.concat([longueur, corps, somme])
}
function png(cote, pixels) {
  const entete = Buffer.alloc(13)
  entete.writeUInt32BE(cote, 0)
  entete.writeUInt32BE(cote, 4)
  entete.set([8, 6, 0, 0, 0], 8) // 8 bits, RVBA
  const brut = Buffer.alloc((cote * 4 + 1) * cote)
  for (let y = 0; y < cote; y++) {
    brut[y * (cote * 4 + 1)] = 0
    pixels.copy(brut, y * (cote * 4 + 1) + 1, y * cote * 4, (y + 1) * cote * 4)
  }
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    bloc('IHDR', entete),
    bloc('IDAT', deflateSync(brut, { level: 9 })),
    bloc('IEND', Buffer.alloc(0)),
  ])
}

function icone(cote, { arrondi, proportion }) {
  const fond = arrondi ? carreArrondi(cote, cote * 0.22) : new Float32Array(cote * cote).fill(1)
  const encre = couverture(cote, contours(cote, proportion))
  const pixels = Buffer.alloc(cote * cote * 4)
  for (let i = 0; i < cote * cote; i++) {
    const e = Math.min(1, encre[i])
    for (let c = 0; c < 3; c++) pixels[i * 4 + c] = Math.round(FOND[c] * (1 - e) + ENCRE[c] * e)
    pixels[i * 4 + 3] = Math.round(fond[i] * 255)
  }
  return png(cote, pixels)
}

mkdirSync(SORTIE, { recursive: true })
const ICONES = [
  ['192.png', 192, { arrondi: true, proportion: 0.56 }],
  ['512.png', 512, { arrondi: true, proportion: 0.56 }],
  ['512-maskable.png', 512, { arrondi: false, proportion: 0.42 }],
  ['180.png', 180, { arrondi: false, proportion: 0.5 }],
  ['32.png', 32, { arrondi: true, proportion: 0.62 }],
]
for (const [nom, cote, options] of ICONES) writeFileSync(join(SORTIE, nom), icone(cote, options))
console.log(`icones : ${ICONES.length} fichiers, lettre « ${lettre} », dans public/icones/`)
