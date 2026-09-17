# Les quatorze composants canoniques

*Ce que chaque composant porte, dans quels états, sous quelle forme, avec quelle voix et quels
mots. Écrit avec le code de T0b, jamais après. La planche 13 (`ecrans/13_systeme-de-design.html`)
et l'artboard US1 (`canvas/US1.dc.html`) les dessinent ; ce document dit ce qui fait foi quand ils
divergent.*

## Comment lire ce document

- **Fichier** : le composant, dans `web/app/components/canon/`, importé sous le préfixe `Canon`
  (`<CanonBouton>`).
- **Énumérations** : le tableau de chaque composant est lu par un test
  (`web/tests/unit/composants-etats.test.ts`). Ses valeurs sont exactement celles de
  `web/app/core/composants/etats.ts`, que le composant réexporte et que la page de style itère.
  Changer un état, c'est changer les trois ensemble.
- **Voix** : la couleur qui parle. Il y en a quatre, et chacune a un sens
  ([05-design.md § 1](../05-design.md)) :

| Voix | Jetons | Ce qu'elle dit |
|---|---|---|
| Réussite | `--success`, `--success-soft` | L'enregistré, le soldé, le justifié, le validé |
| Ocre | `--accent`, `--accent-soft` | L'attente et l'échéance, jamais l'erreur |
| Rouge | `--danger`, `--danger-soft` | L'impayé et l'absence non justifiée ; l'erreur de saisie dans un champ |
| Marque | `--primary`, `--primary-soft` | L'action principale, la sélection, l'envoi en cours ; **aucun état métier** |

- **Aucun état n'est porté par la couleur seule** : chaque état a une forme (point, coche, contour,
  icône, position) et un mot. Les porteurs d'état ont `data-forme` et un texte non vide.
- **Aucun mot n'est écrit dans un composant** : tout libellé est une clé de
  `web/app/core/i18n/{fr,en}.json`, tout mot métier un code neutre résolu par le pack.
- **Aucune couleur hors du thème**, **aucune mesure hors de `mesures.css`** : les hauteurs de cible
  (`--cible-*`), les rayons (`--rayon-*`), le filet et la pulsation en viennent.
- **Aucun composant ne touche le navigateur** : le réseau, le stockage et l'apparence passent par
  `usePlateforme()`.

## Le contexte tactile

L'écran déclare son contexte par `provide('contexte-tactile', …)` ; les composants interactifs
lisent `--cible` pour leur hauteur minimale.

| Contexte | `--cible` | Où |
|---|---|---|
| `classe` | `--cible-classe` (52 px) | L'appel, la saisie debout |
| `standard` | `--cible-standard` (48 px) | Le portail, la tablette ; la valeur par défaut |
| `poste` | `--controle-poste` (36 px dessinés) | Le secrétariat ; la zone interactive garde `--cible-plancher` (44 px) par un pseudo-élément |

Rien, nulle part, ne descend sous 44 px de zone interactive.

---

## Les composants

### 1. Bouton

Fichier : `Bouton.vue`

| Énumération | Valeurs |
|---|---|
| `VARIANTES` | `principal`, `secondaire`, `discret`, `danger` |
| `ETATS` | `repos`, `focus`, `presse`, `inactif` |

- **Principal** : fond marque, encre `--primary-ink`. **Un seul par écran.**
- **Secondaire** : surface, filet `--border-strong`. **Discret** : sans fond ni filet, texte atténué.
- **Danger** : fond `--danger`. Réservé à une action destructrice (supprimer une inscription) ; ce
  n'est pas un état métier, c'est une action.
- **Focus** : filet marque et halo `--primary-soft` de 3 px, visible au clavier.
- **Pressé** : la teinte de survol de la variante (`--primary-hover` pour le principal).
- **Inactif** : fond `--surface-sunken`, texte atténué, **et sa raison dite sous le bouton**, avec
  son versant positif (« Sélectionnez au moins un élève pour enregistrer »). Un bouton inactif sans
  raison n'existe pas. Une action **non autorisée**, elle, n'est pas un bouton inactif : elle est
  absente.
- Le survol ne révèle rien : il assombrit, il n'ajoute aucun élément.

Mots : le libellé et la raison sont des clés.

### 2. Champ

Fichier : `Champ.vue`

| Énumération | Valeurs |
|---|---|
| `TYPES` | `texte`, `nombre`, `choix`, `case` |
| `ETATS` | `repos`, `focus`, `erreur`, `inactif` |
| `COMPLEMENTS` | `aide`, `unite` |

- L'étiquette est **toujours visible, au-dessus** du champ ; jamais un texte indicatif à la place.
- **Nombre** : clavier numérique (`inputmode`), chiffres en IBM Plex Mono tabulaire.
- **Choix** : une liste native, chevron dessiné. **Case** : case de 16 px dessinée, zone
  interactive à la hauteur de cible.
- **Erreur** : filet et message **en voix rouge**, avec une icône ; le message dit la règle et ce
  qu'il faut faire. Voir l'écart 3 plus bas.
- **Inactif** : fond `--surface-sunken`, valeur lisible, non modifiable.
- **Aide** : une ligne atténuée sous le champ. **Unité** : écrite à droite, dans le champ
  (« / 20 », « F » du pack).

### 3. Interrupteur

Fichier : `Interrupteur.vue`

| Énumération | Valeurs |
|---|---|
| `ETATS` | `active`, `desactive`, `inactif` |

Un état binaire **immédiat**, jamais un formulaire à valider. Rôle ARIA `switch`. La **position**
du bouton et le **mot** (« Activé », « Désactivé ») portent l'état ; la couleur marque l'activé.
Inactif : sa raison est dite, comme pour le bouton.

### 4. Pastille d'état

Fichier : `PastilleEtat.vue`

| Énumération | Valeurs |
|---|---|
| `VOIX` | `reussite`, `ocre`, `rouge`, `neutre`, `contour` |
| `FORMES` | `rond`, `capsule` |

- La pastille reçoit un **code d'état métier**, jamais une voix : la voix et le mot se déduisent du
  registre `ETATS_METIER`. **Seuls `IMPAYE` et `NON_JUSTIFIE` parlent en rouge** ; un appelant ne
  peut pas fabriquer un rouge.
- **Capsule** : fond doux de la voix, point de 6 px, mot. **Rond** : le point et le mot, sans fond.
- **Contour** : filet pointillé ocre et point ouvert, pour « Proposé, non validé » : rien n'est
  encore inscrit au registre.
- **Neutre** : « Présent », « Brouillon » ; fond `--surface-sunken`, texte atténué.
- Le code `IMPAYE` s'affiche **« En retard »** : « impayé » est un mot que le lexique refuse
  ([lexique.md § 1](lexique.md)).
- Hauteur `--pastille` (24 px) : une pastille accompagne, elle ne commande pas.

| Code | Voix | Mot (clé) |
|---|---|---|
| `PAYE`, `SOLDE`, `JUSTIFIE`, `ENREGISTRE`, `VALIDE` | réussite | `etat.paye`, `etat.solde`, `etat.justifie`, `etat.enregistre`, `etat.valide` |
| `ECHEANCE_PROCHE`, `EN_ATTENTE`, `NON_FAIT` | ocre | `etat.echeance_proche`, `etat.en_attente`, `etat.non_fait` |
| `IMPAYE`, `NON_JUSTIFIE` | rouge | `etat.impaye`, `etat.non_justifie` |
| `PRESENT`, `BROUILLON` | neutre | `etat.present`, `etat.brouillon` |
| `PROPOSE` | contour | `etat.propose` |

### 5. Pastille de canal

Fichier : `PastilleCanal.vue`

| Énumération | Valeurs |
|---|---|
| `CANAUX` | `EN_LIGNE`, `WHATSAPP`, `SMS`, `PAPIER` |
| `COUTS` | `sans_cout`, `avec_cout` |

Mot en capitales IBM Plex Mono, filet `--border-strong`. **Le SMS est mis en avant** (filet et fond
de marque) : c'est un canal de premier rang (constitution XIII). **Son coût est écrit à côté de
l'action qui l'engage**, mis en forme par le pack (`12 F par envoi`). Le canal se dit « En ligne »,
jamais « Web » (écart 2).

### 6. Recherche

Fichier : `Recherche.vue`

| Énumération | Valeurs |
|---|---|
| `ETATS` | `repos`, `focus`, `saisie`, `resultats`, `aucun` |
| `CONTEXTES` | `mobile`, `poste` |

Bornée au périmètre, et la **portée est écrite dans le champ** (« dans CM2 A »). Le raccourci
(« Ctrl K ») n'est affiché qu'en contexte `poste`. Les résultats montrent avatar, nom et matricule.
**Aucun résultat** : le message dit ce qui a été cherché, où, et propose d'élargir (versant positif).

### 7. Avatar

Fichier : `Avatar.vue`

| Énumération | Valeurs |
|---|---|
| `TAILLES` | `petite`, `grande` |
| `SOURCES` | `initiales`, `photo` |

36 px (grande) ou 28 px (petite). Initiales en Archivo 600 sur `--primary-soft`, ou photo. **Jamais
une couleur seule** : sous une photo absente, les initiales sont toujours rendues. Le nom complet est
dans `aria-label`.

### 8. Fil d'Ariane

Fichier : `FilAriane.vue`

| Énumération | Valeurs |
|---|---|
| `SEGMENTS` | `lien`, `courant` |

La position dans une hiérarchie profonde : cycle, niveau, classe, élève. Les segments sont des
liens ; le dernier est la position courante, **non cliquable**, en couleur de texte, avec
`aria-current="page"`. Le séparateur est une barre oblique atténuée.

### 9. Onglets

Fichier : `Onglets.vue`

| Énumération | Valeurs |
|---|---|
| `ETATS` | `actif`, `inactif`, `avec_compte` |

Les vues d'une même fiche, **pas une navigation**. Rôle `tablist`, flèches du clavier. Actif :
texte plein et trait de marque de 2 px dessous ; inactif : atténué ; avec compte : le chiffre en
IBM Plex Mono.

### 10. Carte d'indicateur

Fichier : `CarteIndicateur.vue`

| Énumération | Valeurs |
|---|---|
| `SENS` | `positive`, `negative`, `neutre` |
| `VALEURS` | `ordinaire`, `reservee` |

Un chiffre clé en Archivo 600 tabulaire, son libellé, sa variation. **Chaque sens a sa flèche et
son mot** (« + 2 sur hier », « stable depuis la rentrée »), jamais la couleur seule. La variation
positive parle en réussite, la négative en texte atténué : une baisse n'est pas une faute.
**Valeur réservée** : le chiffre en rouge, seulement pour un impayé.

### 11. Alerte

Fichier : `Alerte.vue`

| Énumération | Valeurs |
|---|---|
| `NIVEAUX` | `information`, `attente`, `danger`, `enregistre` |
| `ACTIONS` | `sans_action`, `avec_action` |

Un bloc, **un seul niveau**, une icône par niveau, un titre, un corps facultatif, une action
facultative (un lien).

| Niveau | Voix | Icône |
|---|---|---|
| `information` | neutre, filet `--border` | i dans un cercle |
| `attente` | ocre | point d'exclamation dans un cercle |
| `danger` | rouge, **réservé** à l'impayé et à l'absence non justifiée | triangle |
| `enregistre` | réussite | coche |

Une alerte du contexte (`alertes[]`) se rend ainsi : gravité `INFO` en information, `ALERTE` en
attente, `CRITIQUE` en danger **seulement** si son type est un impayé ou une absence non
justifiée, en attente sinon ; un type inconnu en information.

### 12. Ligne de tableau

Fichier : `Tableau.vue`

| Énumération | Valeurs |
|---|---|
| `MODES` | `lignes`, `cartes` |
| `CELLULES` | `texte`, `mono`, `pastille`, `canal` |

`Tableau.vue` porte l'en-tête et le passage en cartes ; `LigneTableau.vue` une ligne. En-tête sur
`--surface-sunken`, texte 13 px atténué. Colonnes `mono` en IBM Plex Mono tabulaire (matricule,
classe, montant, alignés à droite pour un montant). Une cellule peut porter une pastille d'état ou
de canal. **Sous `--rupture-deux-colonnes` (768 px), chaque ligne devient une carte**, avec le
libellé de colonne au-dessus de la valeur ; c'est le même balisage, du CSS seul.

### 13. Ruban d'état de saisie

Fichier : `RubanSaisie.vue`

| Énumération | Valeurs |
|---|---|
| `ETATS` | `enregistre`, `envoi`, `hors_ligne` |
| `VOIX` | `reussite`, `marque`, `ocre` |

Ancré en bas de l'écran de saisie, au-dessus de l'action principale ; il ne défile pas, il ne
recouvre rien. **Trois choses et rien d'autre** : l'heure du dernier enregistrement, le nombre de
saisies en attente, la qualité du lien. **Il ne bloque jamais la saisie.**

| État | Condition | Voix | Forme | Mots |
|---|---|---|---|---|
| `enregistre` | rien en attente, lien présent | réussite | coche | « Tout est enregistré », « Aucune saisie en attente » |
| `envoi` | des saisies en attente, lien présent | marque | point qui pulse | « Envoi de 2 saisies », « Vous pouvez continuer à saisir » |
| `hors_ligne` | aucun lien | ocre | lien barré | « Hors ligne », « 4 saisies conservées, envoi à la reconnexion », « Continuez, rien ne sera perdu » |

- **Jamais rouge** : une coupure n'est pas une faute. Le type l'interdit.
- La qualité du lien s'écrit avec trois barres et un mot : « Lien bon », « Lien faible »,
  « Pas de lien ».
- Avant tout enregistrement : « Aucun enregistrement pour l'instant », jamais « 00:00 ». Le compte
  s'affiche exact, jamais « 99+ ».
- Sous « réduire les animations », le point ne pulse plus ; la forme et le mot restent.
- L'état est **dérivé** (`core/saisie/etat-ruban.ts`), jamais posé par l'écran.

### 14. Coquille d'application

Fichier : `Coquille.vue`

| Énumération | Valeurs |
|---|---|
| `SITUATIONS` | `AUCUNE_CAPACITE`, `MONO_DOMAINE`, `MULTI_PLAT`, `MULTI_FAMILLES` |

Elle **se compose depuis le contexte, jamais depuis un rôle** (`composer(contexte)`,
[ADR 015](../adr/015-l-interface-se-compose-a-partir-des-capacites.md)). Sous-composants :
`CoquilleEntete.vue`, `CoquilleNavigation.vue`, `CoquilleSansCapacite.vue`.

- **En-tête** : établissement et site, année de travail, sélecteur de langue, sélecteur de thème,
  lien « à propos », avatar. Ni cloche ni déconnexion : la session arrive avec T1a, les alertes
  passent par le composant alerte.
- **Navigation** : les domaines dont la personne détient au moins une capacité, **et eux seuls**.
  **À plat jusqu'à cinq domaines inclus ; regroupée par famille dès six** : le domaine
  ([02-domaine.md § 3.4](../02-domaine.md)) l'emporte sur la planche, qui écrivait « en dessous de
  quatre ». Une famille est une étiquette de lecture, jamais une page ; une famille vide
  n'apparaît pas. **Aucune entrée grisée, jamais** : le modèle n'a pas de champ « désactivé ».
- **Sous 768 px**, la navigation est une barre basse jusqu'à cinq domaines ; au-delà, la même
  liste s'ouvre en tiroir depuis un bouton menu. Au-dessus, une barre latérale de 208 px.
- **Un domaine** : l'accueil **est** ce domaine. **Plusieurs** : un tableau composé, un bloc par
  domaine dans l'ordre du registre.
- **Aucune capacité** : ni navigation, ni page vide, ni erreur technique ; un message qui **nomme
  l'administrateur** de l'établissement, donne son téléphone et propose « Demander mes accès ».

---

## Les trois écarts de la revue visuelle, tranchés

La revue visuelle de T0b a relevé trois écarts entre la planche 13 et la spécification. Ils sont
tranchés ici, par dérivation du corpus ([research.md R-19](../../specs/002-socle-interface/research.md)).

1. **« Validé » prend la voix de réussite**, pas le vert profond. [05-design.md § 1.1](../05-design.md)
   dit que le vert profond ne porte aucun état et que la réussite porte l'enregistré, le soldé, le
   justifié ; validé en fait partie. La planche 13 s'écartait de sa propre règle ; l'artboard US1
   l'avait rendu en neutre en attendant.
2. **Le canal se dit « En ligne »**, comme [05-design.md § 5](../05-design.md) et
   [ADR 002](../adr/002-web-d-abord-capacitor-plus-tard.md). « Web » entre au lexique dans la
   colonne « on ne dit jamais ».
3. **Un champ en erreur parle en rouge**, avec une icône et un message qui dit quoi faire. La règle
   « le rouge est réservé à l'impayé et à l'absence non justifiée » vise les **états métier**
   (pastilles, alertes de situation) ; une erreur de saisie n'est pas un état métier, et l'ocre lui
   est interdit ([05-design.md § 1.3](../05-design.md) : l'ocre n'est pas un rouge atténué).

Un quatrième point, qui n'était pas un écart mais un seuil : **cinq domaines restent à plat, six se
regroupent**.
