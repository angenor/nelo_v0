# ADR 011 — Six capacités IA, pas trente-quatre agents

**Statut** : accepté · **Date** : 2026-08-21

## Contexte

La tentation commerciale est d'annoncer un agent autonome par service — trente et quelques agents,
chacun capable d'exécuter la totalité des tâches de son domaine. C'est un mauvais choix, pour trois
raisons distinctes :

1. **C'est faux techniquement.** Ces trente-quatre agents sont en réalité cinq ou six capacités
   identiques déclinées par domaine. Les construire séparément multiplie par trente-quatre le coût de
   développement, d'évaluation et de maintenance, pour une valeur ajoutée nulle.
2. **C'est intenable juridiquement.** L'autonomie complète sur la notation, la discipline, la santé,
   le psychosocial et la paie expose l'établissement et l'éditeur.
3. **C'est dangereux sur certains sujets.** « Prédire les risques d'échec » et « détecter les
   indicateurs de maltraitance » sont du profilage de mineurs. Mal fait, cela produit un effet
   d'étiquetage durable sur des enfants.

## Décision

**L'architecture est celle de six capacités transverses.** La promesse commerciale « trente-quatre
agents » peut rester un argument de présentation ; un « agent » est une **composition de ces capacités
avec un jeu d'outils et de données restreint à un domaine** — un profil de configuration, pas un
système distinct.

| Capacité | MVP |
|---|---|
| **C1 · Rédaction assistée** — appréciations, courriers, PV, traduction | **Oui**, niveau B |
| **C2 · Question-réponse documentaire** | Non |
| **C3 · Planification sous contraintes** — *et ce n'est pas de l'IA générative : c'est un solveur* | Non |
| **C4 · Analyse et détection de signaux** | Non |
| **C5 · Extraction documentaire** — pièces, reçus, import désordonné | **Oui** |
| **C6 · Assistance à l'apprentissage** | Non |

**Et trois niveaux d'autonomie, dont le troisième est un interdit :**

| Niveau | Définition |
|---|---|
| **A · Autonome** | L'IA exécute et informe |
| **B · Proposition validée** | L'IA propose, **un humain nommé valide avant effet** |
| **C · Interdit à l'IA** | **Note finale et décision de passage · sanction disciplinaire · qualification d'une situation de protection de l'enfance · diagnostic médical · décision RH individuelle · attribution ou retrait d'une bourse · exclusion d'un élève** |

## Conséquences

- **Aucun score de risque individuel d'élève n'est affiché.** C4, quand elle arrivera, produira une
  alerte à destination d'une personne nommée, formulée en **faits observables** — « 7 absences en
  3 semaines, moyenne en baisse de 4 points » — jamais en jugement.
- Toute sortie d'IA est étiquetée comme telle et porte le nom du validateur humain quand elle produit
  un effet.
- `journal_ia` enregistre quelle capacité, quel modèle, quelles données, quelle sortie, quel
  validateur. Exigence de conformité et de défense.
- Le contenu généré est évalué sur les stéréotypes de genre, d'origine et de milieu social avant mise
  en production — sujet particulièrement sensible sur les appréciations de bulletin et l'orientation.
- Chaque capacité non implémentée porte **son test de refus explicite** (porte P-08). Une capacité
  ignorée en silence finit par être appelée.

**Le prix accepté** : la promesse commerciale et l'architecture ne disent pas la même chose. C'est
assumé, et c'est documenté ici pour que personne ne construise trente-quatre agents en croyant tenir
une promesse.

## Alternatives écartées

| Alternative | Motif du refus |
|---|---|
| Un agent autonome par service | Trente-quatre fois le coût pour la même valeur, et une exposition juridique majeure |
| IA sur la notation et la discipline | Interdit de niveau C. Non négociable |
| Pas d'IA du tout | C1 et C5 ont une valeur réelle et un risque faible |
