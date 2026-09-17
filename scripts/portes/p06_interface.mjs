// PORTE P-06 : aucune littérale d'interface (docs/01-stack.md § 7, research.md R-11).
//
// Cinq règles sur web/app/, chacune nommant le fichier et la ligne en échec :
//   1. chaînes : aucun texte ni attribut visible écrit en dur dans un gabarit ;
//   2. clés : fr.json et en.json portent les mêmes clés, et toute clé appelée existe ;
//   3. couleurs : aucune valeur de couleur hors theme.css et mesures.css ;
//   4. plateforme : aucun appel au navigateur hors core/plateforme/web*.ts et sw/ ;
//   5. rôles : aucun identifiant de rôle, hors l'attribut ARIA d'un gabarit.
// Plus la comparaison octet à octet des deux copies du système de design.
//
// Les fonctions de règle sont exportées pour web/tests/portes/regles-p06.test.ts.
import { readdirSync, readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { dirname, join, relative, resolve } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const RACINE = resolve(dirname(fileURLToPath(import.meta.url)), '../..')
const WEB = join(RACINE, 'web')
const APP = join(WEB, 'app')
const { parse } = createRequire(join(WEB, 'package.json'))('@vue/compiler-sfc')

const ATTRIBUTS_VISIBLES = new Set([
  'placeholder',
  'title',
  'alt',
  'aria-label',
  'aria-description',
  'aria-placeholder',
  'aria-roledescription',
  'aria-valuetext',
  'label',
])
const NOEUD_ELEMENT = 1
const NOEUD_TEXTE = 2
const NOEUD_ATTRIBUT = 6
const LETTRE = /\p{L}/u

const COPIES = ['theme.css', 'mesures.css']
const COULEURS_NOMMEES =
  'aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue blueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue darkcyan darkgoldenrod darkgray darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid darkred darksalmon darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink deepskyblue dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite gold goldenrod gray green greenyellow grey honeydew hotpink indianred indigo ivory khaki lavender lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan lightgoldenrodyellow lightgray lightgreen lightgrey lightpink lightsalmon lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime limegreen linen magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen mediumslateblue mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin navajowhite navy oldlace olive olivedrab orange orangered orchid palegoldenrod palegreen paleturquoise palevioletred papayawhip peachpuff peru pink plum powderblue purple rebeccapurple red rosybrown royalblue saddlebrown salmon sandybrown seagreen seashell sienna silver skyblue slateblue slategray slategrey snow springgreen steelblue tan teal thistle tomato turquoise violet wheat white whitesmoke yellow yellowgreen'.split(
    ' ',
  )
const COULEUR_NOMMEE = new RegExp(`:[^;{}]*?\\b(${COULEURS_NOMMEES.join('|')})\\b`, 'i')
const COULEUR_FONCTION = /\b(rgba?|hsla?|hwb|oklch|oklab|lab|lch|color-mix|color)\(/i
const COULEUR_HEXA = /(^|[\s:(,'"`=])#([0-9a-f]{8}|[0-9a-f]{6}|[0-9a-f]{3,4})\b/i
const CLASSE_PALETTE =
  /\b(?:bg|text|border|fill|stroke|ring|outline|from|to|via|shadow|accent|caret|decoration|divide|placeholder)-(?:black|white|(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-\d{2,3})\b/

const PLATEFORME_OBJET = /\b(navigator|window|document|globalThis|self)\s*\??\.\s*[A-Za-z_]/
const PLATEFORME_IDENT = /\b(localStorage|sessionStorage|indexedDB|Notification|caches|matchMedia)\b/
const PLATEFORME_ADRESSE = /\b(location|history)\s*\.\s*(reload|assign|replace|href|back|forward|go|pushState|replaceState)\b/
const ROLE = /\b[Rr]oles?\b|\bROLES?\b/

function violation(regle, fichier, ligne, detail) {
  return { regle, fichier, ligne, detail }
}

function ligneDe(source, index) {
  return source.slice(0, index).split('\n').length
}

/** Retire les commentaires, en gardant les sauts de ligne pour que les numéros restent justes. */
export function sansCommentaires(source) {
  const blanc = (m) => m.replace(/[^\n]/g, ' ')
  return source
    .replace(/<!--[\s\S]*?-->/g, blanc)
    .replace(/\/\*[\s\S]*?\*\//g, blanc)
    .replace(/(^|[^:'"`\\])\/\/[^\n]*/g, (m, avant) => avant + blanc(m.slice(avant.length)))
}

function parcourir(noeud, visiter) {
  visiter(noeud)
  for (const enfant of noeud.children ?? []) parcourir(enfant, visiter)
  for (const branche of noeud.branches ?? []) parcourir(branche, visiter)
}

/** Règle 1 : aucun texte visible ni attribut visible statique dans un gabarit. */
export function regleChaines(fichier, source) {
  if (!fichier.endsWith('.vue')) return []
  const { descriptor } = parse(source, { filename: fichier })
  const ast = descriptor.template?.ast
  if (!ast) return []
  const trouvees = []
  parcourir(ast, (noeud) => {
    if (noeud.type === NOEUD_TEXTE && LETTRE.test(noeud.content)) {
      trouvees.push(
        violation('chaîne en dur', fichier, noeud.loc.start.line, noeud.content.trim().slice(0, 40)),
      )
    }
    if (noeud.type === NOEUD_ELEMENT) {
      for (const prop of noeud.props) {
        if (
          prop.type === NOEUD_ATTRIBUT &&
          ATTRIBUTS_VISIBLES.has(prop.name) &&
          prop.value &&
          LETTRE.test(prop.value.content)
        ) {
          trouvees.push(
            violation('attribut en dur', fichier, prop.loc.start.line, `${prop.name}="${prop.value.content}"`),
          )
        }
      }
    }
  })
  return trouvees
}

/** Règle 2 : mêmes clés en fr et en en, et toute clé appelée existe. */
export function regleCles(fr, en, sources) {
  const trouvees = []
  const cleFr = new Set(Object.keys(fr))
  const cleEn = new Set(Object.keys(en))
  for (const cle of cleFr) if (!cleEn.has(cle)) trouvees.push(violation('clé absente de en.json', 'en.json', 0, cle))
  for (const cle of cleEn) if (!cleFr.has(cle)) trouvees.push(violation('clé absente de fr.json', 'fr.json', 0, cle))
  const espaces = new Set([...cleFr].map((cle) => cle.split('.')[0]))
  const appel = /\bt\(\s*['"]([^'"]+)['"]/g
  const litterale = /['"]([a-z_]+(?:\.[A-Za-z_]+)+)['"]/g
  for (const [fichier, brute] of sources) {
    const source = sansCommentaires(brute)
    const vues = new Set()
    for (const motif of [appel, litterale]) {
      for (const m of source.matchAll(motif)) {
        const cle = m[1]
        const ligne = ligneDe(source, m.index)
        if (motif === litterale && !espaces.has(cle.split('.')[0])) continue
        // Une valeur d'attribut lié (:attr="…", @evt="…", v-…="…") est une expression, pas une clé.
        if (motif === litterale && m[0][0] === '"' && /(?:^|\s)(?::|@|v-)[\w:.-]*=$/.test(source.slice(0, m.index))) continue
        if (cleFr.has(cle) || vues.has(`${ligne}:${cle}`)) continue
        vues.add(`${ligne}:${cle}`)
        trouvees.push(violation('clé inconnue', fichier, ligne, cle))
      }
    }
  }
  return trouvees
}

/** Règle 3 : aucune valeur de couleur hors des deux copies du système de design. */
export function regleCouleurs(fichier, brute) {
  if (COPIES.some((copie) => fichier.endsWith(`assets/css/${copie}`))) return []
  const source = sansCommentaires(brute)
  const trouvees = []
  const estCss = fichier.endsWith('.css')
  const blocsStyle = fichier.endsWith('.vue')
    ? [...source.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)].map((m) => [m.index, m[0]])
    : []
  source.split('\n').forEach((ligne, i) => {
    for (const [motif, nom] of [
      [COULEUR_HEXA, 'valeur hexadécimale'],
      [COULEUR_FONCTION, 'fonction de couleur'],
      [CLASSE_PALETTE, 'classe de palette'],
    ]) {
      const m = motif.exec(ligne)
      if (m) trouvees.push(violation(`couleur littérale (${nom})`, fichier, i + 1, m[0].trim()))
    }
  })
  const cssAInspecter = estCss ? [[0, source]] : blocsStyle
  for (const [debut, css] of cssAInspecter) {
    css.split('\n').forEach((ligne, i) => {
      const m = COULEUR_NOMMEE.exec(ligne)
      if (m) {
        trouvees.push(
          violation('couleur littérale (nom)', fichier, ligneDe(source, debut) + i, m[1]),
        )
      }
    })
  }
  return trouvees
}

/** Règle 4 : le navigateur ne s'appelle que depuis core/plateforme/web*.ts et sw/. */
export function reglePlateforme(fichier, brute) {
  if (/core\/plateforme\/web[^/]*\.ts$/.test(fichier) || /(^|\/)sw\//.test(fichier)) return []
  if (!/\.(ts|vue|mjs|js)$/.test(fichier)) return []
  const source = sansCommentaires(brute)
  const trouvees = []
  source.split('\n').forEach((ligne, i) => {
    for (const motif of [PLATEFORME_OBJET, PLATEFORME_IDENT, PLATEFORME_ADRESSE]) {
      const m = motif.exec(ligne)
      if (m) trouvees.push(violation('appel de plateforme', fichier, i + 1, m[0]))
    }
  })
  return trouvees
}

/** Règle 5 : aucun rôle ; seul l'attribut ARIA role="…" d'un gabarit est permis. */
export function regleRoles(fichier, brute) {
  let source = sansCommentaires(brute)
  if (fichier.endsWith('.vue')) source = source.replace(/(\s):?role="[^"]*"/g, '$1')
  const trouvees = []
  source.split('\n').forEach((ligne, i) => {
    const m = ROLE.exec(ligne)
    if (m) trouvees.push(violation('rôle', fichier, i + 1, m[0]))
  })
  return trouvees
}

function fichiers(dossier) {
  return readdirSync(dossier, { withFileTypes: true }).flatMap((entree) => {
    const chemin = join(dossier, entree.name)
    return entree.isDirectory() ? fichiers(chemin) : [chemin]
  })
}

function principal() {
  const echecs = []
  for (const copie of COPIES) {
    const source = readFileSync(join(RACINE, 'docs/design', copie))
    const copiee = readFileSync(join(APP, 'assets/css', copie))
    if (!source.equals(copiee)) {
      echecs.push(violation('copie modifiée', `web/app/assets/css/${copie}`, 0, `diffère de docs/design/${copie}`))
    }
  }
  const tous = fichiers(APP).filter((f) => /\.(vue|ts|css|json)$/.test(f))
  const sources = tous.map((f) => [relative(RACINE, f), readFileSync(f, 'utf8')])
  const fr = JSON.parse(readFileSync(join(APP, 'core/i18n/fr.json'), 'utf8'))
  const en = JSON.parse(readFileSync(join(APP, 'core/i18n/en.json'), 'utf8'))
  const code = sources.filter(([f]) => /\.(vue|ts)$/.test(f))
  echecs.push(...regleCles(fr, en, code))
  for (const [fichier, source] of sources) {
    const estDictionnaire = /core\/i18n\/(fr|en)\.json$/.test(fichier)
    echecs.push(...regleChaines(fichier, source))
    if (!estDictionnaire) echecs.push(...regleCouleurs(fichier, source))
    echecs.push(...reglePlateforme(fichier, source))
    if (!estDictionnaire) echecs.push(...regleRoles(fichier, source))
  }
  if (echecs.length > 0) {
    for (const e of echecs) {
      console.error(`PORTE P-06 ÉCHOUÉE : ${e.regle} ${e.fichier}:${e.ligne} « ${e.detail} »`)
    }
    process.exit(1)
  }
  console.log(`PORTE P-06 : ${sources.length} fichiers, ${Object.keys(fr).length} clés, 0 littérale`)
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) principal()
