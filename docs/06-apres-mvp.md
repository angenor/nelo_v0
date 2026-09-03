# 06 — Après le MVP

> ## Ce document est fermé jusqu'à ce qu'un établissement pilote édite ses bulletins dans Nelo.
>
> Rien de ce qui suit ne se construit avant. Ce n'est pas une liste de tâches : c'est ce qu'on saura
> **le jour où la question se posera**, pour ne pas la reprendre à zéro.
>
> **Un projet qui construit une plateforme multi-segments avant d'avoir un établissement qui paie ne
> construit rien du tout.**

---

## 1. À quoi sert ce document

Le document de conception d'origine décrivait **55 services et modules**, six segments
d'établissements et trois vagues de pays. Le MVP en garde le socle et douze modules.

Les quarante-trois autres ne sont pas abandonnés : ils sont **datés**. Ce fichier dit lesquels, dans
quel ordre, à quel coût, et — surtout — **quelles fractures il ne faut pas confondre**.

Il existe pour une raison précise : quand une tranche du MVP fige une colonne, il faut savoir si cette
colonne bloquera une extension. C'est **la porte P-08** qui répond à cette question, mécaniquement, en
506 tokens et sans ouvrir ce fichier. **Ne pas ouvrir ce document pour coder une tranche.**

### Ce qui a déjà été payé

Le modèle du MVP porte des provisions qui rendent ces extensions **additives plutôt que migratoires**.
Elles ne coûtent rien aujourd'hui et évitent une reprise de toutes les données demain :

| Provision | Sans elle |
|---|---|
| **Référentiel d'évaluation versionné, formules déclaratives** | Le passage à l'anglophone est une réécriture du module d'évaluation, du bulletin, et de tous les bulletins archivés |
| **Country pack, aucune littérale de pays hors du pack** | Chaque nouveau pays devient un déploiement |
| **Notes et coefficients en `NUMERIC`** | Migrer toutes les notes du produit le jour où un pack passe au pourcentage à décimales |
| **`annee_id NOT NULL` sur toute table pédagogique** | Les référentiels de N+1 écrasent ceux de N, et les bulletins archivés deviennent faux |
| **Absences en intervalle `[début, fin)`** | L'appel par demi-journée du primaire, par cours du secondaire et par UE du supérieur exigent trois modèles |
| **Capacités + périmètre, jamais des rôles fixes** | Un système de rôles ne se transforme pas en ABAC : il se remplace, avec toutes les vérifications d'accès |
| **`protection` sans dépendance entrante** | Le cloisonnement devient une convention, et une convention se contourne |
| **`inscription.regime` nullable** | L'internat devient une migration |
| **`classe.site_id` nullable** | Le groupe scolaire multi-sites devient une migration |
| **`evaluation.groupe_id` nullable** | Le dédoublement et les options rendent l'emploi du temps et l'appel faux |
| **`editeur` sans référence à `classe`, `note`, `bulletin`** | Un centre de formation continue, sans classes, devient infacturable |
| **Six capacités IA, chacune avec son test de refus** | Une capacité non implémentée est appelée en silence |

---

## 2. Le modèle à trois couches

```
socle/          tenants · personnes · habilitations · annees · communication · documents · pilotage
                → ne connaît ni « classe », ni « bulletin », ni « trimestre »

metier/         structure · scolarite · evaluation · vie_scolaire · conseil · finance · protection
                → le métier scolaire, commun à tous les segments

segments/       secondaire  [livré]
                prescolaire · primaire · technique · superieur  [à venir]
                → les spécialisations, additives
```

### Ce qui est réellement partagé

**De l'ordre de 70 à 80 % du code** entre le préscolaire et le supérieur. Une personne, un foyer, un
lien de responsabilité, une année scolaire, une capacité, un envoi SMS, une facture, un signalement :
tout cela est identique d'une maternelle à une université.

Ce qui diffère tient dans quatre fractures, et **il faut les nommer avant de les confondre**.

---

## 3. Les quatre fractures

### 3.1 Le modèle d'évaluation — la fracture principale

| | Francophone | Anglophone |
|---|---|---|
| Échelle | Note sur 20 | Pourcentage sur 100 |
| Restitution | Moyenne pondérée par coefficient | *Grade code* A1 (75-100) à F9 (< 40), C4-C6 valant *credit* |
| Découpage | Trimestres ou semestres | *Three terms* |
| Composition | Devoirs + compositions, pondérations locales | *Continuous assessment* 30 % + examen externe 70 % |
| Classement | Rang, moyenne générale | *Position in class*, par matière **et** globale, imprimée sur le bulletin |
| Instance | Conseil de classe, PV, mention | *Head teacher's remark*, critères de promotion |

**Cette fracture est déjà payée** par [ADR 010](adr/010-le-referentiel-d-evaluation-est-une-donnee-versionnee.md).
Le coût résiduel du passage anglophone est celui d'**écrire un country pack**, pas de modifier le
moteur. C'est la vérification la plus importante à faire au moment de la V3 : si le moteur doit être
touché, c'est que la provision a été dégradée quelque part.

### 3.2 L'unité d'inscription — la fracture du supérieur

**Un élève de secondaire appartient à une classe. Un étudiant s'inscrit à des unités
d'enseignement.**

Ce n'est pas une nuance de vocabulaire. Le modèle actuel — `inscription → classe`, un élève, une
classe, `n` groupes — ne décrit pas :

- l'inscription **par UE** avec crédits et capitalisation ;
- la **compensation** entre UE et la capitalisation d'une UE validée d'une année sur l'autre ;
- un étudiant redoublant qui ne repasse que trois UE sur huit ;
- les **mutualisations inter-filières** — la même UE servie à trois parcours.

**Coût estimé : 6 à 10 semaines-développeur** pour le module `segments/superieur`, dont la moitié pour
les délibérations et les jurys. **Ce n'est pas une extension du secondaire.**

**Ce qui a déjà été payé** : `classe_id` reste obligatoire sur l'inscription, mais l'entité `groupe`
et l'entité `enseignement` sont déjà des rattachements `n`-aires. Une UE est un `enseignement` avec
des crédits ; un parcours est une suite de `groupe`. La structure absorbe, elle ne bloque pas.

### 3.3 La nature de l'évaluation — note contre compétence

Trois segments n'évaluent pas avec des notes :

| Segment | Ce qu'il évalue |
|---|---|
| **Préscolaire** | **Observation par domaine d'apprentissage.** Il n'y a pas de note, pas de moyenne, pas de rang |
| **Primaire** | Évaluation **par compétence**, avec suivi des acquis fondamentaux — lecture, écriture, calcul |
| **Technique** | **Compétence certifiante**, avec livret de suivi et validation par le tuteur d'entreprise |

Le référentiel d'évaluation déclaratif absorbe le premier cas — une échelle à quatre niveaux
d'acquisition est une échelle. Il n'absorbe **pas** le troisième : une compétence certifiante n'est pas
une note dans une période, c'est un état qui se valide une fois et se conserve.

**Coût estimé : 3 à 5 semaines** pour le référentiel de compétences et le livret de suivi.

### 3.4 Le ministère de tutelle — la fracture administrative

**L'enseignement technique et professionnel relève en Côte d'Ivoire d'un ministère distinct** de celui
de l'éducation nationale, avec ses propres référentiels et ses propres remontées statistiques.

Ce n'est pas un détail de configuration : c'est un jeu complet de documents officiels, de formats de
remontée et de calendriers. Il vit dans le country pack — c'est exactement ce à quoi le pack sert —
mais **il double le travail de rédaction du pack ivoirien** le jour où le technique entre au
catalogue.

---

## 4. Les segments candidats, par ordre de coût

| Segment | Ce qu'il ajoute | Coût | Rang |
|---|---|---|---|
| **Primaire** | Évaluation par compétences, acquis fondamentaux, cantine subventionnée, coopérative scolaire | **2-4 sem.** | 1 |
| **Préscolaire** | Journal de vie quotidienne, ratio d'encadrement, observation par domaine, album photo à consentement révocable, **remise de l'enfant avec contrôle systématique** | **3-5 sem.** | 2 |
| **Technique et professionnel** | Ateliers et plateaux, alternance, stages et conventions tripartites, compétences certifiantes, équipements et EPI, relations entreprises | **8-12 sem.** | 3 |
| **Supérieur** | UE et crédits, LMD, concours, délibérations et jurys, recherche et CAMES, international, formation continue, vie étudiante, BU, qualité | **14-20 sem.** | 4 |

> **Le primaire est le moins cher parce que le socle a été conçu pour lui** : appel par demi-journée
> (l'intervalle), enseignant polyvalent (un `service_enseignant` couvrant toutes les matières), remise
> à la personne autorisée (déjà dans le modèle). Il valide surtout que le référentiel déclaratif
> absorbe une échelle non numérique.

---

## 5. Les country packs, dans l'ordre

| Vague | Marchés | Effort de localisation | Coût par pack |
|---|---|---|---|
| **V1** | **Côte d'Ivoire** | Pack complet | *(fait)* |
| **V2** | Sénégal, Bénin, Togo, Burkina Faso, Mali, Cameroun, Gabon | **Allégé** : même monnaie (XOF/XAF), même droit comptable (SYSCOHADA), même référentiel du supérieur (CAMES), structure scolaire proche. Ce qui change : examens, ministère, opérateurs de paiement | **1-2 sem.** |
| **V3** | Ghana, Nigeria, Kenya, Rwanda | **Lourd** : modèle d'évaluation, vocabulaire, structure de l'année | **3-5 sem.** *si* le référentiel déclaratif a tenu |

**La séquence est délibérée.** Le passage au monde anglophone n'est pas une traduction : c'est un
changement de modèle d'évaluation. Le socle a été conçu dès le départ pour l'absorber ; **la V3 est le
test de cette conception**, et si elle exige de toucher le moteur, la provision a été dégradée en
route.

Trois points de vigilance par pack anglophone :

- **le placement centralisé** — au Ghana, la sélection vers le second cycle passe par un système
  national d'affectation ; il faut s'y interfacer, pas s'y substituer ;
- **la transmission du contrôle continu au conseil d'examen** (WAEC) — c'est une intégration, pas un
  export ;
- **le mobile money change d'acteurs** : MTN MoMo dominant au Ghana, cartes et virements plus
  répandus au Nigeria qu'en zone UEMOA.

---

## 6. Les quatre capacités IA en attente

| Capacité | Ce qu'elle débloque | Coût | Risque |
|---|---|---|---|
| **C2 · Question-réponse documentaire** | Chatbot parent, assistant règlement intérieur, recherche documentaire. **Un cache sémantique absorbe l'essentiel du trafic** : les questions des parents sont extrêmement répétitives | 3-4 sem. | Hallucination |
| **C3 · Planification sous contraintes** | Emploi du temps, constitution des classes, salles d'examen, tournées de transport. **Ce n'est pas de l'IA générative : c'est un solveur** — et c'est la capacité au meilleur rapport valeur/risque | 6-10 sem. | Faible |
| **C4 · Analyse et détection de signaux** | Absentéisme, décrochage, anomalies comptables, prévision de trésorerie | 4-6 sem. | **Élevé quand il s'agit d'élèves** |
| **C6 · Assistance à l'apprentissage** | Quiz, fiches de révision, exercices différenciés | 4-6 sem. | Exactitude du contenu |

### C3 mérite d'arriver la première

La **constitution des classes N+1** est un problème d'optimisation sous contraintes, pas une liste :
effectif maximal, équilibre des niveaux, équilibre filles/garçons, choix d'options et de langues,
séparation d'élèves demandée par la vie scolaire, maintien ou dispersion des fratries, capacité des
salles, contraintes de service des enseignants.

**C'est le même moteur que l'emploi du temps.** Un solveur, deux usages, aucun risque de profilage de
mineurs. C'est la meilleure première extension IA du produit.

### C4 ne s'ouvre qu'avec ses garde-fous

Rappel de [ADR 011](adr/011-six-capacites-ia-pas-trente-quatre-agents.md), et il ne se relâche pas :

- **aucun score de risque individuel affiché** ;
- une alerte à destination d'**une personne nommée**, formulée en faits observables — « 7 absences en
  3 semaines, moyenne en baisse de 4 points » — jamais en jugement ;
- **aucune notification automatique aux familles** ;
- **aucune qualification** d'une situation de protection de l'enfance.

*« Prédire les risques d'échec » et « détecter les indicateurs de maltraitance » sont du profilage de
mineurs. Mal fait, cela produit un effet d'étiquetage durable sur des enfants.*

---

## 7. Les services d'établissement en attente

| Service | Pourquoi il compte | Coût |
|---|---|---|
| **RH et paie** | Contrats, agréments, **vérification des antécédents et habilitation à encadrer des mineurs**, services et charges horaires, congés, remplacements, préparation de paie CNPS | **8-12 sem.** |
| **Santé scolaire complète** | Registre d'infirmerie, campagnes de vaccination et de déparasitage, alertes épidémiques. *(La fiche d'urgence et les allergies sont déjà au MVP)* | 3-4 sem. |
| **Transport scolaire** | Itinéraires, listes embarquées imprimables, confirmation montée/descente, suivi GPS, facturation, conformité des véhicules | 5-7 sem. |
| **Restauration** | Menus, régimes, prépaiement, stocks, hygiène, **cantines subventionnées avec reporting dédié** | 4-6 sem. |
| **Économat et coopérative** | Manuels, uniformes, fournitures, photos scolaires. **Source de revenu réelle des établissements** | 4-6 sem. |
| **Patrimoine et maintenance** | Inventaire, tickets avec photo, maintenance préventive, **groupes électrogènes, onduleurs, panneaux solaires, forage** | 3-5 sem. |
| **Examens officiels** | Inscription aux examens nationaux, examens blancs, salles et surveillance, statistiques de réussite | 4-6 sem. |
| **Orientation** | Fiches métiers et filières du pays, vœux, entretiens, passerelles, information sur les bourses | 3-4 sem. |
| **Internat** | Chambres, appel du soir, sorties de week-end, facturation, communication avec les familles éloignées | 3-4 sem. |
| **CDI / bibliothèque** | Catalogue, prêt, ressources numériques, retards | 2-3 sem. |
| **Vie associative et sport** | Clubs, association sportive, compétitions, **délégués et *prefects*** | 2-3 sem. |
| **APE / COGES** | Instance avec bureau, cotisations, budget propre, réunions, projets financés | 2-3 sem. |
| **Sorties et voyages** | Autorisation parentale tracée, liste d'appel hors les murs, budget, assurance, encadrants | 2-3 sem. |
| **Recrutement d'élèves** | Le taux de réinscription et le recrutement sont des **indicateurs vitaux** d'un établissement privé, dès le primaire | 3-4 sem. |
| **Décrochage** | Détection, relance, médiation familiale, réinsertion, reporting à la tutelle | 3-4 sem. |
| **Assurances** | Assurance scolaire, responsabilité civile, accidents, sinistres | 2 sem. |
| **Alumni** | Réseau des anciens, source de dons et de réputation | 2-3 sem. |

**Trois d'entre eux se vendent tout seuls**, et méritent d'être regardés en premier après le MVP :
le **transport** (les familles le demandent et il se facture), l'**économat** (c'est une source de
revenu de l'établissement, donc un argument de retour sur investissement), et le **SMS entrant par
mot-clé** — qui n'est pas un service mais le point suivant.

---

## 8. Le SMS entrant — la première dette du MVP

C'est la seule chose reportée du MVP dont le report **coûte de l'argent tous les mois**.

Sans consultation en libre-service, l'information circule en flux sortant, **à la charge de
l'établissement**. Un parent qui veut connaître son solde n'a que deux options : appeler
l'établissement, ou recevoir un SMS que l'établissement paie.

**Ce qui est déjà conçu** ([ADR 013](adr/013-le-sms-est-un-canal-de-premier-rang.md)) : numéro long
virtuel fourni par l'agrégateur — il s'obtient sans négociation opérateur, contrairement à un code
court —, analyse du mot-clé, réponse automatique sous 160 caractères, **contrôle d'accès par le numéro
appelant**, et réponse générique sans donnée personnelle à un numéro inconnu.

**Coût estimé : 2 à 3 semaines.** C'est la meilleure première extension du produit après le MVP,
mesurée en marge.

---

## 9. Ce que le report du hors-connexion change pour la suite

[ADR 001](adr/001-hors-connexion-differe.md) diffère, il n'exclut pas. Quatre fondations sont déjà
posées : UUID v7 généré par le client, idempotence avec mémorisation de la réponse, horodatage serveur
faisant autorité avec conservation de l'horodatage client, journal d'événements immuable et permanent.

**Ce qu'il restera à faire le jour où la décision se réexamine :**

| Chantier | Coût |
|---|---|
| File d'actions persistante côté client, avec ordre et rejeu | 3-4 sem. |
| Classification de chaque entité selon sa tolérance à l'écriture concurrente | 2 sem. |
| **Arbitrage humain des écritures orphelines** — une note saisie hors ligne sur une période clôturée entre-temps | 3-5 sem. |
| Purge des caches contenant des données de mineurs sur appareil partagé | 2 sem. |
| Écrans de conflit et de reprise | 2-3 sem. |

**Total : 12 à 16 semaines**, et **il ne se réduit pas** : c'est le coût irréductible du hors-ligne,
pas une pénalité de report. Les fondations posées évitent la partie qui aurait été *impossible* à
rattraper, pas celle qui est simplement longue.

**Le déclencheur de réexamen** : si plus d'un pilote sur trois n'a pas de réseau utilisable en salle
de classe. C'est la première question à poser, et elle se pose **avant la vente**.

---

## 10. Ce que le report de Capacitor change pour la suite

[ADR 002](adr/002-web-d-abord-capacitor-plus-tard.md). L'enveloppe Capacitor autour de la même base
Nuxt coûte **2 à 3 semaines** — plus le cycle de publication dans deux magasins, qui est un coût
récurrent, pas ponctuel.

**Elle arrivera probablement avec le hors-connexion** : ce sont les deux mêmes besoins — un stockage
local fiable et une exécution en arrière-plan — et il serait absurde de payer deux fois la
qualification.

**Ce qui la déclenchera vraiment** : les notifications natives côté parent. Tant que le SMS porte les
notifications critiques, Capacitor n'apporte rien qu'un raccourci sur l'écran d'accueil ne fasse déjà.

---

## 11. Ce qu'il ne faut surtout pas faire maintenant

| Tentation | Pourquoi c'est une erreur |
|---|---|
| **Construire `segments/superieur` « pendant qu'on y est »** | C'est une autre unité d'inscription. Le faire maintenant spécialiserait le socle sur un besoin sans client |
| **Généraliser le référentiel d'évaluation « pour tous les cas »** | Il est déjà déclaratif. Le généraliser davantage sans un deuxième pays réel produit une abstraction fausse |
| **Écrire les country packs V2 à l'avance** | Un pack écrit sans client se découvre faux au premier client |
| **Ouvrir C4** | Profilage de mineurs, sans le retour terrain qui dirait ce qui est utile et ce qui étiquette |
| **Extraire un microservice** | Aucune frontière n'a encore été éprouvée par la charge |
| **Ajouter un segment dans `metier/`** | Il spécialiserait le noyau. `segments/` existe précisément pour ça |
| **Traiter les 43 modules restants comme une file d'attente** | Trois d'entre eux valent les quarante autres réunis. L'ordre compte plus que la liste |

---

## 12. Séquencement et effort réel

Après que le pilote a abandonné son classeur, et pas avant :

| Rang | Chantier | Coût | Ce qu'il débloque |
|---|---|---|---|
| 1 | **SMS entrant par mot-clé** | 2-3 sem. | De la marge, tous les mois |
| 2 | **C3 — solveur** (EDT + constitution des classes) | 6-10 sem. | La corvée la plus détestée de l'année scolaire |
| 3 | **Segment primaire** | 2-4 sem. | Le groupe scolaire multi-cycles complet |
| 4 | **Transport** | 5-7 sem. | Un module qui se facture aux familles |
| 5 | **Country packs V2** (2 pays) | 2-4 sem. | Le marché régional francophone |
| 6 | **Économat** | 4-6 sem. | Une source de revenu pour l'établissement |
| 7 | **RH et paie** | 8-12 sem. | Le dernier classeur papier de l'administration |
| 8 | **Segment préscolaire** | 3-5 sem. | La maternelle du groupe scolaire |
| 9 | **C2 — question-réponse** | 3-4 sem. | Une baisse du volume d'appels au secrétariat |
| 10 | **Country pack anglophone** | 3-5 sem. | **Le test de la conception du référentiel** |
| 11 | **Segment technique** | 8-12 sem. | Un segment volumineux et négligé par la concurrence |
| 12 | **Hors-connexion** | 12-16 sem. | *Si la mesure terrain le justifie* |
| 13 | **Segment supérieur** | 14-20 sem. | Un autre produit, presque |

**Total de la file : environ trois années-développeur.** C'est pourquoi elle est une file et non un
plan, et pourquoi elle se réordonne à chaque client gagné.

---

## 13. Questions ouvertes — aucune ne se tranche avant le jalon

1. **Le produit se vend-il au groupe scolaire ou à l'établissement ?** La facturation est par élève
   actif, mais le décideur est le fondateur du groupe. La réponse change le back-office éditeur.
2. **Le SMS se refacture-t-il au coût réel majoré, ou s'inclut-il dans un forfait ?** Le forfait est
   plus simple à vendre et transfère le risque à l'éditeur.
3. **Le partage de revenu sur l'encaissement mobile money** aligne les intérêts, mais peut créer un
   frein à l'adoption. À évaluer avec un pilote, pas en théorie.
4. **L'hébergement régional est-il exigible, ou seulement souhaitable ?** La réponse dépend du droit,
   et le droit était en révision.
5. **Un établissement peut-il exporter et partir ?** Oui, et c'est un argument de vente. Mais l'export
   doit-il être réimportable dans un concurrent, ou seulement lisible ?
6. **Le réseau de partenaires intégrateurs locaux** est-il un canal de distribution ou une source de
   support dégradé ? Les deux sont arrivés à d'autres éditeurs.
7. **Que se passe-t-il quand un établissement cesse de payer ?** Les données sont celles de mineurs, et
   la durée légale de conservation ne dépend pas du contrat.

---

**Retour** → [00-brief.md](00-brief.md) pour le périmètre, [progress.md](progress.md) pour l'état.
