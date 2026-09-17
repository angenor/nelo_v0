// Le lecteur typé de web/ecrans.json, le seul endroit qui déclare les écrans et leurs budgets
// (data-model.md § 5). P-05 ouvre chaque entrée, P-10 mesure chaque budget non nul. La lecture
// du fichier appartient à l'appelant (Vitest, Playwright) : ce module ne fait que valider.

export interface Ecran {
  nom: string
  route: string
  budgetKo: number | null
  budgetPolicesKo?: number | null
  personas?: string[]
  developpement?: boolean
}

function entierPositifOuNull(valeur: unknown): boolean {
  return valeur === null || (Number.isInteger(valeur) && (valeur as number) > 0)
}

export function valider(entrees: unknown): Ecran[] {
  if (!Array.isArray(entrees) || entrees.length === 0) {
    throw new Error('ecrans.json : la liste des écrans est vide')
  }
  const noms = new Set<string>()
  for (const e of entrees as Ecran[]) {
    if (!e.nom || !e.route?.startsWith('/')) {
      throw new Error(`ecrans.json : entrée sans nom ou sans route (${JSON.stringify(e)})`)
    }
    if (noms.has(e.nom)) throw new Error(`ecrans.json : écran « ${e.nom} » déclaré deux fois`)
    noms.add(e.nom)
    if (!entierPositifOuNull(e.budgetKo)) {
      throw new Error(`ecrans.json : « ${e.nom} », budgetKo doit être un entier positif ou null`)
    }
    if (e.budgetPolicesKo !== undefined && !entierPositifOuNull(e.budgetPolicesKo)) {
      throw new Error(`ecrans.json : « ${e.nom} », budgetPolicesKo doit être un entier positif ou null`)
    }
    if (e.developpement && e.budgetKo !== null) {
      throw new Error(`ecrans.json : « ${e.nom} » est de développement, son budgetKo doit être null`)
    }
  }
  return entrees as Ecran[]
}

/** Le contenu de web/ecrans.json, validé. */
export function lireEcrans(texte: string): Ecran[] {
  return valider((JSON.parse(texte) as { ecrans: unknown }).ecrans)
}
