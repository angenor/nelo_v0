#!/usr/bin/env bash
# Test négatif de P-10 : une image de 300 Ko, incompressible, dans le gabarit de l'accueil.
set -euo pipefail
node -e '
  const { deflateSync } = require("node:zlib")
  const { randomBytes } = require("node:crypto")
  const cote = 320
  const brut = Buffer.alloc((cote * 3 + 1) * cote)
  for (let y = 0; y < cote; y++) randomBytes(cote * 3).copy(brut, y * (cote * 3 + 1) + 1)
  const bloc = (type, donnees) => {
    const l = Buffer.alloc(4); l.writeUInt32BE(donnees.length)
    return Buffer.concat([l, Buffer.from(type), donnees, Buffer.alloc(4)])
  }
  const entete = Buffer.alloc(13); entete.writeUInt32BE(cote, 0); entete.writeUInt32BE(cote, 4); entete.set([8, 2, 0, 0, 0], 8)
  const png = Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), bloc("IHDR", entete), bloc("IDAT", deflateSync(brut)), bloc("IEND", Buffer.alloc(0))])
  require("node:fs").writeFileSync("web/public/lourde.png", png)
'
[ "$(wc -c < web/public/lourde.png)" -ge 300000 ]
sed -i.bak 's|<div class="blocs">|<img src="/lourde.png" alt="" width="1" height="1"><div class="blocs">|' web/app/pages/index.vue
rm -f web/app/pages/index.vue.bak
grep -q 'lourde.png' web/app/pages/index.vue
