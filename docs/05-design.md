# 05 — Design

*Direction « Registre » : la référence est le registre relié et le reçu numéroté.*
*Rigueur, densité, aucune décoration. Chaque écran dit ce qui est enregistré.*

---

## 0. Les sources, dans l'ordre

| Rang | Fichier | Statut |
|---|---|---|
| 1 | **`design/theme.css`** | **La seule source des valeurs de couleur.** Thèmes clair et sombre, base typographique |
| 2 | **`design/mesures.css`** | **La seule source des mesures non colorées** : hauteurs de cible, rayons, filet, points de rupture, pulsation. Copié tel quel dans l'application, comme `theme.css` ; les valeurs sont celles de la [§ 3](#3-espacement-hauteurs-rayons-ombres) et de la planche, rien n'y est inventé |
| 3 | `design/tokens.json` | Les mêmes valeurs que `theme.css`, en JSON, pour l'outillage |
| 4 | `design/ecrans/index.html` | Le sommaire — **à ouvrir en premier** |
| 5 | `design/ecrans/13_systeme-de-design.html` | Jetons et composants, tous états |
| 6 | `design/ecrans/*.html` | Douze écrans maquettés, du mobile 390 px au poste 1440 px |

**Deux règles de lecture de `theme.css`** :

1. **Les noms de jetons sont identiques en clair et en sombre.** Seules les valeurs changent sous
   `[data-theme="dark"]`. Un composant écrit avec `var(--surface)` et `var(--text)` bascule tout
   seul ; une règle spécifique au sombre ne sert **qu'à ce qu'une couleur ne peut pas porter** — une
   ombre remplacée par une bordure, une opacité, une épaisseur.
2. **Tout ce qui a un nom ici n'a jamais de valeur en dur ailleurs.** Ce document ne répète aucune
   valeur qui ne serait pas déjà dans `theme.css` : une seconde source divergerait.

> ⚠️ **Le HTML de maquette ne se copie jamais vers `web/app/`.** C'est une cible, pas une source :
> styles en ligne, pas de sémantique, pas d'i18n, pas de capacités. Seul `theme.css` voyage.

> ⚠️ **Les maquettes sont à gabarit fixe. Le produit se construit mobile-first** : on part du plus
> petit gabarit et on ajoute vers le haut. Les fichiers de référence disent **le dessin, la hiérarchie
> et le vocabulaire** — pas la disposition sur un téléphone. Celle-ci se conçoit à chaque écran, avec
> les règles de la [§ 9](#9-coder-un-écran).

### 0.1 Ce qui manque encore

Le système est arrêté sur la couleur, la typographie et les composants. Trois fichiers de Kaya n'ont
pas d'équivalent ici et se produiront quand la première tranche d'interface les exigera :

| Fichier | Ce qu'il porterait | Quand |
|---|---|---|
| `design/lexique.md` | Le vocabulaire visible, **opposable, primant sur les clés i18n** | **Avant le premier écran** — voir [§ 8](#8-la-langue) |
| `design/composants.md` | Les quatorze composants, tous états, en spécification | Avec la tranche de la coquille |
| `design/mouvement.md` | Durées, courbes, patrons d'animation | Avec la tranche de la coquille |

---

## 1. Couleur

Le thème se bascule par `<html data-theme="dark">`, et `[data-theme]` se pose **sur n'importe quel
conteneur** — c'est ce qui permet d'afficher les deux modes côte à côte dans le styleguide.

**Les valeurs sont dans `theme.css`. Elles ne sont pas répétées ici.** Ce qui est ici, c'est ce que
chaque jeton veut dire — et cette intention, elle, ne se lit pas dans un fichier CSS.

### 1.1 Les quatre voix de couleur

| Voix | Jetons | Ce qu'elle dit — et **ce qu'elle ne dit jamais** |
|---|---|---|
| **Le vert profond** | `--primary`, `--primary-hover`, `--primary-soft`, `--primary-ink` | **Il vient du tableau d'école.** C'est la marque et l'action principale. Il ne porte aucun état |
| **L'ocre** | `--accent`, `--accent-soft`, `--accent-ink` | **L'attente et l'échéance.** Un dossier incomplet, une échéance qui approche, une saisie en cours d'envoi. **Jamais l'erreur** |
| **Le rouge** | `--danger`, `--danger-soft`, `--danger-ink` | **Réservé à l'impayé et à l'absence non justifiée.** C'est tout. Un rouge banalisé ne se voit plus le jour où il compte |
| **Le vert de réussite** | `--success`, `--success-soft` | L'enregistré, le soldé, le justifié |

### 1.2 Surfaces et filets

`--board` porte le plan de travail, `--bg` le fond de page, `--surface` la feuille posée dessus,
`--surface-sunken` le creux — en-tête de tableau, piste de segment, squelette de chargement.
`--border` sépare, `--border-strong` appuie et borde un champ au repos.

### 1.3 Les trois règles de couleur

1. **Un état n'est jamais porté par la couleur seule.** Il porte aussi une forme : une pastille, une
   icône, un mot. Sur un écran délavé par le soleil ou lu par une personne daltonienne, la couleur
   disparaît la première.
2. **L'ocre n'est pas un rouge atténué.** Attendre et échouer sont deux choses différentes, et les
   confondre rend l'écran illisible : un dossier incomplet n'est pas une faute.
3. **Aucune valeur littérale hors de `theme.css`.** Ni dans un composant, ni dans un écran, ni dans ce
   document.

---

## 2. Typographie

**Trois familles, trois emplois disjoints.** Les valeurs exactes sont dans `theme.css` et dans
`13_systeme-de-design.html` ; ce qui suit dit **quand** employer quoi.

| Famille | Emploi | Ce qu'elle ne fait jamais |
|---|---|---|
| **Archivo** | Titres et **chiffres clés** | Du texte courant |
| **Public Sans** | Tout le reste : texte, interface, étiquettes, mentions | Un chiffre qu'on compare colonne à colonne |
| **IBM Plex Mono** | **Matricule, reçu, montant, identifiant de transaction, code de classe** | Tout le reste. *Nulle part ailleurs* |

### 2.1 L'échelle

| Rôle | Composition |
|---|---|
| Titre de page | Archivo 700 · 34 px · −0.02em · interligne 1.15 |
| Titre de section | Archivo 600 · 26 px · −0.02em |
| **Chiffre clé** | Archivo 600 · 34 px · **`font-variant-numeric: tabular-nums`** |
| Sous-titre | Archivo 600 · 20 px · −0.02em |
| Texte courant | Public Sans 400 · 16 px |
| Interface | Public Sans 500 · 14 px |
| Étiquette et méta | Public Sans 500/600 · 13 px |
| Mention | Public Sans 400 · 12 px |
| **Données** | IBM Plex Mono 500 · 12–14 px · **tabulaire** |

### 2.2 Les chiffres qui s'empilent sont tabulaires — sans exception

Un solde, une moyenne, un effectif, un montant, un rang : **`font-variant-numeric: tabular-nums`**.
Une colonne de montants dont les chiffres n'ont pas la même largeur ne se lit pas, elle se déchiffre.

**Les montants portent l'espace fine insécable** comme séparateur de milliers, et le symbole de la
devise du country pack. `145 000 F`, jamais `145000F`.

**Une note s'écrit avec sa virgule décimale et son barème** : `14,25 / 20`. Jamais `14.25`, jamais
`14,25` seul — un nombre sans son barème est faux dès qu'un pack passe au pourcentage.

---

## 3. Espacement, hauteurs, rayons, ombres

### 3.1 Hauteurs canoniques

| Contexte | Hauteur | Pourquoi |
|---|---|---|
| **Cible tactile en classe** | **52 px** | L'appel se fait debout, en marchant entre les rangs, parfois avec une craie dans l'autre main |
| Cible tactile standard | 48 px | Le portail parent, la saisie sur tablette |
| **Plancher absolu** | **44 px** | Jamais moins, nulle part, sur aucun gabarit |
| Contrôle sur poste | 36 px **dessinés**, zone interactive de 44 px | Souris et clavier, densité de tableau. Le plancher vaut aussi ici : le contrôle se dessine bas, sa zone interactive ne descend jamais sous 44 px |
| Pastille d'état | 22–24 px | Elle accompagne, elle ne commande pas |

> **Le 52 px n'est pas un confort.** Un appel raté parce que la case voisine a été cochée coûte un SMS
> envoyé à tort à une famille, et une confiance qui ne revient pas.

### 3.2 Rayons

| Rayon | Emploi |
|---|---|
| **8 px** | Cartes, panneaux, blocs |
| **6 px** | Champs, boutons, tuiles |
| **999 px** | Pastilles d'état et de canal — **et rien d'autre** |
| 4 px | Micro-éléments seulement |

### 3.3 Bordures et ombres

**Bordures de 1 px. Aucune ombre, hors popover et modale.** C'est le trait du registre : une feuille
posée se distingue par son filet, pas par sa lévitation.

En sombre, la séparation passe par `--border` et par le contraste des surfaces — **jamais par une
ombre plus marquée**, qui ne se voit pas sur fond noir.

---

## 4. Les moments qui comptent

Cinq moments décident de l'adoption. Ils se conçoivent avant les autres.

| Moment | Ce qui doit être vrai |
|---|---|
| **L'appel de séance** | Un geste par élève, aucune navigation. Enregistrement au fil de l'eau. **L'écran le plus léger du produit** |
| **La saisie de notes** | Même contrat, sur tablette. Le clavier numérique s'ouvre seul, la tabulation descend la colonne |
| **La perte de réseau** | Le ruban dit ce qui est enregistré et ce qui attend. **La saisie ne se bloque jamais** |
| **Le retour du réseau** | Ce qui attendait part, le ruban repasse au vert, **et l'utilisateur n'a rien à faire** |
| **L'absence de capacité** | Un message qui nomme l'administrateur de l'établissement. **Jamais une page vide, jamais une erreur technique** |

---

## 5. Les quatorze composants canoniques

Tous sont maquettés dans `13_systeme-de-design.html`, en clair et en sombre.

| # | Composant | Ce qu'il porte |
|---|---|---|
| 1 | **Bouton** | Principal, secondaire, discret, danger. Un seul principal par écran |
| 2 | **Champ** | Repos, focus, erreur, désactivé, avec aide et avec unité |
| 3 | **Interrupteur** | Un état binaire immédiat, jamais un formulaire à valider |
| 4 | **Pastille d'état** | Rond ou capsule, **toujours avec son mot** |
| 5 | **Pastille de canal** | SMS, WhatsApp, en ligne, papier — le canal se lit d'un coup d'œil |
| 6 | **Recherche** | Bornée au périmètre, avec son indication de portée |
| 7 | **Avatar** | Photo ou initiales, jamais une couleur seule |
| 8 | **Fil d'Ariane** | La position dans une hiérarchie profonde : cycle → niveau → classe → élève |
| 9 | **Onglets** | Les vues d'une même fiche, pas une navigation |
| 10 | **Carte d'indicateur** | Un chiffre clé, son libellé, sa variation. Archivo tabulaire |
| 11 | **Alerte** | Information, attente (ocre), danger (rouge), enregistré (voix de réussite). **Jamais deux niveaux dans le même bloc** |
| 12 | **Ligne de tableau** | Élève, matricule, classe, reste à payer, état, dernier contact |
| 13 | **Ruban d'état de saisie** | Voir [§ 5.1](#51-le-ruban-détat-de-saisie) |
| 14 | **Shell d'application** | Voir [§ 5.2](#52-le-shell-se-compose-il-ne-se-choisit-pas) |

**Un composant manquant arrête un cycle.** On ne dessine pas un composant dans une tranche métier : on
l'ajoute au système, on le maquette dans ses états, puis on l'assemble. Sinon le système devient une
collection de cas particuliers.

### 5.1 Le ruban d'état de saisie

**Ancré en bas de chaque écran de saisie.** Il dit trois choses, et rien d'autre :

1. **l'heure du dernier enregistrement** — « Dernier enregistrement à 10:42 » ;
2. **le nombre de saisies en attente** — « Aucune saisie en attente », ou le compte exact ;
3. **la qualité du lien** — « Lien bon », « Envoi en cours », « Hors ligne ».

**Il ne bloque jamais la saisie. Il informe.** C'est la contrepartie visible de
[ADR 001](adr/001-hors-connexion-differe.md) : sans mode hors connexion, la confiance ne peut venir
que de l'explicite. *L'ambiguïté sur ce point est exactement là où se perd la confiance.*

> **Trois états, trois formes, trois mots.** Le vert seul ne suffit pas : un enseignant qui regarde
> son téléphone en plein soleil doit lire le mot.

### 5.2 Le shell se compose, il ne se choisit pas

Il n'existe pas de « shell du censeur ». Le shell se construit à partir de
`GET /moi/capacites` ([ADR 015](adr/015-l-interface-se-compose-a-partir-des-capacites.md)) :

| Situation | Ce que rend le shell |
|---|---|
| **Un seul domaine** | L'utilisateur atterrit **dans son domaine**, pas sur un tableau de bord presque vide |
| **Deux ou trois domaines** | Ils s'affichent à plat |
| **Au-delà de cinq** | Regroupement par famille. La navigation d'un directeur qui détient tout ne peut pas être la même liste que celle d'un enseignant qui détient une chose |
| **Aucune capacité** | Un message qui nomme l'administrateur de l'établissement et dit quoi faire |

**Pas de menu grisé, jamais.** Un menu visible mais inaccessible est du bruit et une invitation à
réclamer des droits.

---

## 6. Les écrans maquettés

Douze écrans, plus la planche du système. Ils sont dans `design/ecrans/`, sommaire dans `index.html`.

| Code | Fichier | Gabarit |
|---|---|---|
| **A1** | `01_connexion-mobile.html` | Mobile 390 px — parcours de connexion |
| **P1** | `02_appel-de-seance-mobile.html` | Mobile 390 px — **l'écran qui décide de l'adoption** |
| **F1** | `03_espace-parent-mobile.html` | Mobile 390 px **+ les variantes SMS** |
| **N1** | `04_saisie-des-notes-tablette.html` | Tablette 1024 px |
| **E1** | `05_fiche-eleve-trois-vues.html` | **La fiche unique, vue par trois rôles** |
| **S1** | `06_navigation-composee.html` | Le shell avec quatre rattachements |
| **F2** | `07_fiche-foyer-econome.html` | Poste 1440 px |
| **C1** | `08_conseil-de-classe-poste.html` | Poste 1440 px |
| **M1** | `09_console-de-communication-poste.html` | Poste 1440 px — routage et budget SMS |
| **P2** | `10_registre-protection-enfance-poste.html` | Poste 1440 px — **cloisonné** |
| **H1** | `11_roles-et-rattachements-poste.html` | Poste 1440 px |
| **D1** | `12_tableau-de-bord-direction-poste.html` | Poste 1440 px |
| **—** | `13_systeme-de-design.html` | Jetons et composants |

> **`05_fiche-eleve-trois-vues.html` est le fichier le plus important du lot.** Il montre la règle
> centrale du produit : **une fiche élève, plusieurs vues** — l'éducateur y voit la discipline,
> l'économe le solde, l'enseignant les notes de ses seules matières. Jamais quatre écrans concurrents.

> ⚠️ **Les treize maquettes portent des données de secondaire** — « 6ᵉ A », professeurs de matière,
> conseil de classe. Elles ont été dessinées avant que le MVP ne bascule sur le primaire
> ([ADR 018](adr/018-le-mvp-commence-par-le-primaire.md)). **Le système de design ne change pas** : ce
> sont des jeux de données fictifs, et ils se reprennent **écran par écran à la revue visuelle qui
> suit chaque `specify`**, jamais en une passe globale qui les toucherait tous sans besoin. Un
> artboard dessiné à partir d'une maquette non reprise **remplace ses données par du primaire** — CM2,
> maître titulaire, conseil des maîtres.

---

## 7. Le mode dégradé se dessine

Ce n'est pas une page d'erreur : ce sont des états de premier rang, maquettés comme les autres.

| État | Ce qu'il montre |
|---|---|
| **Lien lent** | Le ruban en ocre, la saisie continue, rien ne clignote |
| **Lien perdu** | Le ruban le dit, le compte de saisies en attente monte, **la saisie continue** |
| **Retour du lien** | Les envois partent, le compte descend, le ruban repasse au vert. Aucune action de l'utilisateur |
| **Liste imprimable** | Sur chaque écran critique — appel, fiches d'urgence, personnes autorisées. **Un bouton, pas un menu enfoui** |

---

## 8. La langue

**Le produit, le code, les commentaires et la documentation sont en français.** Les accents sont
obligatoires partout.

**Et les clés `fr` et `en` naissent ensemble** : le bilinguisme est dans le socle, pas dans une phase
ultérieure — [ADR 014](adr/014-la-localisation-passe-par-le-country-pack.md). Une clé écrite en `fr`
seul est une dette qui se découvre au moment du premier client anglophone, c'est-à-dire trop tard.

### 8.1 Le vocabulaire visible vient du country pack

**Aucun libellé métier n'est une littérale.** « Classe », « trimestre », « bulletin », « professeur
principal » sont des **codes** dont le mot affiché vient du pack. Le même écran dit *Classe* en Côte
d'Ivoire et *Form* au Ghana, sans une ligne de code différente — et *conseil des maîtres* au primaire
là où il dira *conseil de classe* au secondaire.

Ce qui suit est le vocabulaire **canonique en français**, celui que `lexique.md` figera :

| On dit | On ne dit jamais |
|---|---|
| Élève | Apprenant, étudiant *(sauf dans le supérieur, où le pack le dit)* |
| Responsable légal | Parent — sauf quand le lien est effectivement `PERE` ou `MERE` |
| Appel | Pointage, feuille de présence |
| Absence non justifiée | Absence illégale, absence sauvage |
| Bulletin | Relevé de notes |
| Reste à payer | Impayé, dette, arriéré *(l'arriéré existe, mais c'est la créance sur l'État)* |
| Échéance | Deadline, date limite |
| Enregistré | Sauvegardé, synchronisé |
| Signalement | Alerte, dénonciation |
| Établissement | École — le MVP sert des écoles primaires, le produit servira aussi des lycées et des groupes scolaires |

### 8.2 Les règles de rédaction

1. **Le refus s'annonce avant la saisie, et il dit son versant positif.** Pas « vous ne pouvez pas
   valider cette inscription », mais « il manque le certificat de naissance et la photo — vous pouvez
   valider dès qu'ils sont déposés, ou demander une dérogation ».
2. **Un message dit un fait, pas un jugement.** « 7 absences en 3 semaines » — jamais « élève à
   risque ». C'est une règle de langue et une règle d'IA
   ([ADR 011](adr/011-six-capacites-ia-pas-trente-quatre-agents.md)).
3. **Le SMS est rédigé pour le SMS.** Sous 160 caractères, sans abréviation SMS, avec le nom de
   l'établissement. *Un SMS n'est pas un push tronqué.*
4. **Aucune chaîne d'interface en dur.** Les clés `fr` et `en` naissent ensemble (porte P-06).

### 8.3 Le registre grave

Trois familles d'écrans changent de ton : **la protection de l'enfance, la santé, la discipline.**

Pas d'emoji, pas d'illustration, pas de couleur d'accent, pas de formule encourageante. Le texte est
sobre, factuel, et **nomme le circuit** : qui est le référent, quel est le délai, à qui la situation
sera transmise.

> Un signalement de maltraitance ne s'affiche pas dans la même grammaire visuelle qu'un solde de
> cantine. La sobriété n'est pas une préférence esthétique : c'est ce qui permet à la personne qui
> dépose un signalement de faire confiance à l'outil.

---

## 9. Coder un écran

### 9.1 Les quatre cas — règle opposable

| Cas | Ce qu'on fait |
|---|---|
| **L'écran est maquetté** | On suit la maquette. C'est la référence, pas une illustration |
| **L'écran n'est pas maquetté, ses composants existent** | On assemble à partir du canon. On ne dessine rien de neuf |
| **Il manque un composant** | **On arrête le cycle.** On ajoute le composant au système, dans tous ses états, puis on assemble |
| **La maquette contredit le domaine** | **Le domaine gagne, et on le dit.** Une maquette peut être incomplète ou porter une erreur de disposition ou de contenu ; c'est précisément ce que la revue visuelle sert à détecter |

> **Le dessin fait autorité. Le domaine tranche les conflits.** Une maquette n'est pas une
> illustration : c'est la référence. On la suit. Mais elle peut n'être pas exhaustive, ou contenir une
> erreur — dans ces cas-là seulement, la source de vérité tranche, **et l'écart se documente**.

### 9.2 Mobile-first — les règles de disposition

1. **On part du plus petit gabarit.** 390 px de large est la cible de conception, pas un cas dégradé.
2. **Une colonne sur mobile, toujours.** Deux colonnes commencent à 768 px, trois à 1200 px.
3. **Un tableau ne se réduit pas : il se transforme.** Sur mobile, une ligne de tableau devient une
   carte, avec le libellé au-dessus de la valeur.
4. **L'action principale est atteignable au pouce**, en bas de l'écran, sur toute la largeur si elle
   est unique.
5. **Le ruban d'état de saisie est ancré**, il ne défile pas avec le contenu.
6. **Rien n'est masqué derrière un survol.** Il n'y a pas de survol au doigt.

### 9.3 Le budget de poids est une contrainte de design

Ce n'est pas un sujet de développeur : **c'est un arbitrage de conception**, et il se fait au moment
du dessin.

| Écran | Budget |
|---|---|
| **Appel de séance** | **120 Ko** transférés, premier affichage utile < 2 s sur 3G lente |
| Saisie de notes | 200 Ko |
| Portail parent | 150 Ko par vue |
| Back-office | 500 Ko au premier chargement |

Une illustration, une police supplémentaire, une bibliothèque de graphiques : chacune se pèse contre
ce budget avant d'être dessinée, pas après (porte P-10).

### 9.4 Accessibilité

- **Contraste AA au minimum**, vérifié en clair **et** en sombre.
- **Un état n'est jamais porté par la couleur seule** : forme, icône ou mot en plus.
- **Taille de police ajustable** sans casser la disposition — les postes des établissements sont
  parfois réglés à 125 %.
- **Navigation au clavier complète** sur les écrans de poste : le secrétariat saisit vite, à la
  tabulation.
- **`prefers-reduced-motion` respecté.**

---

## 10. Impression

L'impression n'est pas une sortie de secours : c'est un canal de premier rang
([ADR 013](adr/013-le-sms-est-un-canal-de-premier-rang.md)), et le **mode dégradé assumé** de
[ADR 001](adr/001-hors-connexion-differe.md).

| Document | Règle |
|---|---|
| **Bulletin** | Gabarit du country pack. **Rendu par le serveur**, jamais par le navigateur. Porte son empreinte |
| **Liste d'appel** | Une classe par page, cases à cocher, imprimable **à l'avance** |
| **Fiches d'urgence** | Une classe par page : allergies, protocole, personne à prévenir |
| **Personnes autorisées à récupérer** | Une classe par page, avec les photos |
| **Reçu** | Numéroté séquentiel par caisse, avec le nom de l'établissement |
| **Avis de situation** | Le solde complet, remis à l'élève ou disponible à l'accueil — **il remplace un SMS** |

**Règles communes** : noir et blanc lisible, aucune couleur porteuse d'information, en-tête
d'établissement, date et heure d'édition, et **la mention du gabarit et de sa version** sur les
documents officiels.

---

## 11. Trois décisions à trancher avant le premier composant

Elles sont dans [progress.md](progress.md), section « Ce qui attend une réponse ». Elles ne se
décident pas en écrivant un composant.

| # | Question |
|---|---|
| **Q1** | **Les polices sont chargées depuis un service distant.** Elles doivent être servies localement — quelle version, quels sous-ensembles de glyphes, sous quelle licence redistribuable ? |
| **Q2** | **Le produit n'a pas de marque.** Pas de logo, pas de nom affiché, pas de favicon. « Nelo » vient du nom du dépôt : est-ce le nom du produit ? |
| **Q3** | **Le mode sombre est-il proposé au parent ?** Il est défini dans les jetons. Sur le portail parent, il double la surface de test pour un gain incertain — l'usage est court et diurne |

---

## Le prompt de revue visuelle

**Après chaque `specify` conclu**, on produit ce bloc et on le lance en session dédiée, avant `plan`.
Son but n'est pas de dessiner : c'est de **rendre une dérive visible** — une entité, un état ou un
champ absent du domaine doit sauter aux yeux.

### D'abord une question, et elle décide de tout

> **Cette tranche produit-elle un écran qu'une personne regarde ?**

| Réponse | Ce qu'on lance | Pourquoi |
|---|---|---|
| **Oui** | **`/design`** — la forme A ci-dessous | Il faut voir la facture, les états, la densité, le mode sombre. Rien d'autre ne les montre |
| **Non** — socle serveur, moteur, contrat, chaîne de vérification, migration | **Une planche de diagrammes Mermaid** — la forme B. **On ne lance pas `/design`** | Un artboard qui représente une migration ou un test **est du texte mis en page**. Le diagramme dit la même chose, il se relit dans un diff, il se versionne, et il coûte deux ordres de grandeur de moins |

> ⚠️ **Le piège, et il s'est produit.** La forme A porte un paragraphe entier de contraintes d'écran
> — cibles tactiles, clair et sombre, lexique, montants. Collée sur une tranche d'infrastructure,
> **elle noie la clause « sinon un diagramme » et produit huit artboards pour dessiner des tests.**
> On ne choisit pas la forme dans le prompt : **on la choisit avant de l'écrire.**

**Mermaid, et pas une image** : c'est du texte. Il se relit dans une revue, il se corrige sans
rouvrir un éditeur, et il s'affiche tel quel dans GitHub comme dans un artifact.

---

### Forme B — la tranche n'a pas d'écran

Un seul fichier, `specs/00X-nom-de-la-tranche/design/diagrammes.md`, fait de blocs ```mermaid.
**Pas de canvas, pas d'artboard, pas de `.dc.html`.**

Le gabarit — remplacer ce qui est entre crochets :

```text
Produis la planche de diagrammes de la tranche [nom], à partir de [chemin du spec.md].

Pas d'écran dans cette tranche : ne dessine aucune interface, n'ouvre ni le fichier de composants,
ni le dossier d'écrans, ni le lexique. Aucun mode sombre, aucune cible tactile, aucun jeton de
couleur — ce sont des diagrammes, pas des maquettes.

Écris UN SEUL fichier : [chemin]/design/diagrammes.md, composé de blocs mermaid séparés par un
titre de niveau 2 et une phrase qui dit ce que le diagramme rend visible.

[trois à cinq] diagrammes, pas un de plus. Pour chacun : sa grammaire, ce qu'il montre, et les
user stories qu'il couvre.
  1. [graph LR | sequenceDiagram | stateDiagram-v2 | erDiagram] — [ce qu'il montre] — couvre [US…]
  …

À lire avant, et à ne pas dépasser : [le spec.md, et les deux ou trois sections de docs/ qui font foi].

Ne rien inventer hors de ces fichiers. Le but est de rendre visible une dérive : une entité, une
étape ou un contrôle qui n'existe pas dans le corpus doit sauter aux yeux. Aucune prose hors des
phrases d'introduction.
```

**Choisir la grammaire selon ce qu'on veut voir** — et une seule par diagramme :

| Ce qu'on veut voir | Grammaire |
|---|---|
| Une frontière, une dépendance, **une arête interdite** | `graph LR`, l'arête interdite en pointillé avec la porte qui la refuse |
| Un enchaînement d'acteurs, un aller-retour | `sequenceDiagram` |
| Un cycle de vie, des transitions | `stateDiagram-v2` |
| Une structure de données et ses cardinalités | `erDiagram` |
| Une chaîne qui s'arrête au premier échec | `graph LR`, la sortie en échec explicite |

**Trois règles qui évitent le diagramme illisible** : un diagramme répond à **une** question ·
trois mots par nœud, jamais une phrase · **s'il faut une légende, le diagramme est raté**.

---

### Forme A — la tranche a des écrans

### Où les fichiers atterrissent

`/design` ne dépose rien tout seul — c'est à l'agent d'écrire les fichiers de travail, et **il faut le
lui dire dans le prompt**. Toute modification ultérieure repart de ces sources, jamais du canvas
publié : leur emplacement compte.

**Le critère de répartition tient en une question : est-ce que ça survit à la tranche ?**

| Quoi | Où | Pourquoi |
|---|---|---|
| **La planche de style** | `docs/design/canvas/` | Transverse et durable. Elle est citée comme référence de facture par **toutes** les tranches |
| **Les maquettes d'une tranche** | `specs/00X-nom/design/` | Elles naissent avec la spécification, documentent une décision de cette tranche, et personne ne les relit ensuite |

**Ce qui se versionne, et ce qui ne se versionne pas** — les sources `.dc.html` et `canvas.json` pèsent
quelques dizaines de kilo-octets et partent dans git ; **le fichier assemblé pèse environ 2 Mo dont
l'essentiel est le code de l'éditeur**, et se régénère en une commande. Le `.gitignore` porte déjà
cette règle.

Remplacer les quatre valeurs entre crochets, puis coller :

```text
/design Représente les user stories de [chemin du spec.md] pour la tranche [nom de la tranche].

Un artboard par user story, nommé par son identifiant. Si la story produit des écrans, dessine les
écrans ; sinon un diagramme adapté — machine à états pour un cycle de vie, séquence pour un
enchaînement d'acteurs, classes pour une structure de données, flux de gauche à droite pour un
parcours.

À lire avant de dessiner, et à ne pas dépasser :
- docs/02-domaine.md, sections [sections concernées] — les entités, leurs états, leurs invariants
- docs/03-api.md, sections [sections concernées] — les ressources et les codes d'erreur
- docs/design/theme.css — les jetons, seule source des couleurs
- docs/design/ecrans/13_systeme-de-design.html — les quatorze composants et leurs états
- docs/design/ecrans/ — les douze écrans maquettés, référence de facture
- docs/05-design.md — la synthèse, la langue et les règles d'écran

Contraintes non négociables : mobile-first mais responsive · mode clair ET mode sombre, les deux ·
52 px de cible tactile en classe, 48 ailleurs, 44 en plancher absolu · un état n'est jamais porté par
la couleur seule, il porte aussi une forme et un mot · l'ocre porte l'attente, jamais l'erreur · une
action non autorisée est absente de l'écran, jamais grisée · un refus s'annonce avant la saisie et dit
son versant positif · aucun libellé métier en dur, ils viennent du country pack · les chiffres qui
s'empilent sont tabulaires · les montants avec l'espace fine insécable · tout écran de saisie porte le
ruban d'état.

Écris les fichiers de travail dans specs/[00X-nom-de-la-tranche]/design/ : un .dc.html par artboard,
plus canvas.json. Ils se versionnent ; le fichier assemblé, non. Reporte l'adresse du canvas publié
dans le spec.md de la tranche, sous les user stories.

Ne rien inventer hors de ces fichiers. Le but de cette planche est de rendre visible une dérive :
une entité, un état ou un champ qui n'existe pas dans le domaine doit sauter aux yeux.
```

### À la validation — la procédure, en trois gestes

**Dès que l'utilisateur valide la maquette, on l'applique sans attendre qu'il la demande.** Elle ne
prend que quelques secondes, et chacun de ces trois gestes évite une perte qu'on ne rattrape pas.

**1. Les sources vont à leur place.** Un `.dc.html` par artboard, plus `canvas.json` :

| La maquette est… | Elle va dans… |
|---|---|
| la planche de style, ou toute référence transverse | `docs/design/canvas/` |
| liée à une tranche | `specs/00X-nom-de-la-tranche/design/` |

Si l'agent les a écrites ailleurs pendant la session, on les déplace maintenant — **toute modification
future repart de ces sources**, jamais du canvas publié, et une source égarée est une maquette qu'on
devra refaire entièrement.

**2. L'adresse du canvas est reportée dans le `spec.md` de la tranche**, sous les user stories, sous
une ligne `## Revue visuelle`. Sans elle, le lien se perd à la session suivante.

**3. On dit en une ligne ce qui a été rangé** — où sont les sources, où est notée l'adresse. Rien de
plus : le rangement n'est pas un événement.

> **Ce qu'on ne fait pas** : versionner le fichier assemblé. Il pèse environ 2 Mo dont l'essentiel est
> le code de l'éditeur, et se régénère en une commande à partir des sources. Le `.gitignore` l'écarte
> déjà — aux deux emplacements.

---

**Suite** → [06-apres-mvp.md](06-apres-mvp.md) pour l'après, [progress.md](progress.md) pour le journal.
