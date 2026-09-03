# ADR 018 — Le MVP commence par le primaire

**Statut** : accepté · **Date** : 2026-09-03 · **Décision de segment, pas de périmètre fonctionnel**

## Contexte

Le corpus posé le 2026-08-21 retenait **un seul segment au MVP : le secondaire général**, collège et
lycée. Le primaire était le **rang 1 de la file d'après-MVP**, à deux à quatre semaines, et
[06-apres-mvp.md § 4](../06-apres-mvp.md) en donnait déjà le motif :

> **Le primaire est le moins cher parce que le socle a été conçu pour lui** : appel par demi-journée
> (l'intervalle), enseignant polyvalent (un `service_enseignant` couvrant toutes les matières), remise
> à la personne autorisée (déjà dans le modèle).

Ce constat, écrit pour justifier un rang d'extension, se retourne : **si le segment le moins cher est
celui que le socle absorbe le mieux, c'est par lui qu'on éprouve le socle**, pas par le plus lourd.

Le client type reste le **groupe scolaire multi-cycles** — maternelle, primaire, collège, lycée sous
une même fondation. Le MVP ne le sert entièrement dans aucune hypothèse ; la question n'est pas *quel
segment couvrir*, c'est **par quel cycle du groupe on entre**.

## Décision

**Le MVP livre `segments/primaire`.** L'ordre de couverture des segments devient :

| Rang | Segment | Quand |
|---|---|---|
| **1** | **Primaire** | **MVP** |
| 2 | Préscolaire | Après-MVP, 3-5 sem. |
| 3 | Secondaire général | Après-MVP, 4-6 sem. |
| 4 | Technique et professionnel | Après-MVP, 8-12 sem. |
| 5 | Supérieur | Après-MVP, 14-20 sem. |

**Les vingt-et-une tranches restent vingt-et-une.** Aucune n'est ajoutée, aucune n'est retirée : elles
changent d'**hypothèses de travail**, pas de nombre. Le socle, le modèle, le contrat et le système de
design ne bougent pas — ils étaient déjà agnostiques du segment, et cette décision en est la première
vérification réelle.

## Conséquences

### Ce qui change, tranche par tranche

| Tranche | Ce que le primaire y change |
|---|---|
| **T2b** | **La série disparaît du cas nominal** — `serie_code` reste nullable, il n'est simplement jamais rempli. Le coefficient reste porté par l'enseignement : le français n'a pas le même coefficient au CP1 et au CM2 |
| **T2b** | **L'enseignant est polyvalent** : un `service_enseignant` par matière pour la même personne sur la même classe. Le maître titulaire *est* le professeur principal |
| **T5** | **L'appel est par demi-journée**, pas par cours. L'intervalle `[début, fin)` l'absorbe sans changement — c'est exactement la provision annoncée |
| **T6a** | **Le pack ivoirien livre l'évaluation du primaire.** Si le pack déclare une échelle d'acquisition par compétence, le moteur la traite comme une échelle de plus — et **c'est le test que le référentiel était bien déclaratif** |
| **T6b** | **Le même enseignant saisit toutes les matières de sa classe** : la grille change de matière sans quitter l'écran |
| **T6c** | Le bulletin restitue le niveau atteint par compétence quand le pack en déclare un, par le même moteur et le même gabarit. Le même maître rédige toutes les appréciations |
| **T7** | **Le conseil des maîtres**, pas le conseil de classe. Ni délégués élèves, ni réorientation de série. Le libellé de l'instance et la liste des issues viennent **du pack** |
| **T7** | En fin de cycle, le passage dépend d'un **examen national** — hors périmètre : on s'y interface, on ne s'y substitue pas ([00-brief.md § 6](../00-brief.md)) |
| **T8c** | **La tranche perd son cas nominal** — voir ci-dessous |

### Ce que la décision coûte

**T8c est la vraie perte.** L'affectation d'élèves par l'État vers le privé est, en Côte d'Ivoire, un
dispositif **du secondaire** : il se joue à l'entrée en sixième. Un établissement primaire privé n'a
pas d'élèves affectés. La tranche garde son modèle — décision de financement public, créance par année
de rattachement, réconciliation des trois effectifs, attestation qui déclenche le paiement — mais son
**cas nominal devient la subvention à l'établissement conventionné**, et l'élève affecté n'arrive
qu'avec le segment secondaire. **T8c reste au MVP et garde son rang 17** : son modèle est ce qui
serait irrattrapable, pas ses valeurs par défaut, qui dépendaient déjà de Q9 et de Q19.

**Les treize maquettes portent des données de secondaire** — « 6ᵉ A », professeurs de matière, conseil
de classe. Le **système de design ne change pas** : ce sont des jeux de données fictifs, repris écran
par écran à la revue visuelle qui suit chaque `specify`.

**Ce que le primaire ajoute au MVP** : l'échelle du pack ivoirien primaire, et — si le pilote
l'attend — une échelle d'acquisition par compétence, qui est **une échelle de plus dans le référentiel
déclaratif**, donc absorbée par [ADR 010](010-le-referentiel-d-evaluation-est-une-donnee-versionnee.md).
Le **suivi longitudinal des acquis fondamentaux** — l'acquis qui se conserve d'une période à l'autre —
n'est **pas** une échelle : il reste hors MVP, avec le livret de compétences du technique.

**Ce qui reste hors MVP malgré le changement de segment** : la cantine subventionnée et la coopérative
scolaire, citées par [06-apres-mvp.md § 4](../06-apres-mvp.md) comme apports du segment primaire, sont
des **services d'établissement** (restauration, économat) et restent au § 7 du même document.

### Ce que la décision gagne

- **Le segment le moins cher éprouve le socle en premier.** Pas de série, pas d'emploi du temps par
  matière, un appel par demi-journée : ce qui reste à valider, c'est le socle lui-même.
- **L'écran qui décide de l'adoption se valide sur son cas le plus simple.** Un maître appelle sa
  classe deux fois par jour, pas huit professeurs six fois.
- **La provision d'agnosticité est vérifiée pour de vrai**, et tôt. Un corpus écrit pour le secondaire
  qui accueille le primaire sans toucher au modèle ni au contrat, c'est la démonstration que
  [ADR 010](010-le-referentiel-d-evaluation-est-une-donnee-versionnee.md) et
  [ADR 014](014-la-localisation-passe-par-le-country-pack.md) tiennent. **Si une entité doit être
  ajoutée pour accueillir le primaire, la provision était fausse** — et il vaut mieux le découvrir
  maintenant que trois ans plus tard sur un pack ghanéen.

## Ce que la décision NE change pas

Le socle, `modules/metier/`, le modèle de [02-domaine.md](../02-domaine.md), le contrat de
[03-api.md](../03-api.md), les jetons et les composants de [05-design.md](../05-design.md), les onze
epics, les vingt-et-une tranches et leur ordre, les douze portes de vérification, et les dix-sept ADR
antérieurs. **Aucune règle non négociable n'est touchée.**

## Alternatives écartées

| Alternative | Motif du refus |
|---|---|
| **Garder le secondaire au MVP** | Le corpus lui-même désigne le primaire comme le segment le mieux absorbé par le socle. Commencer par le plus lourd, c'est payer la complexité de la série et de l'emploi du temps par matière avant d'avoir un client |
| **Couvrir primaire + préscolaire + secondaire au MVP** | Sept à onze semaines-développeur de plus, et trois natures d'évaluation à valider en même temps. Un MVP qui couvre trois cycles ne se livre pas |
| **Ne rien écrire et « configurer » le segment au moment du pilote** | Le segment n'est pas un réglage : il décide des jeux de données d'exemple, des critères de fin et des maquettes. Un corpus qui dit « secondaire » partout produit des tranches taillées pour le secondaire |
| **Ajouter une tranche « T11 — le segment primaire »** | Le primaire n'est pas une couche posée sur un produit secondaire : c'est l'hypothèse de travail des tranches existantes. Une tranche séparée reconstruirait le secondaire d'abord |

## Question laissée ouverte

**Le motif commercial du choix appartient au pilote, pas au corpus.** Cette décision consigne l'ordre
et son coût ; ce que le pilote attend réellement de l'évaluation au primaire — barème sur dix ou sur
vingt, livret de compétences ou bulletin de moyennes — est **Q26** dans
[progress.md](../progress.md), et il décide du contenu du pack, jamais du moteur.
