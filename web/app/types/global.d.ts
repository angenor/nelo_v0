// Les constantes posées par l'empaqueteur (nuxt.config.ts, vite.define).
//
// `__NELO_DEMONSTRATION__` dit si la construction porte les personas de démonstration
// (research.md R-10). En production elle vaut `false` : la branche qui les charge est morte et
// l'empaqueteur l'élague, le code de démonstration ne voyage pas.

declare global {
  const __NELO_DEMONSTRATION__: boolean
}

export {}
