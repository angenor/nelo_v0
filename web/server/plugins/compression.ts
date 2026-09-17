// Les pages rendues par le serveur partent compressées, comme les fichiers statiques
// (nitro.compressPublicAssets). Sans cela, le HTML pèserait plusieurs fois ce que le réseau
// transporte derrière n'importe quel mandataire, et P-10 mesurerait autre chose que la réalité.
import { brotliCompressSync, constants, gzipSync } from 'node:zlib'

export default defineNitroPlugin((nitro) => {
  nitro.hooks.hook('render:response', (reponse, { event }) => {
    // Seules les pages rendues avec succès : une page d'erreur est recopiée par le gestionnaire
    // d'erreur, qui garderait l'en-tête et perdrait la compression.
    if (typeof reponse.body !== 'string' || (reponse.statusCode ?? 200) !== 200) return
    if (!reponse.headers?.['content-type']?.startsWith('text/html') || event.path.startsWith('/__nuxt_error')) return
    const acceptees = getRequestHeader(event, 'accept-encoding') ?? ''
    const corps = Buffer.from(reponse.body)
    let compresse: Buffer | null = null
    if (/\bbr\b/.test(acceptees)) {
      compresse = brotliCompressSync(corps, { params: { [constants.BROTLI_PARAM_QUALITY]: 5 } })
      reponse.headers['content-encoding'] = 'br'
    } else if (/\bgzip\b/.test(acceptees)) {
      compresse = gzipSync(corps)
      reponse.headers['content-encoding'] = 'gzip'
    }
    reponse.headers.vary = 'accept-encoding'
    if (compresse) (reponse as { body: unknown }).body = compresse
  })
})
