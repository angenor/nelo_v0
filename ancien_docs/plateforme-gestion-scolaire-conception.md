# Plateforme de Gestion Scolaire et Universitaire — Afrique francophone et anglophone

**Document de conception — Version 1.0 — Août 2026**
Marché : Afrique de l'Ouest et Centrale francophone + Afrique anglophone
Pays pilote : **Côte d'Ivoire**
Architecture : Monolith-First, Microservice-Ready — Nuxt 4 / Rust (Actix Web) / FastAPI (sidecar IA)

---

> **Statut du document** : document de conception interne. Les éléments réglementaires (montants, dénominations ministérielles, textes de loi) sont donnés à titre indicatif et **doivent être validés par un conseil juridique local** avant tout engagement contractuel. Voir Partie 8.2.

---

## Sommaire

- **Partie 0 — Cadrage stratégique**
- **Partie 1 — Socle métier commun** (le noyau non négociable)
- **Partie 2 — Catalogue des services**
- **Partie 3 — Architecture technique**
- **Partie 4 — Canaux et applications**
- **Partie 5 — Stratégie IA**
- **Partie 6 — Produit SaaS et go-to-market**
- **Partie 7 — MVP et feuille de route**
- **Partie 8 — Risques, hypothèses et décisions à trancher**
- **Annexes** — Glossaire FR/EN, country packs, modèle de données

---

# PARTIE 0 — CADRAGE STRATÉGIQUE

## 0.1 Marché cible et séquence de déploiement

| Vague | Marchés | Justification | Effort de localisation |
| :-- | :-- | :-- | :-- |
| **V1 — Pilote** | Côte d'Ivoire | Marché d'origine, densité d'établissements privés, mobile money mature, zone OHADA/UEMOA | Country pack complet |
| **V2 — Extension francophone** | Sénégal, Bénin, Togo, Burkina Faso, Mali, Cameroun, Gabon | Même monnaie (XOF/XAF), même droit comptable (SYSCOHADA), même référentiel supérieur (CAMES), structure scolaire proche | Country pack allégé : examens, ministère, opérateurs de paiement |
| **V3 — Anglophone** | Ghana, Nigeria, Kenya, Rwanda | Marchés volumineux, forte densité d'écoles privées, MTN MoMo / Paystack / M-Pesa | Country pack lourd : modèle d'évaluation, vocabulaire, structure de l'année |

La séquence est délibérée : **le passage au monde anglophone n'est pas une traduction, c'est un changement de modèle d'évaluation.** Le socle (Partie 1) doit être conçu dès le départ pour absorber ce changement, sinon la V3 sera une réécriture.

## 0.2 Segments d'établissements couverts

| Segment | Traitement |
| :-- | :-- |
| Préscolaire / maternelle | Modules dédiés (Partie 2.3.1) |
| Primaire | Socle commun + évaluation par compétences |
| Secondaire général (collège + lycée) | Socle commun + 7 modules |
| Secondaire technique et professionnel | Socle commun + 6 modules (Partie 2.3.4) |
| Supérieur (université, grande école, IUT/BTS) | Socle commun + 10 modules, localisés CAMES/LMD |
| Groupe scolaire multi-sites / multi-cycles | Transverse — c'est le client type en Côte d'Ivoire |
| Formation continue / executive education | Module du supérieur |

Le **groupe scolaire multi-cycles** (une même fondation exploitant maternelle + primaire + collège + lycée, parfois sur plusieurs sites) est le profil de client dominant sur le marché privé ivoirien. La plateforme doit gérer une fratrie répartie sur trois cycles avec une facturation consolidée par famille, et une direction générale qui pilote l'ensemble tout en laissant chaque site autonome sur son quotidien.

## 0.3 Les huit contraintes structurelles qui dictent l'architecture

Ces contraintes ne sont pas des « limitations à contourner » : ce sont les données d'entrée de la conception.

1. **Le parent n'a pas forcément de smartphone ni de data.** Une part significative des responsables légaux, en particulier hors Abidjan, dispose d'un téléphone basique ou d'un smartphone sans forfait data actif. Toute fonctionnalité critique (absence, convocation, échéance de paiement) doit exister en SMS.
2. **L'électricité est intermittente.** Un serveur on-premise dans un établissement s'éteindra. Le modèle par défaut est le cloud, avec un cache local résilient côté client.
3. **La connectivité est intermittente et coûteuse.** La plateforme fonctionne en ligne, mais chaque écran doit rester utilisable sur une connexion lente : pages légères, envois tolérants à la latence, reprise après coupure sans perte de saisie. Le volume de données échangées est un critère de conception, pas un détail.
4. **Le paiement est mobile money, pas carte bancaire.** La Côte d'Ivoire est le premier marché de mobile money d'Afrique de l'Ouest francophone, avec plus de 28 millions de comptes actifs répartis entre Wave, Orange Money, MTN MoMo et Moov. Une intégration carte bancaire seule est inutilisable.
5. **L'État est un payeur majeur et un mauvais payeur.** Pour les établissements privés accueillant des élèves affectés, la trésorerie dépend de subventions versées avec retard. En février 2025, les fondateurs d'établissements privés laïcs réclamaient l'apurement de 118 milliards de FCFA d'arriérés au titre de l'année 2023-2024. Le module financier doit modéliser cette créance et son ancienneté.
6. **La capacité informatique de l'établissement est faible.** Il n'y a souvent ni DSI ni service informatique. Le produit doit être administrable par un censeur ou un économe, et le support doit être humain et local.
7. **Les données existantes sont dans Excel, sur papier, ou dans un logiciel abandonné.** La migration n'est pas une option : c'est la première fonctionnalité vendue.
8. **Le prix de référence est bas.** Une tarification par élève et par an doit se situer dans un ordre de grandeur compatible avec des frais de scolarité en FCFA, ce qui contraint fortement le coût d'infrastructure et le coût d'inférence IA par élève.

## 0.4 Principes de conception non négociables

| # | Principe | Conséquence concrète |
| :-- | :-- | :-- |
| P1 | **Tolérance à la connexion lente** | Budget de poids par écran, envoi idempotent avec reprise, aucune saisie perdue sur coupure, procédure papier de secours |
| P2 | **Le SMS est un canal de premier rang, pas un repli** | Chaque notification métier a une variante SMS de moins de 160 caractères, rédigée pour ce canal |
| P3 | **Multi-pays par configuration, jamais par branche de code** | Aucun `if country == "CI"` dans la logique métier ; tout passe par le country pack |
| P4 | **Bilingue FR/EN dès le socle** | Modèle de données neutre, libellés externalisés, y compris les noms d'entités métier |
| P5 | **L'IA assiste, l'humain décide** | Aucune décision produisant un effet juridique ou disciplinaire n'est exécutée sans validation nommée |
| P6 | **Le cloisonnement prime sur les habilitations** | Les données santé, psychosociales et de protection de l'enfance sortent du système d'habilitation général |
| P7 | **Toute donnée d'élève est une donnée de mineur** | Base légale, durée de conservation et journal d'accès définis pour chaque traitement |
| P8 | **Le coût par élève est un budget, pas un résultat** | Chaque fonctionnalité IA porte une estimation de coût d'inférence par élève et par an |

## 0.5 Périmètre exclu (assumé)

Pour éviter la dérive de périmètre, la plateforme **ne fera pas** :

- de contenu pédagogique propriétaire (cours, manuels) — elle héberge et distribue, elle ne produit pas le curriculum ;
- de LMS complet type Moodle en V1 — un dépôt de ressources et un cahier de textes suffisent ;
- de comptabilité générale certifiée — elle produit les écritures et les exports vers un logiciel comptable SYSCOHADA, sans prétendre le remplacer en V1 ;
- de paie complète et déclarative en V1 — elle prépare, elle n'assume pas la responsabilité déclarative CNPS/impôts ;
- de gestion des concours nationaux et affectations d'État — ces plateformes appartiennent aux ministères ; la plateforme s'y **interface** au mieux, elle ne s'y substitue pas ;
- de **mode hors ligne** : la plateforme fonctionne en ligne, avec une tolérance forte à la connexion lente et une procédure papier de secours (3.3). Décision réexaminable une fois le produit installé ;
- d'**application native** au démarrage : l'accès se fait par le web, installable sur l'écran d'accueil ; le passage par Capacitor est une option de phase ultérieure.

---

# PARTIE 1 — SOCLE MÉTIER COMMUN

> C'est la partie la plus importante du document. Les six premiers points ci-dessous sont des **refontes de schéma de base de données** s'ils sont ajoutés après coup : ils doivent être tranchés avant la première ligne de code.

## 1.1 Référentiel des personnes, familles et responsables légaux

Raisonner en « parents » ne suffit pas. La réalité est plus complexe et n'est pas modélisable a posteriori.

**Entités**

- `Personne` — entité unique et unique source de vérité. Une même personne peut être simultanément parent d'un élève, enseignant vacataire dans l'établissement, et membre du bureau de l'APE : un seul enregistrement, trois rôles.
- `Foyer` — regroupement d'adressage et de facturation. Un élève peut relever de deux foyers (garde alternée, parents séparés).
- `Lien de responsabilité` — relie une `Personne` à un `Élève` avec un type qualifié.

**Typologie des liens à modéliser explicitement**

| Attribut du lien | Valeurs | Pourquoi c'est indispensable |
| :-- | :-- | :-- |
| Nature | père, mère, tuteur légal, tuteur de fait, grand-parent, oncle/tante, aîné de fratrie, employeur, institution | Le « tuteur de fait » — l'enfant confié à un parent en ville pour la scolarité — est extrêmement fréquent en Afrique de l'Ouest |
| Autorité parentale | oui / non / partagée | Conditionne qui peut autoriser une sortie, une opération, un changement d'établissement |
| Contact prioritaire | rang 1..n | Détermine l'ordre d'appel en cas d'urgence |
| Destinataire des communications | par type (scolaire / financier / disciplinaire / santé) | Le père peut recevoir la facture et la mère les absences |
| Redevable financier | quote-part en % | Facturation éclatée entre deux payeurs |
| Autorisé à récupérer l'enfant | oui / non + pièce d'identité | Sujet de sécurité physique, pas de confort |
| Actif | oui / non + date de fin | Décès, déchéance, changement de tuteur |

**Fonctionnalités associées**

- Fratrie : détection automatique, remise fratrie paramétrable, vue famille consolidée sur trois cycles.
- Consolidation de facturation par foyer avec un échéancier unique et un solde par payeur.
- Registre des personnes autorisées à récupérer un élève, avec photo et pièce d'identité, consultable par le personnel de sortie et imprimable par classe.
- Historique complet des changements de responsabilité, horodaté et non modifiable.

## 1.2 L'année scolaire comme objet de premier ordre

C'est techniquement le morceau le plus difficile d'un système d'information scolaire, et celui qui est le plus souvent traité trop tard.

**Ce qu'une année scolaire porte**

- une structure pédagogique propre (les classes de 2025-2026 ne sont pas celles de 2026-2027) ;
- une grille tarifaire propre ;
- un référentiel d'évaluation propre (coefficients, barèmes) ;
- un calendrier propre (trimestres/semestres/terms, vacances, jours fériés, examens) ;
- un état : `préparation` → `active` → `clôturée` → `archivée`.

**Le processus de bascule d'année** (le plus sous-estimé)

1. Ouverture de l'année N+1 en préparation, **pendant que N est encore active**. Les deux années coexistent : on réinscrit pour septembre alors que le troisième trimestre n'est pas terminé.
2. Duplication paramétrable de la structure (niveaux, matières, coefficients, tarifs) avec possibilité de modification.
3. Import des décisions de passage issues des conseils de classe (voir 1.5).
4. Constitution des classes N+1.
5. Campagne de réinscription et d'inscription.
6. Clôture de N : gel des notes, archivage des bulletins en PDF signé, calcul des indicateurs, apurement des comptes.
7. Archivage : les données de N restent consultables en lecture seule pour la durée légale de conservation, y compris après le départ de l'élève.

**Règles à trancher explicitement** : que devient une note saisie après la clôture ? Un élève peut-il être inscrit dans deux années actives ? Un bulletin réédité trois ans plus tard doit-il refléter le barème de l'époque (oui) ou le barème courant (non) ? Cette dernière règle impose le **versionnage de tous les référentiels**.

## 1.3 Structure pédagogique

Classe, niveau et groupe sont trois notions distinctes qu'il ne faut jamais confondre. Modèle cible :

```
Établissement
 └─ Cycle (préscolaire, primaire, 1er cycle secondaire, 2nd cycle, supérieur)
     └─ Niveau (CP1, CM2, 6e, Tle, L1…)
         └─ Série / Filière / Track (A, C, D ; Science/Arts/Business ; Génie civil…)
             └─ Classe (6e A, Form 2 Blue) ── rattachée à une salle et un professeur principal
                 └─ Groupe (LV2 espagnol, groupe TP 1, groupe de soutien, option EPS)
```

- Un élève appartient à **une** classe et à **n** groupes.
- Un enseignement (`Matière × Niveau × Année`) porte un coefficient, un volume horaire, un statut (obligatoire/optionnel) et un mode d'évaluation.
- Les **dédoublements** (une classe scindée en deux groupes pour les TP) doivent être modélisés au niveau du groupe, sinon l'emploi du temps et l'appel sont faux.
- Le **professeur principal / form master / class teacher** est un rôle rattaché au couple (classe, année), pas à une personne globalement.

## 1.4 Référentiel d'évaluation configurable

**C'est le point qui décide de la viabilité de l'extension anglophone.** Les deux modèles sont irréconciliables si le calcul est codé en dur.

| Dimension | Modèle francophone (CI, SN, BF…) | Modèle anglophone (GH, NG…) |
| :-- | :-- | :-- |
| Échelle | Note sur 20 | Pourcentage sur 100 |
| Restitution | Moyenne pondérée par coefficient | Grade code sur l'échelle WAEC A1 (75-100) à F9 (moins de 40), avec les grades C4 à C6 comptant comme credit |
| Découpage de l'année | Trimestres ou semestres | Three terms |
| Composition de la note | Devoirs + compositions, pondérations locales | Continuous assessment 30 % + examen externe 70 % pour les examens certifiants |
| Classement | Rang dans la classe, moyenne générale | Position in class, affichée par matière et globalement sur le bulletin |
| Instance de décision | Conseil de classe, PV, mention | Head teacher's remark, promotion criteria |
| Document | Bulletin trimestriel | Terminal report / report card |

**Implémentation** : le référentiel d'évaluation est une **entité versionnée par pays et par année**, contenant :

- l'échelle de notation et ses bornes ;
- la table de conversion note → grade (le cas échéant) ;
- la formule de composition de la note périodique (arbre de calcul déclaratif, pas du code) ;
- les règles d'arrondi (elles sont une source majeure de contestation) ;
- les règles de rang, d'ex æquo et de mention ;
- le gabarit de bulletin associé.

Le moteur de calcul est un **interpréteur de formules déclaratives**, pas une fonction Rust par pays. Sans cela, chaque nouveau pays devient un déploiement.

## 1.5 Conseil de classe, décision de passage et constitution des classes

Le conseil de **classe** est le rituel central de l'année scolaire : il ne doit pas être confondu avec le conseil de **discipline**, qui relève de la vie scolaire (S06).

**Conseil de classe**

- Convocation, ordre du jour, quorum, participants (dont délégués élèves et parents).
- Préparation automatique du dossier : moyennes, rang, assiduité, incidents, appréciations par matière.
- Saisie de l'appréciation générale et de la mention/sanction positive (tableau d'honneur, encouragements, avertissement travail/conduite).
- Procès-verbal signé et archivé.

**Décision de fin d'année** — une entité en soi, avec une valeur juridique

- Valeurs : admis en classe supérieure / admis sous condition / redoublement / réorientation vers une autre série / exclusion / orientation vers l'enseignement technique.
- Voie de recours et délai.
- Verrouillage après notification aux familles.

**Constitution des classes N+1** — un problème d'optimisation sous contraintes, pas une liste

Contraintes à respecter : effectif maximal, équilibre des niveaux scolaires, équilibre filles/garçons, choix d'options et de langues vivantes, séparation d'élèves demandée par la vie scolaire, maintien ou dispersion des fratries, capacité des salles, contraintes de service des enseignants. C'est le même moteur de contraintes que celui utilisé pour l'emploi du temps (voir 5.2, capacité « Planification »).

## 1.6 Financement : payeurs multiples et élèves subventionnés

Le modèle simple « les parents paient l'école » est faux pour une part majeure des effectifs du privé en Côte d'Ivoire.

**Les circuits de financement à modéliser**

| Circuit | Payeur | Spécificités |
| :-- | :-- | :-- |
| Scolarité privée classique | Foyer(s) | Échéancier, remise fratrie, remise personnel, pénalités |
| **Élève affecté / subventionné par l'État** | État + complément famille | Plus d'un tiers des élèves du premier cycle du secondaire sont scolarisés dans un établissement privé financé par l'État. Circuit et pièces distincts |
| Bourse (État, entreprise, ONG, fondation, diaspora) | Tiers | Convention, conditions de maintien, justificatifs |
| Prise en charge employeur | Entreprise | Facturation à l'employeur, attestation, plafond |
| Parrainage individuel | Personne physique | Reporting au parrain |

**Ce que le module « élèves affectés » doit gérer**

- Rattachement de l'élève à une décision d'affectation de l'État et à sa cohorte.
- **Contrôle et attestation d'effectif** : c'est la pièce qui déclenche le paiement. Les fondateurs eux-mêmes demandent l'amélioration du processus de contrôle des effectifs afin que les décisions financières soient établies dans les délais prévus par la convention avec l'État — échéances des 30 mars, 30 juin et 30 septembre.
- **Suivi de la créance sur l'État** : montant dû, année de rattachement, ancienneté, encaissements partiels. Un établissement doit pouvoir sortir en un clic l'état de ses arriérés par année.
- Séparation stricte entre ce que l'État couvre et ce qui est facturable à la famille — sujet sensible et contrôlé.
- Réconciliation entre l'effectif déclaré, l'effectif contrôlé et l'effectif payé.

**Impact trésorerie** : le tableau de bord financier doit distinguer *chiffre d'affaires facturé*, *encaissé* et *encaissable à court terme*, faute de quoi il est mensonger pour un établissement conventionné.

## 1.7 Communication multicanale et canal dégradé

Le point de départ n'est pas la notification push : c'est le fait qu'une part importante des responsables légaux n'a ni smartphone ni forfait data actif.

**Hiérarchie des canaux**

| Canal | Usage | Coût | Fiabilité |
| :-- | :-- | :-- | :-- |
| Notification web (espace en ligne) | Tout | Nul | Moyenne — dépend de la data et de l'autorisation du navigateur |
| WhatsApp Business API | Notification riche, échanges | Par conversation | Bonne, mais dépend de la data |
| **SMS** | Absence, convocation, échéance, résultat, urgence | Par message — **poste de coût majeur** | Très bonne |
| **SMS entrant (mot-clé)** | Consultation à la demande : solde, absences, prochaine échéance | Faible | Très bonne, sans data ni smartphone |
| Voix / SVI | Urgence, illettrisme | Élevé | Bonne |
| Papier | Bulletin, convocation officielle, avis de situation | Impression | Totale |

**Règles**

- Chaque type de message porte une **variante par canal**, rédigée séparément (un SMS n'est pas un push tronqué).
- Une **politique de routage** par établissement : quel événement part sur quel canal, pour quel profil de destinataire, avec quel budget mensuel.
- Un **budget SMS** paramétrable avec alerte de dépassement, et une facturation à l'établissement, sinon le modèle économique est intenable.
- **Fenêtres d'envoi** respectant les heures ouvrables et les jours de repos.
- **Illettrisme** : prévoir la synthèse vocale en langue locale pour les messages critiques (à évaluer en V3, pas en MVP, mais à ne pas rendre impossible par l'architecture).

**Comment le parent sans smartphone consulte**

| Besoin | Solution retenue |
| :-- | :-- |
| Être informé d'un événement (absence, convocation, échéance) | **SMS sortant**, déclenché par l'événement |
| Consulter à la demande (solde, absences du mois, prochaine échéance) | **SMS entrant par mot-clé** vers un numéro dédié fourni par l'agrégateur (`SOLDE`, `ABSENCE`), avec réponse automatique. Un numéro long virtuel s'obtient sans négociation opérateur, contrairement à un code court |
| Faire le point périodiquement | **Récapitulatif SMS** hebdomadaire ou mensuel, un seul message groupé au lieu d'une consultation |
| Situation complète et pièces justificatives | **Avis de situation imprimé**, remis à l'élève ou disponible à l'accueil, généré en un clic par l'économat |
| Échange nécessitant une réponse | Appel de l'établissement, ou WhatsApp si le parent en dispose |

**Conséquence à assumer** : sans consultation gratuite en libre-service, l'information circule surtout en flux sortant, donc **à la charge de l'établissement**. Deux mesures compensent : le regroupement des notifications non urgentes en un récapitulatif périodique plutôt qu'un SMS par événement, et une politique de routage qui réserve le SMS unitaire aux événements réellement critiques (absence non justifiée, convocation, échéance dépassée). Le reste passe par l'espace en ligne, WhatsApp ou le papier.

## 1.8 Identité, habilitations et cloisonnement

Quatre couches distinctes, à ne pas confondre.

1. **Authentification** — numéro de téléphone comme identifiant principal (pas l'e-mail : beaucoup de parents n'en ont pas), OTP par SMS, code PIN pour les usages fréquents, biométrie sur mobile. Comptes partagés à interdire explicitement côté personnel, à tolérer côté famille avec traçabilité.
2. **Autorisation contextuelle (ABAC)** — la décision d'accès se prend sur des attributs, pas sur un rôle seul. Les règles réelles sont du type : *un enseignant voit les notes des seules classes où il enseigne, pour l'année en cours* ; *un professeur principal voit toutes les matières de sa classe* ; *un parent voit ses enfants, et uniquement les rubriques dont il est destinataire déclaré*. Attributs porteurs de la décision : classe, matière, année scolaire, site, lien de responsabilité, période d'activité. Les politiques sont déclaratives et centralisées, jamais dispersées dans le code des modules.
3. **Cloisonnement absolu** — certaines données sortent du système de rôles et relèvent d'une liste nominative d'accès :
   - dossier médical et infirmerie ;
   - dossier psychosocial ;
   - signalements de protection de l'enfance ;
   - dossier disciplinaire en cours d'instruction ;
   - éléments de paie individuels.
   Pour ces données : **journal d'accès inaltérable**, consultation motivée, et alerte au responsable en cas d'accès anormal. Un chef d'établissement ne doit pas avoir accès par défaut au contenu d'un signalement le concernant.
4. **Administration des comptes et des rôles** — assurée par l'établissement lui-même dans le back-office, sans intervention de l'éditeur. Voir ci-dessous.

**Administration des comptes et des rôles (back-office établissement)**

| Fonction | Détail |
| :-- | :-- |
| Création de compte | Individuelle ou en masse par import ; l'invitation part par SMS avec un lien à usage unique |
| Rôles types | Direction, censeur / éducateur, enseignant, professeur principal, économe / caissier, secrétariat, infirmier, référent protection de l'enfance, référent informatique, chauffeur, parent, élève |
| **Rattachement, pas seulement rôle** | Un rôle sans périmètre ne veut rien dire : chaque affectation lie une personne à un rôle **et** à un périmètre (site, cycle, classes, matières, année). C'est ce couple qui alimente l'ABAC |
| Rôles cumulés | Cas normal, pas exception : une même personne peut tenir la scolarité **et** la pédagogie, ou être enseignante **et** professeur principal. Les capacités s'additionnent, les cloisonnements ne se contournent jamais. L'interface s'adapte en conséquence — voir 1.12 |
| Délégation temporaire | Un intérim borné dans le temps, avec date de fin obligatoire et expiration automatique — le cas du censeur qui remplace le proviseur absent |
| Cycle de vie | Suspension immédiate, désactivation à date, révocation de session en cours. **Le départ d'un enseignant en cours d'année doit couper l'accès le jour même** |
| Bascule d'année | Les affectations sont rattachées à une année scolaire : elles expirent avec elle et sont reconduites explicitement, jamais par défaut |
| Réinitialisation | Auto-dépannage par OTP SMS ; c'est le premier motif de sollicitation du support (S15) |
| Revue des accès | Liste des comptes actifs et de leurs périmètres, exportable, à passer en revue à chaque rentrée |
| Journal | Toute création, modification ou suppression d'habilitation est tracée avec son auteur |

## 1.9 Protection de l'enfance (safeguarding)

C'est le domaine où une erreur de conception a les conséquences les plus graves, humaines comme juridiques. Il fait l'objet d'un module dédié et cloisonné, jamais d'une fonctionnalité annexe d'un autre service.

**Module dédié, cloisonné, et à circuit humain obligatoire**

- Registre de signalement accessible à tout membre du personnel, y compris de façon confidentielle.
- Circuit de traitement nommé : référent protection de l'enfance désigné dans l'établissement, délais de traitement, escalade vers la direction puis vers les autorités compétentes.
- Traçabilité intégrale et non modifiable de chaque action.
- Politique de conservation spécifique, distincte du dossier scolaire.
- Vérification des antécédents du personnel au recrutement (module RH) et registre des habilitations à encadrer des mineurs.
- Charte de conduite et procédure applicable aux communications adulte-mineur **dans la plateforme elle-même** : la messagerie enseignant-élève doit être journalisée, non supprimable, et visible d'un tiers. Une plateforme scolaire qui offre un canal privé non tracé entre un adulte et un mineur crée un risque qu'elle sera tenue de justifier.

**Ce que l'IA peut faire ici** : agréger des signaux (absences + chute de notes + visites répétées à l'infirmerie) et **alerter une personne nommée**. Rien d'autre. Pas de qualification, pas de score de risque affiché, pas de décision, pas de notification automatique aux familles. Voir Partie 5.4.

## 1.10 Conformité et protection des données

Le RGPD n'est pas le texte applicable. Pour la Côte d'Ivoire :

- Loi n° 2013-450 du 19 juin 2013 relative à la protection des données à caractère personnel, avec l'ARTCI comme autorité de contrôle, dotée d'un pouvoir réglementaire et d'un pouvoir de sanction.
- Décret n° 2015-19 du 4 février 2015 fixant les modalités de dépôt des déclarations et de demande d'autorisation pour le traitement des données à caractère personnel : la plateforme et chaque établissement client devront accomplir ces formalités.
- Régime renforcé pour les **données sensibles** (santé, données biométriques si reconnaissance faciale envisagée — à éviter en V1) et pour les **mineurs**.

**Un texte de révision de cette loi était en discussion ; vérifier l'état du droit à date avant tout engagement.**

**Ce que le produit doit embarquer**

| Exigence | Implémentation |
| :-- | :-- |
| Base légale par traitement | Registre des traitements intégré, exportable |
| Information des personnes | Mentions générées, consentement horodaté du responsable légal |
| Durées de conservation | Politique par catégorie de donnée, purge automatique, archivage légal séparé |
| Droits des personnes | Accès, rectification, opposition, portabilité — outillés, pas manuels |
| Localisation des données | Question à trancher : hébergement régional (Abidjan, Dakar) ou UE ? Le transfert hors du territoire est encadré |
| Sous-traitance | Contrat de sous-traitance type entre l'éditeur et l'établissement, l'établissement restant responsable de traitement |
| Journal d'accès | Inaltérable, sur les catégories sensibles au minimum |
| Notification de violation | Procédure et délai définis |

**Point spécifique IA** : l'utilisation de données d'élèves pour entraîner ou affiner un modèle est un traitement distinct, qui nécessite sa propre base légale et son propre consentement. Aucune promesse commerciale du type « le système apprend de vos données » ne doit être faite tant que ce cadre n'est pas contractuellement établi.

## 1.11 Country pack : la localisation par configuration

Un `country_pack` est un ensemble de données de référence versionnées, chargé au provisionnement d'un tenant. **Aucune logique métier ne doit dépendre du pays autrement que par ce pack.**

Contenu d'un country pack :

- structure des cycles et niveaux, avec libellés FR/EN ;
- découpage de l'année (trimestres/semestres/terms) et calendrier type ;
- référentiel d'évaluation (échelle, conversion, formules, gabarit de bulletin) ;
- examens officiels et leur calendrier ;
- référentiel des séries et filières ;
- plan comptable et régime fiscal ;
- opérateurs de paiement disponibles ;
- autorité de protection des données et formalités ;
- ministères de tutelle et formats de remontée statistique ;
- devise, format de date, format de numéro de téléphone, langues ;
- vocabulaire métier (voir Annexe A).


## 1.12 Composition de l'interface selon les habilitations

**Il n'y a pas d'« interface du censeur » ni d'« interface de l'économe ».** Il y a un back-office unique dont la surface se compose à partir des capacités effectives de la personne connectée. C'est une exigence structurante, pas un raffinement d'ergonomie.

**Pourquoi** — la répartition des fonctions varie énormément d'un établissement à l'autre, à segment identique. Dans un collège privé de 400 élèves, une seule personne tient la scolarité, la pédagogie et l'emploi du temps. Dans un groupe scolaire de 3 000 élèves, ce sont trois personnes et parfois trois services distincts. Un produit qui impose un découpage fixe oblige le petit établissement à jongler entre plusieurs comptes — avec le partage de mots de passe qui s'ensuit — et force le grand à accorder des droits trop larges.

### Modèle

- Chaque service du catalogue expose un ensemble de **capacités** nommées par verbe métier, pas par opération technique : `scolarite.inscription.valider`, `pedagogie.edt.publier`, `finance.encaissement.saisir`, `evaluation.note.saisir`, `evaluation.bulletin.publier`.
- Un **rôle** est un ensemble nommé de capacités. Les rôles sont livrés sous forme de **modèles préconfigurés par segment**, que l'établissement peut cloner et ajuster lui-même, sans intervention de l'éditeur.
- Une **affectation** lie une personne à un rôle **et** à un périmètre (site, cycle, classes, matières, année) — voir 1.8.
- Les capacités effectives d'une personne sont l'**union** de ses affectations. L'interface se compose à partir de cette union.

### Règles de composition

| Élément | Règle |
| :-- | :-- |
| Navigation | Un domaine n'apparaît que si la personne détient au moins une capacité dedans. **Pas de menu grisé** : un menu visible mais inaccessible est du bruit et une invitation à réclamer des droits |
| Densité | Deux ou trois domaines s'affichent à plat ; au-delà de cinq, regroupement par famille. La navigation d'un directeur qui détient tout ne peut pas être la même liste que celle d'un enseignant qui détient une chose |
| Écran d'accueil | Un utilisateur mono-domaine atterrit directement dans son domaine, jamais sur un tableau de bord presque vide. Un utilisateur multi-domaines reçoit un tableau de bord composé des blocs de chaque domaine autorisé, réordonnables |
| Écrans partagés | Une **fiche élève unique**, dont les onglets et les actions varient : l'éducateur y voit la discipline, l'économe le solde, l'enseignant les notes de ses seules matières, l'infirmier rien du tout sauf habilitation nominative. Une seule fiche, plusieurs vues — pas quatre écrans concurrents |
| Recherche et exports | Ne portent que sur le périmètre autorisé. Un export ne doit jamais être une porte dérobée vers des données que l'écran refuse d'afficher |
| Notifications | Une personne ne reçoit que les alertes des domaines qu'elle détient. Le cumul de rôles ne doit pas produire un cumul de bruit : regroupement par domaine |
| Absence de capacité | Message explicite renvoyant vers l'administrateur de l'établissement, jamais une page vide ni une erreur technique |

### Modèles de rôles livrés par segment

Le catalogue de modèles est un élément du paramétrage, ajustable par l'établissement. Il varie selon le segment **et selon la taille**.

| Segment | Modèles fournis |
| :-- | :-- |
| Préscolaire et primaire | Directeur (toutes capacités du site) ; Instituteur ; **Secrétaire-économe** (scolarité + finances) ; Personnel de sortie |
| Secondaire, structure réduite | Fondateur / Proviseur ; **Censeur — scolarité + pédagogie + emploi du temps** ; Éducateur (vie scolaire) ; Économe ; Enseignant ; Professeur principal |
| Secondaire, structure étoffée | Proviseur ; Directeur des études (pédagogie + emploi du temps) ; Chef de scolarité (inscriptions, dossiers, examens) ; Censeur (vie scolaire, discipline) ; Économe ; Comptable ; Responsable RH ; Enseignant ; Professeur principal ; Documentaliste ; Surveillant d'internat |
| Technique et professionnel | Les précédents + **Chef de travaux** (ateliers, plateaux, sécurité) ; Responsable des stages et de l'alternance |
| Supérieur | Directeur ; Responsable pédagogique de filière ; Chef de scolarité ; Responsable des examens et délibérations ; Agent comptable ; Responsable recherche ; Responsable relations entreprises ; Enseignant-chercheur ; Vacataire |

**Le cas cité en exemple est le cas nominal** : dans le secondaire, le modèle « Censeur — scolarité + pédagogie » et le modèle « Directeur des études — pédagogie seule » coexistent dans le catalogue. L'établissement choisit celui qui correspond à son organisation, ou compose le sien.

### Limite : ce qui ne s'attribue jamais par un rôle

Les capacités relevant du cloisonnement de 1.8 — dossier médical, dossier psychosocial, signalements de protection de l'enfance, éléments de paie individuels — **ne sont pas ajoutables à un modèle de rôle**. Elles s'attribuent nominativement, une personne à la fois, avec motif et traçabilité. Sans cette exception, il suffirait d'ajouter une capacité à un rôle largement distribué pour ouvrir l'accès au dossier psychosocial de tous les élèves.

### Conséquences techniques

- **Le serveur est la seule autorité.** L'interface masque, l'API refuse. Un élément d'interface masqué n'est pas une protection : chaque appel revérifie la capacité et le périmètre.
- Le front-end Nuxt compose sa navigation à partir d'un point d'entrée `/me/capabilities` renvoyant les capacités effectives et leurs périmètres. **Aucune liste de rôles n'est codée en dur côté front** — sinon chaque nouveau modèle de rôle exige un déploiement.
- Les capacités sont **versionnées** : une capacité introduite par une mise à jour n'est jamais accordée automatiquement aux rôles existants. Elle est proposée à l'administrateur de l'établissement, qui décide.
- Le cumul rend les tests combinatoires. On ne teste pas toutes les combinaisons possibles mais un jeu de **personas** correspondant aux cumuls réellement observés chez les établissements pilotes — à collecter pendant la phase de découverte (8.4).
- Les affectations expirant avec l'année scolaire (1.2), la composition de l'interface change à la bascule d'année. Une personne dont les affectations n'ont pas été reconduites doit voir un message clair, pas une interface vide.

---

# PARTIE 2 — CATALOGUE DES SERVICES

## 2.1 Principe : un catalogue unique, des variations explicites

La tentation, en décrivant une plateforme multi-niveaux, est de rédiger un catalogue par segment — puis de recopier les mêmes services d'un segment à l'autre en les qualifiant d'« enrichis » sans dire en quoi. Ce document pose au contraire un **socle commun de 15 services** activés pour tous les segments, plus des **modules de segment**. Chaque service commun porte une rubrique « variations » qui dit précisément ce qui change d'un niveau à l'autre.

Notation de priorité : **MVP** = version 1 ; **V2** = 6-12 mois ; **V3** = au-delà ; **Partenaire** = à ne pas construire soi-même.

## 2.2 Socle commun — 15 services

### S01 · Direction et pilotage
**Objet** — Pilotage de l'établissement, documents administratifs, calendrier, dossiers élèves.
**Fonctions clés** — Tableau de bord (effectifs, assiduité, réussite, trésorerie, créance État) ; dossier élève complet et historisé ; génération de documents (certificat de scolarité, attestation, bulletin, convocation) avec gabarits par pays ; calendrier scolaire ; annuaire ; réunions et PV ; remontées statistiques à la tutelle (DRENA/DDENA en Côte d'Ivoire, GES au Ghana).
**Variations** — Supérieur : ajout des instances (conseil d'administration, conseil scientifique) et du dossier d'accréditation CAMES.
**Priorité** — MVP (dossier élève, documents, tableau de bord de base).

### S02 · Scolarité, inscriptions et réinscriptions
**Objet** — Cycle de vie administratif de l'élève, de la candidature au départ.
**Fonctions clés** — Campagne d'inscription et de réinscription ; dossier de pièces avec contrôle de complétude ; frais d'inscription ; affectation en classe ; certificat de transfert et radiation ; **rattachement au circuit d'affectation de l'État** ; carte scolaire / student ID avec QR ; gestion des départs et de la déscolarisation.
**Variations** — Supérieur : candidature en ligne, concours d'entrée, équivalences, VAE. Anglophone : admission par placement centralisé (au Ghana, la sélection vers le second cycle passe par le Computerized School Selection and Placement System).
**Priorité** — MVP.

### S03 · Pédagogie, programmes et emploi du temps
**Objet** — Programmes, progressions, cahier de textes, emploi du temps.
**Fonctions clés** — Référentiel de programmes par niveau et matière, aligné sur le curriculum national ; progressions et séquences ; cahier de textes numérique ; devoirs ; bibliothèque de ressources ; emploi du temps avec moteur de contraintes (salles, services enseignants, groupes, dédoublements, sites multiples).
**Variations** — Primaire : logique de compétences, un enseignant polyvalent. Secondaire : multi-enseignants, séries. Technique : plateaux techniques et rotation d'ateliers. Supérieur : maquettes LMD et crédits, mutualisations inter-filières.
**Priorité** — MVP (cahier de textes, devoirs, EDT en saisie manuelle) ; V2 (génération automatique d'EDT).

### S04 · Évaluations, notes et bulletins
**Objet** — Cycle complet d'évaluation jusqu'au bulletin.
**Fonctions clés** — Saisie de notes par lot, tolérante aux coupures ; **moteur de calcul piloté par le référentiel d'évaluation** (1.4) ; appréciations ; bulletin PDF conforme au gabarit du pays ; rang et mentions ; historique et graphiques ; publication multicanale.
**Variations** — Voir 1.4 : le calcul, le vocabulaire et le document diffèrent radicalement entre zone francophone et zone anglophone.
**Priorité** — MVP. **C'est la fonctionnalité qui fait acheter.**

### S05 · Conseil de classe, passage et constitution des classes
**Objet** — Voir 1.5.
**Priorité** — MVP pour le conseil de classe et la décision de passage ; V2 pour la constitution automatique des classes.

### S06 · Vie scolaire : présence, discipline, sécurité
**Objet** — Appel, absences, retards, discipline, mouvements d'élèves.
**Fonctions clés** — Appel par séance en un geste, sur une page très légère ; justification d'absence par le responsable ; notification immédiate par SMS ; sanctions et registre d'incidents ; conseil de discipline ; autorisations de sortie ; **contrôle de sortie avec vérification de la personne autorisée à récupérer l'élève** (1.1) ; statistiques d'assiduité.
**Variations** — Primaire : appel par demi-journée, remise à la personne autorisée. Secondaire : appel par cours, régime d'externat/demi-pension/internat. Supérieur : émargement par UE, contrôle d'assiduité pour les boursiers.
**Priorité** — MVP.

### S07 · Finances, facturation et recouvrement
**Objet** — Frais de scolarité, encaissement, comptabilité, trésorerie.
**Fonctions clés** — Grille tarifaire par niveau et régime ; échéanciers ; **facturation par foyer avec quotes-parts** ; remises (fratrie, personnel, mérite, social) ; encaissement **mobile money** multi-opérateurs et espèces avec reçu numéroté ; relances multicanales ; **suivi des élèves affectés et de la créance sur l'État** (1.6) ; bourses et prises en charge ; comptabilité analytique et export **SYSCOHADA révisé** ; états de trésorerie.
**Variations** — Anglophone : tarification par term, boarding fees, levies. Supérieur : frais différenciés, droits d'inscription, prestations de formation continue.
**Priorité** — MVP. **C'est la fonctionnalité qui fait payer.**

### S08 · Ressources humaines et paie
**Objet** — Personnel enseignant et non enseignant.
**Fonctions clés** — Dossiers, contrats, diplômes et **agrément/autorisation d'enseigner** ; **vérification des antécédents et habilitation à encadrer des mineurs** (1.9) ; services et charges horaires ; vacataires et heures supplémentaires ; congés, absences et **remplacements** ; pointage ; préparation de paie avec cotisations **CNPS** et retenues fiscales ; évaluation et formation.
**Variations** — Supérieur : statuts d'enseignant-chercheur, grades et **listes d'aptitude CAMES**, décharges, vacations.
**Priorité** — V2 pour la paie ; MVP pour le dossier personnel et les remplacements.

### S09 · Communication et relations familles
**Objet** — Voir 1.7.
**Fonctions clés** — Messagerie **journalisée** ; circulaires ; notifications par événement ; agenda ; rendez-vous parent-enseignant ; sondages ; **console de routage et budget SMS** ; modèles de messages bilingues.
**Priorité** — MVP.

### S10 · Santé scolaire et infirmerie
**Objet** — Suivi médical et premiers soins.
**Fonctions clés** — Fiche médicale (allergies, traitements, vaccinations, groupe sanguin, drépanocytose, asthme) ; registre de passage à l'infirmerie ; protocole d'urgence et personne à prévenir, consultables en un écran et imprimables par classe ; campagnes de vaccination et de déparasitage ; alertes épidémiques (paludisme, choléra, méningite en zone sahélienne) ; **accessible uniquement à la liste nominative habilitée** (1.8).
**Priorité** — V2 (sauf fiche d'urgence et allergies : MVP).

### S11 · Protection de l'enfance et accompagnement psychosocial
**Objet** — Voir 1.9.
**Fonctions clés** — Signalement confidentiel ; circuit et référent nommés ; suivi psychosocial cloisonné ; harcèlement ; accompagnement du handicap ; liaison avec les services sociaux et les ONG partenaires ; climat scolaire anonymisé.
**Priorité** — MVP pour le registre de signalement et le circuit (obligation morale et exposition juridique) ; V2 pour le reste.

### S12 · Restauration
**Objet** — Cantine et restauration scolaire.
**Fonctions clés** — Menus ; inscription et régimes (allergies, végétarien, halal) ; facturation et prépaiement ; stocks et approvisionnement ; hygiène ; **gestion des cantines subventionnées** (programmes nationaux et partenaires internationaux) avec reporting dédié ; fréquentation.
**Priorité** — V2.

### S13 · Transport scolaire
**Objet** — Ramassage et suivi.
**Fonctions clés** — Itinéraires et arrêts ; inscription ; liste embarquée consultable et imprimable ; confirmation de montée et de descente ; notification aux familles ; suivi GPS ; facturation ; conformité et entretien des véhicules ; incidents.
**Priorité** — V2.

### S14 · Patrimoine, équipements, maintenance et sécurité
**Objet** — Bâtiments, matériel, sécurité des personnes et des biens.
**Fonctions clés** — Inventaire ; tickets d'intervention avec photo ; maintenance préventive ; consommables ; **groupes électrogènes, onduleurs, panneaux solaires, forage et château d'eau** ; contrôle d'accès ; exercices d'évacuation ; conformité incendie.
**Priorité** — V2.

### S15 · Système d'information de l'établissement
**Objet** — Comptes, équipements numériques, support. Ce service existe à tous les niveaux, pas seulement dans le supérieur : une école primaire gère elle aussi des comptes, des tablettes et des mots de passe oubliés.
**Fonctions clés** — Gestion des comptes et des réinitialisations (le cas d'usage n°1 du support) ; parc de tablettes et d'ordinateurs ; salle informatique ; connectivité et forfaits data ; sauvegardes ; **support de niveau 1 assuré par un référent interne**, avec escalade vers l'éditeur.
**Priorité** — MVP pour la gestion des comptes et le support ; V2 pour le parc.

## 2.3 Modules par segment

### 2.3.1 Préscolaire et maternelle

| Module | Fonctions |
| :-- | :-- |
| Journal de vie quotidienne | Repas, sieste, propreté, humeur, incidents — partagé aux familles quotidiennement |
| Ratio d'encadrement | Suivi du taux d'encadrement réglementaire par section et par moment de la journée |
| Développement | Observation par domaine d'apprentissage plutôt que notation |
| Album photo sécurisé | Consentement à l'image explicite et révocable par responsable, filigrane, pas de diffusion externe |
| Remise de l'enfant | Contrôle systématique de la personne autorisée, avec photo — critique à cet âge |

### 2.3.2 Primaire

Socle commun + évaluation par compétences + **suivi des acquis fondamentaux** (lecture, écriture, calcul) + préparation aux examens de fin de cycle et à l'affectation vers le secondaire + cantine subventionnée + coopérative scolaire.

### 2.3.3 Secondaire général

Socle commun + les modules suivants :

| Module | Fonctions clés |
| :-- | :-- |
| **Examens officiels** | Inscription aux examens nationaux, examens blancs, salles et surveillance, statistiques de réussite par série. Côte d'Ivoire : BEPC, BAC, gérés par la Direction des Examens et Concours. Anglophone : BECE en fin de premier cycle et WASSCE en fin de second cycle, organisés par le WAEC, avec transmission des notes de contrôle continu au conseil d'examen |
| **Séries et filières** | Choix de série, conditions d'accès, changement de série, coefficients par série |
| **Orientation** | Fiches métiers et filières du pays, vœux, entretiens, forums, passerelles vers le technique, information sur les bourses |
| **Portail élève** | Emploi du temps, notes, devoirs, ressources — PWA très légère, utilisable sur un smartphone d'entrée de gamme et une connexion lente |
| **Internat** | Chambres, appel du soir, sorties de week-end, incidents, facturation, communication avec les familles éloignées |
| **CDI / bibliothèque** | Catalogue, prêt, ressources numériques, retards |
| **Vie associative et sport** | Clubs, association sportive, compétitions inter-établissements, **système de prefects / délégués** |

### 2.3.4 Secondaire technique et professionnel

Segment volumineux et souvent négligé par les plateformes généralistes. Il relève en Côte d'Ivoire d'un ministère distinct de celui de l'éducation nationale, avec ses propres référentiels et ses propres remontées.

| Module | Fonctions clés |
| :-- | :-- |
| Ateliers et plateaux techniques | Réservation, rotation des groupes, sécurité, habilitations, consommables et matières d'œuvre |
| Alternance et apprentissage | Contrat, maître d'apprentissage, alternance des périodes, rémunération |
| Stages en entreprise | Convention tripartite, carnet de suivi, visite de stage, évaluation par le tuteur entreprise, rapport et soutenance |
| Référentiels de compétences professionnelles | Évaluation par compétence certifiante, livret de suivi |
| Équipements | Machines, contrôle réglementaire, EPI, registre de sécurité |
| Relations entreprises | Répertoire, conventions, taxe d'apprentissage locale le cas échéant |

### 2.3.5 Supérieur (université, grande école, BTS/IUT)

Socle commun + les modules ci-dessous, calés sur les référentiels régionaux (CAMES, LMD) et non sur des référentiels européens.

| Module | Contenu localisé |
| :-- | :-- |
| Gouvernance | Conseils statutaires, **agrément du ministère de l'enseignement supérieur**, reconnaissance et accréditation CAMES, qui vaut reconnaissance dans l'espace des pays africains francophones membres, via le programme de reconnaissance et d'équivalence des diplômes |
| Scolarité | Candidature, concours, **système LMD** (adopté en Côte d'Ivoire par décret en 2009 et arrêté en 2011, encore partiellement coexistant avec l'ancien système), crédits, équivalences, supplément au diplôme |
| Examens et délibérations | Compensation, capitalisation, jurys, PV, rattrapages, aménagements, anti-plagiat |
| Recherche | Laboratoires, projets, publications, **listes d'aptitude et grades CAMES**, bailleurs régionaux et internationaux (au lieu d'ANR/ERC) |
| International | Mobilité intra-africaine et Nord-Sud, doubles diplômes, accueil, visas |
| Insertion professionnelle | Stages, alumni, forums, enquêtes d'insertion, entrepreneuriat |
| Formation continue | Catalogue, sessions courtes, facturation entreprise, certification |
| Vie étudiante | Logement, bourses d'État, restauration, santé, associations, sport |
| Bibliothèque universitaire | Catalogue, bases documentaires, dépôt de mémoires et thèses, accès distant |
| Qualité | Auto-évaluation, préparation des dossiers d'accréditation, enquêtes de satisfaction |

### 2.3.6 Services d'établissement transverses

| Service | Pourquoi il compte | Priorité |
| :-- | :-- | :-- |
| **Économat / coopérative scolaire** | Manuels, uniformes, fournitures, photos scolaires : ventes, stock, marge. Source de revenu réelle des établissements | V2 |
| **Sorties et voyages scolaires** | Autorisation parentale tracée, liste d'appel hors les murs, budget, assurance, encadrants | V2 |
| **Sport et EPS** | Évaluation EPS, aptitude médicale, association sportive, compétitions | V2 |
| **APE / COGES / PTA** | Instance avec bureau, cotisations, budget propre, réunions, projets financés | V2 |
| **Assurances** | Assurance scolaire élève, responsabilité civile, accidents du travail, sinistres | V2 |
| **Recrutement d'élèves et marketing** | Pour un établissement privé, le taux de réinscription et le recrutement sont des indicateurs vitaux — dès le primaire, pas seulement dans le supérieur | V2 |
| **Décrochage et déscolarisation** | Détection, relance, médiation familiale, réinsertion, reporting à la tutelle | V2 |
| **Alumni K-12** | Réseau des anciens, source de dons et de réputation pour les établissements privés | V3 |

## 2.4 Récapitulatif du catalogue

| Bloc | Nombre de services | Dont MVP |
| :-- | :-- | :-- |
| Socle métier (Partie 1) | 11 fondations transverses | 11 |
| Socle commun de services (2.2) | 15 | 9 |
| Préscolaire | 5 modules | 0 |
| Primaire | 4 modules | 1 |
| Secondaire général | 7 modules | 2 |
| Secondaire technique | 6 modules | 0 |
| Supérieur | 10 modules | 0 |
| Transverses établissement | 8 modules | 0 |

**Total : 55 services et modules**, auxquels s'ajoutent les 11 fondations transverses du socle métier. Périmètre du MVP : les 11 fondations et 12 modules.

---

# PARTIE 3 — ARCHITECTURE TECHNIQUE

## 3.1 Philosophie : Monolith-First, Microservice-Ready

Démarrer par un monolithe modulaire bien structuré, découpable ensuite en microservices lorsque le besoin de scalabilité indépendante apparaît. Les raisons : complexité opérationnelle disproportionnée au démarrage, overhead réseau inutile quand tout tient sur un serveur, impossibilité de définir de bonnes frontières de service sans retour du terrain, coût d'infrastructure multiplié. Les frontières modulaires du monolithe sont les futures frontières de microservices.

**La condition à respecter** pour que l'extraction future soit indolore est que **les modules ne partagent jamais de transaction de base de données**. Un module qui écrit dans le schéma d'un autre module rend l'extraction impossible, quelle que soit la propreté des traits Rust. Règle : `finance` ne fait pas de `SELECT` dans `scolarite.eleves` ; il appelle l'interface du module `scolarite`.

## 3.2 Stack technologique

| Couche | Choix | Motif |
| :-- | :-- | :-- |
| Web (back-office, portails, site public) | **Nuxt 4** | Rendu serveur et pages statiques pour la légèreté et le référencement, hydratation partielle, une seule codebase pour le back-office, le portail parent et le portail élève |
| Mobile | **Nuxt 4 en application web installable**, aspect et navigation d'application native | Pas de codebase séparée à maintenir au démarrage. Rien à installer depuis un magasin d'applications, aucune mise à jour à pousser aux utilisateurs — décisif pour les parents |
| Passage en application native | **Capacitor, phase ultérieure** | Enveloppe la même base Nuxt le jour où l'on a besoin de notifications natives, de la caméra en usage intensif ou d'une présence dans les magasins d'applications. Décision reportée, pas écartée |
| Desktop | **Hors périmètre** | Le web suffit |
| Monolithe applicatif | **Rust / Actix Web** | Performance, faible empreinte mémoire, sécurité mémoire, adapté à des ressources serveur contraintes |
| Sidecar IA | **FastAPI (Python)**, **optionnel au déploiement** | Écosystème IA Python, isolé du chemin critique. Un établissement doit pouvoir tourner sans aucune fonctionnalité IA |
| Base de données | **PostgreSQL 18** | Schéma par domaine, Row Level Security pour l'isolation tenant |
| Cache, sessions, files | **Valkey** | Compatible Redis, gouvernance ouverte, pas de risque de changement de licence |
| Bus de messages | **Reporté après le MVP** | En monolithe mono-binaire, une table `outbox` PostgreSQL + un worker suffisent et coûtent bien moins cher à opérer. Un bus dédié devient pertinent au moment du découplage |
| Stockage objet | **Garage** (API S3) | Auto-hébergeable, très faible empreinte, conçu pour des nœuds hétérogènes et une réplication géographique — cohérent avec un hébergement régional. Interface S3 standard, donc migration possible vers un S3 managé sans réécriture |
| Passerelles de communication | SMS sortant et entrant, WhatsApp Business API | Voir 3.4 |
| Passerelle de paiement | Agrégateur mobile money derrière une interface interne | Voir 3.5 |
| CI/CD | **Minimal** : build, tests, migration de schéma, déploiement en une commande | Pas de chaîne élaborée au démarrage. La seule exigence non négociable est la migration de schéma automatisée et réversible |
| Supervision | **OpenTelemetry** (traces, métriques, journaux) | Instrumentation standard et neutre : le choix du collecteur et du backend reste ouvert et changeable sans retoucher le code |
| Sauvegardes | Quotidiennes, chiffrées, **restauration testée** | Voir 3.6. C'est le seul point où l'économie de moyens est interdite |

### Pourquoi Rust en façade plutôt que FastAPI

FastAPI est un excellent framework, mais le placer en façade devant la logique métier créerait un goulot d'étranglement : latence supplémentaire par requête (sérialisation Python, GIL, boucle asyncio) là où Actix Web répond sous la milliseconde ; empreinte mémoire d'un ordre de grandeur supérieure ; concurrence limitée par le GIL sur les tâches CPU. Sur des serveurs à ressources contraintes et avec un prix de vente par élève bas, chaque Mo de RAM et chaque milliseconde comptent. Python reste indispensable, mais cantonné au sidecar IA, appelé en HTTP interne uniquement pour les requêtes d'inférence.

### Conséquence du choix Nuxt sur le back-end

Le front-end étant entièrement découplé, le monolithe Rust n'expose que des API. Deux points à cadrer dès le départ : la **session** (jeton en cookie `HttpOnly` plutôt qu'en stockage navigateur, pour les postes partagés dans les établissements) et le **rendu des documents** (bulletins, reçus, listes d'appel), qui doit être produit côté serveur en PDF par le monolithe, jamais par le navigateur — la mise en page d'un bulletin ne peut pas dépendre du terminal de l'utilisateur.

## 3.3 Fonctionnement en connexion dégradée

**La plateforme fonctionne en ligne.** Il n'y a pas de mode hors ligne ni de moteur de synchronisation : le coût de conception, de test et de support d'un tel sous-système (résolution de conflits, horloges non fiables, purge des caches sensibles) est disproportionné au démarrage. La décision est réexaminable une fois le produit installé.

**Ce que cela impose en contrepartie**

- **Budget de poids par écran.** Les écrans utilisés en classe (appel, saisie de notes) sont les plus légers de la plateforme : pas de dépendance lourde, pas d'image inutile, données paginées.
- **Écriture idempotente et reprise.** Toute soumission porte une clé d'idempotence. Une coupure au mauvais moment ne crée jamais de doublon et n'efface jamais la saisie en cours : le formulaire est restitué tel quel au retour, et l'envoi est rejoué.
- **Enregistrement au fil de l'eau.** L'appel et la saisie de notes s'enregistrent par petits lots au fur et à mesure, pas en un envoi unique en fin de séance. Perdre le réseau à la dernière ligne ne doit pas coûter quarante saisies.
- **États explicites.** L'utilisateur voit à tout moment si sa saisie est enregistrée sur le serveur ou en attente. Aucune ambiguïté sur ce point, c'est là que se perd la confiance.
- **Procédure papier de secours.** Toutes les listes critiques — appel, embarquement transport, fiches d'urgence, personnes autorisées à récupérer un élève — sont imprimables à l'avance par classe. C'est le mode dégradé assumé pour la journée où le réseau tombe, et il doit être documenté dans la formation des établissements, pas découvert le jour même.

**Ce qu'il faut vérifier auprès des pilotes** : la couverture réseau réelle dans les salles de classe, en particulier aux étages et dans les bâtiments en dur. Si un établissement pilote n'a pas de réseau utilisable en classe, l'appel s'y fera sur papier puis en saisie différée au bureau — c'est un compromis acceptable, mais il doit être identifié avant la vente, pas après.

## 3.4 Communication : passerelles et coûts

- **SMS** : agrégateur multi-opérateurs avec bascule automatique, accusés de réception, gestion des numéros invalides, respect des fenêtres horaires. Coût unitaire suivi par établissement.
- **SMS entrant** : numéro long virtuel fourni par l'agrégateur, analyse du mot-clé, réponse automatique en moins de 160 caractères. Contrôle d'accès par le numéro appelant : un parent ne consulte que ses enfants, et un numéro inconnu reçoit une réponse générique sans donnée personnelle.
- **WhatsApp Business API** : modèles de message pré-approuvés, notion de fenêtre de conversation, coût par conversation.
- **Moteur de rendu de message** : un événement métier produit un message décliné par canal et par langue, avec troncature intelligente et repli en cascade (push → WhatsApp → SMS).

## 3.5 Paiement : architecture mobile money

Les agrégateurs centralisent les opérateurs en une seule API ; CinetPay est le plus utilisé en Côte d'Ivoire et couvre Wave, Orange Money, MTN MoMo, Moov ainsi que les cartes. PayDunya couvre également plusieurs marchés d'Afrique de l'Ouest et du Centre. Le choix agrégateur contre intégration directe est une décision d'architecture structurante.

**Recommandation** : démarrer via un agrégateur, mais **isoler l'agrégateur derrière une interface interne dès le premier jour** afin de pouvoir en changer ou passer en direct sur les gros volumes sans toucher la logique métier.

**Exigences non négociables du module de paiement**

| Exigence | Raison |
| :-- | :-- |
| **Idempotence** stricte des initiations et des webhooks | Les confirmations arrivent en retard, en double, ou jamais |
| **Machine à états** explicite de la transaction | `initiée → en attente → confirmée / échouée / expirée / remboursée` |
| **Réconciliation quotidienne** automatique | Écart entre le journal de la plateforme et le relevé de l'opérateur : c'est ici que naissent les litiges |
| **Encaissement espèces** avec caisse et arrêté quotidien | Une part majoritaire des paiements reste en espèces dans beaucoup d'établissements |
| **Reçu numéroté, séquentiel, infalsifiable** | Exigence comptable et culturelle |
| **Aucun paiement supprimable** | Annulation par écriture inverse uniquement |
| Multi-devises XOF / XAF / GHS / NGN / KES | Extension régionale |

## 3.6 Déploiement en contexte contraint

- **Cloud d'abord**, hébergement régional à privilégier pour la latence et pour la question de la localisation des données (8.2).
- **Pas de serveur dans l'école** en V1 : l'électricité et la sécurité physique rendent le on-premise ingérable à distance. Le cache local des applications joue ce rôle.
- **Budget de données** : chaque écran a un poids cible. Un parent qui consomme 5 Mo pour consulter un bulletin n'y reviendra pas.
- **Sauvegardes** : quotidiennes, chiffrées, **restauration testée mensuellement**. Un export complet des données de l'établissement doit être disponible à tout moment, dans un format ouvert — c'est aussi un argument de vente contre la peur de l'enfermement.
- **Mode de secours** : impression PDF de toutes les listes critiques (appel, embarquement, urgences), pour la journée où tout tombe.

## 3.7 Sécurité

Authentification par téléphone + OTP, PIN, verrouillage après tentatives ; chiffrement en transit et au repos ; chiffrement applicatif supplémentaire des catégories sensibles ; isolation tenant par Row Level Security **et** par vérification applicative (double barrière) ; journal d'audit inaltérable ; revue d'accès semestrielle ; test d'intrusion avant la mise en production d'un pilote payant.

---

# PARTIE 4 — CANAUX ET APPLICATIONS

## 4.1 Matrice canal × profil

| Profil | Canal principal | Canaux secondaires | Fonctionne sans smartphone ? |
| :-- | :-- | :-- | :-- |
| Direction | Web | App mobile | Non (acceptable) |
| Personnel administratif / économe | Web | — | Non (acceptable) |
| Enseignant | **Application web sur mobile** | Poste partagé en salle des professeurs | Non — l'appareil et la connexion sont un prérequis |
| **Parent** | **SMS sortant + SMS entrant par mot-clé** | WhatsApp, portail web | **Oui — obligatoire** |
| Élève secondaire | Portail web léger | Affichage en classe | Partiellement |
| Étudiant | App / web | — | Non (acceptable) |
| Chauffeur | Application web sur mobile + liste imprimée | SMS | Non |
| Personnel de sortie / gardien | Application web sur mobile + liste imprimée | — | Non |

## 4.2 Espaces

Les espaces décrits ci-dessous ne sont **pas des applications distinctes** : ce sont des compositions de la même interface, produites par les capacités de la personne connectée (1.12). Une personne cumulant deux rôles voit une seule interface réunissant les deux.


**Espace Enseignant** — appel, saisie de notes, cahier de textes, devoirs, consultation du dossier pédagogique, signalement d'incident, messagerie journalisée, emploi du temps, congés. C'est l'écran le plus contraint de la plateforme : conçu pour un appareil d'entrée de gamme et une connexion lente, avec enregistrement au fil de l'eau.

**Espace / canal Parent** — absences et retards en temps réel, notes et bulletin, devoirs, solde et échéancier, paiement mobile money, menus, transport, santé, messagerie, rendez-vous. **Toutes les fonctions critiques existent aussi en SMS : notification sortante pour l'alerte, mot-clé entrant pour la consultation.**

**Portail Élève** (secondaire) — emploi du temps, notes, devoirs, ressources, clubs, orientation. Page très légère, pensée pour un appareil d'entrée de gamme. Les élèves sans smartphone passent par l'affichage en classe et par le canal du responsable légal.

**Espace Étudiant** (supérieur) — scolarité, notes, examens, paiement, bourses, logement, restauration, bibliothèque, associations, stages.

**Espace Direction** — tableau de bord, validations, alertes, consultation. Utilisable sur mobile pour les validations, sur poste pour le pilotage.

**Espace Chauffeur** — itinéraire, liste d'embarquement consultable et imprimable, confirmation montée/descente, incidents.

## 4.3 Fonctions transverses des applications

Tolérance à la connexion lente et reprise après coupure (3.3) ; notifications filtrables par urgence ; **français et anglais dès le socle**, architecture ouverte à d'autres langues ; mode sombre ; accessibilité (contraste, taille de police, lecteur d'écran) ; **budget de poids par écran, suivi comme un indicateur produit** ; liens profonds ; installation sur l'écran d'accueil sans passer par un magasin d'applications.

---

# PARTIE 5 — STRATÉGIE IA

## 5.1 Pourquoi pas « un agent autonome par service »

La tentation est d'annoncer un agent par service — trente et quelques agents, chacun capable d'exécuter la totalité des tâches de son domaine de manière autonome. C'est un mauvais choix, pour trois raisons :

1. **C'est faux techniquement.** Ces 34 agents sont en réalité cinq ou six capacités identiques déclinées par domaine. Les construire séparément multiplie par 34 le coût de développement, d'évaluation et de maintenance, pour une valeur ajoutée nulle.
2. **C'est intenable juridiquement.** L'autonomie complète sur la notation, la discipline, la santé, le psychosocial et la paie expose l'établissement et l'éditeur.
3. **C'est dangereux sur certains sujets.** « Prédire les risques d'échec » et « détecter les indicateurs de maltraitance » sont du profilage de mineurs. Mal fait, cela produit un effet d'étiquetage durable sur des enfants.

La promesse commerciale « 34 agents » peut rester un argument de présentation. **L'architecture, elle, doit être celle de 6 capacités.**

## 5.2 Les six capacités transverses

| Capacité | Ce qu'elle fait | Services servis | Risque |
| :-- | :-- | :-- | :-- |
| **C1 · Rédaction assistée** | Appréciations de bulletin, courriers, circulaires, PV, comptes rendus, traduction FR↔EN | S01, S04, S05, S09 | Faible — sortie relue |
| **C2 · Question-réponse documentaire (RAG)** | Chatbot parent, assistant règlement intérieur, aide administrative, recherche documentaire | S01, S09, bibliothèque | Faible à moyen — hallucination |
| **C3 · Planification sous contraintes** | Emploi du temps, constitution des classes, salles d'examen, tournées de transport, affectation de chambres | S03, S05, examens, S13 | Faible — **et ce n'est pas de l'IA générative : c'est un solveur** |
| **C4 · Analyse et détection de signaux** | Absentéisme, décrochage, anomalies de notation, anomalies comptables, prévision de trésorerie et de fréquentation | S06, S07, S11 | **Élevé quand il s'agit d'élèves** |
| **C5 · Extraction documentaire** | Lecture de pièces d'inscription, extraction de copies manuscrites, reconnaissance de reçus, import de fichiers désordonnés | S02, S04, S07, migration | Moyen — erreur d'extraction |
| **C6 · Assistance à l'apprentissage** | Quiz, fiches de révision, exercices différenciés, aide à la compréhension | Portail élève, S03 | Moyen — exactitude du contenu |

Un « agent » commercial (le « Comptable Virtuel », la « Vie Scolaire ») est simplement une **composition de ces capacités avec un jeu d'outils et de données restreint à un domaine**. C'est un profil de configuration, pas un système distinct.

## 5.3 Gouvernance : trois niveaux d'autonomie

| Niveau | Définition | Domaines |
| :-- | :-- | :-- |
| **A · Autonome** | L'IA exécute et informe | Rappels de paiement, réponses documentaires factuelles, résumés, traduction, propositions d'emploi du temps |
| **B · Proposition validée** | L'IA propose, un humain nommé valide avant effet | Appréciations, courriers officiels, relances, plans de remédiation, constitution des classes |
| **C · Interdit à l'IA** | Décision humaine seule ; l'IA peut au mieux préparer un dossier | **Note finale et décision de passage ; sanction disciplinaire ; qualification d'une situation de protection de l'enfance ; diagnostic ou conseil médical ; décision RH individuelle (licenciement, promotion, paie) ; attribution ou retrait d'une bourse ; exclusion d'un élève** |

**Règles complémentaires**

- Toute sortie d'IA est **étiquetée comme telle** et porte le nom du validateur humain lorsqu'elle produit un effet.
- Aucun **score de risque individuel d'élève** n'est affiché. La capacité C4 produit une **alerte à destination d'une personne nommée**, formulée en faits observables (« 7 absences en 3 semaines, moyenne en baisse de 4 points »), jamais en jugement (« élève à risque, probabilité d'échec 72 % »).
- **Journal d'audit IA** : quelle capacité, quel modèle, quelles données, quelle sortie, quel validateur. Exigence de conformité et de défense.
- **Biais** : le contenu généré doit être évalué sur les stéréotypes de genre, d'origine et de milieu social avant mise en production — sujet particulièrement sensible sur les appréciations de bulletin et l'orientation.
- **Retrait de la promesse d'apprentissage automatique sur les données client** tant que la base légale et le contrat ne l'autorisent pas explicitement (1.10).

## 5.4 Économie de l'inférence

Contrainte issue de P8 : le coût IA par élève et par an doit rester une fraction faible du prix de vente par élève.

- **Routage par tâche** : petit modèle pour la classification, la reformulation et l'extraction simple ; grand modèle réservé au raisonnement et à la rédaction longue.
- **Cache agressif** : les questions des parents sont extrêmement répétitives ; un cache sémantique absorbe l'essentiel du trafic du chatbot.
- **Traitement par lot et en heures creuses** pour les appréciations de bulletin, qui arrivent trois fois par an en pic.
- **Ce qui ne doit pas être de l'IA** : calcul de moyennes, application de barèmes, relances d'échéance, contrôle de complétude d'un dossier, génération d'un bulletin. Ce sont des règles déterministes. Les faire passer par un modèle de langage est plus lent, plus cher et moins fiable — et transforme une opération vérifiable en une opération à auditer.
- **Fonctionnement dégradé** : la plateforme doit rester pleinement opérationnelle avec le sidecar IA éteint.

---

# PARTIE 6 — PRODUIT SAAS ET GO-TO-MARKET

## 6.1 Back-office éditeur

Souvent oublié des documents de conception, il conditionne pourtant la capacité à exploiter le produit au-delà de trois clients.

Provisionnement d'un établissement ; gestion des country packs ; abonnements, facturation et impayés ; activation de modules par tenant ; supervision et alertes ; support avec accès délégué et tracé aux données d'un client (avec consentement) ; gestion des versions et des migrations de schéma ; tableau de bord d'usage par établissement (indicateur d'alerte sur le risque de non-renouvellement).

## 6.2 Onboarding et migration — la première fonctionnalité vendue

- Import depuis Excel avec **assistant de correspondance de colonnes tolérant au désordre** : c'est un cas d'usage direct de la capacité C5.
- Import de photos d'élèves en masse.
- Reprise des soldes de scolarité au 1er jour — le point de bascule le plus délicat.
- **Année de transition** : l'établissement bascule en cours d'année, avec un historique partiel. Ce cas doit être prévu, pas subi.
- Objectif : **un établissement de 800 élèves opérationnel en moins de deux semaines**.
- Formation : le personnel n'est pas nécessairement à l'aise avec l'outil informatique. Prévoir des supports courts, en vidéo, en français simple, et un référent formé sur place.

## 6.3 Modèle économique

- Tarification **par élève actif et par an**, avec paliers dégressifs et prix différencié par segment (le supérieur paie davantage).
- Facturation **en monnaie locale**, encaissable en mobile money, avec un échéancier calé sur celui des rentrées de scolarité de l'établissement — un établissement conventionné n'a pas de trésorerie en janvier.
- **Refacturation du SMS** au coût réel majoré, poste distinct de l'abonnement.
- Modules premium : IA, transport avec GPS, économat, supérieur.
- Option de **partage de revenu sur l'encaissement mobile money** — à évaluer, car cela aligne les intérêts mais peut créer un frein à l'adoption.

## 6.4 Distribution et support

Vente directe à Abidjan sur les groupes scolaires privés (le décideur est le fondateur ou le directeur général, pas le censeur) ; réseau de partenaires intégrateurs locaux pour les autres villes et pays ; support en français et en anglais, avec canal WhatsApp — c'est ce que les clients utiliseront de toute façon ; référence pilote obtenue en échange d'une gratuité de première année contre engagement de témoignage.

## 6.5 Concurrence

Le marché n'est pas vide. Il faut cartographier explicitement : les solutions internationales génériques, les acteurs régionaux existants, les développements sur mesure d'agences locales, les ERP open source adaptés, et surtout **Excel + WhatsApp**, qui est le concurrent réel dans la majorité des établissements. Le combat se gagne sur la migration, le prix en monnaie locale, le canal SMS et le support de proximité — pas sur le nombre d'agents IA.

---

# PARTIE 7 — MVP ET FEUILLE DE ROUTE

## 7.1 Critère de sélection du MVP

Un module entre dans le MVP s'il satisfait l'un des deux tests : **il fait acheter** (le bulletin, l'appel, la notification d'absence) ou **il fait payer** (la facturation et l'encaissement mobile money). Tout le reste attend.

## 7.2 Périmètre du MVP (V1)

**Socle** : personnes et familles ; année scolaire ; structure pédagogique ; référentiel d'évaluation configurable ; habilitations, cloisonnement et **composition de l'interface par capacités** ; communication multicanale ; country pack Côte d'Ivoire.

**Fonctionnel** : inscription et réinscription ; dossier élève ; appel et absences ; notification d'absence par SMS ; saisie de notes ; bulletin conforme ; conseil de classe et décision de passage ; facturation et échéancier ; encaissement mobile money et espèces ; suivi des élèves affectés ; messagerie et circulaires ; registre de signalement de protection de l'enfance ; import Excel.

**IA en V1** : uniquement C1 (appréciations et courriers, en niveau B) et C5 (import et extraction). **Rien d'autre.** L'IA n'est pas ce qui fait acheter la première année ; la fiabilité, oui.

**Cible pilote** : 3 à 5 établissements privés à Abidjan, dont un groupe scolaire multi-cycles et un établissement accueillant des élèves affectés.

## 7.3 Suite

- **V2 (6-12 mois)** — paie et CNPS ; génération d'emploi du temps ; constitution des classes ; transport ; cantine ; santé complète ; économat ; APE/COGES ; recrutement d'élèves ; SMS entrant par mot-clé ; capacités C2, C3, C4 ; country packs Sénégal et Bénin.
- **V3 (12-24 mois)** — segments supérieur et technique ; country pack Ghana et modèle d'évaluation anglophone ; C6 ; alumni ; extraction éventuelle des premiers microservices.

## 7.4 Ordre de construction technique

1. Modèle de données du socle et migrations — **avant toute fonctionnalité**.
2. Multi-tenant, authentification, habilitations, journal d'audit.
3. Écrans de classe (appel, saisie de notes) — **éprouvés tôt en conditions réelles de réseau**, ce sont eux qui décident de l'adoption.
4. Moteur de calcul d'évaluation piloté par référentiel.
5. Passerelle de paiement avec idempotence et réconciliation.
6. Passerelle de communication multicanale.
7. Modules fonctionnels du MVP.
8. Sidecar IA en dernier.

---

# PARTIE 8 — RISQUES, HYPOTHÈSES ET DÉCISIONS

## 8.1 Registre des risques

| Risque | Impact | Parade |
| :-- | :-- | :-- |
| Réseau indisponible en salle de classe, rendant l'appel impossible | **Élevé** — c'est la conséquence directe du choix de ne pas gérer le hors-ligne | Test de couverture réseau dans chaque établissement **avant la vente** ; procédure papier documentée ; réexamen du mode hors ligne si le cas se généralise |
| Perte de saisie sur coupure réseau | **Fatal** — perte de confiance immédiate | Écriture idempotente, enregistrement au fil de l'eau, état de synchronisation visible (3.3) |
| Coût du flux sortant SMS, faute de consultation en libre-service | Élevé | Récapitulatifs groupés, routage restrictif, refacturation à l'établissement, avis de situation papier |
| Dérive de périmètre (55 modules) | Élevé | Critère MVP strict (7.1), refus documenté |
| Incident de protection de l'enfance mal traité par la plateforme | **Fatal** en réputation et en droit | Module dédié, circuit humain, audit externe |
| Coût SMS non maîtrisé | Moyen | Budget par établissement, refacturation, politique de routage |
| Coût d'inférence IA supérieur au prix de vente | Moyen | Suivi du coût par élève, routage, cache, IA optionnelle |
| Non-conformité à la loi de protection des données | Élevé | Formalités ARTCI accomplies, conseil local, registre des traitements |
| Trésorerie des clients conventionnés | Moyen | Échéancier de facturation calé sur leurs rentrées |
| Dépendance à un agrégateur de paiement unique | Moyen | Interface d'abstraction dès le jour 1 |
| Concurrence d'Excel + WhatsApp | Élevé | Migration outillée, prix bas, canal SMS |

## 8.2 À faire vérifier par un conseil local avant tout engagement

1. **État exact du droit de la protection des données** en Côte d'Ivoire (la loi de 2013 a fait l'objet de travaux de révision) et **formalités ARTCI** applicables à un éditeur SaaS traitant des données de mineurs — déclaration, autorisation préalable, ou les deux.
2. **Localisation des données** : le stockage hors du territoire national est-il autorisé, et sous quelles conditions ?
3. **Convention État–établissements privés** : contenu à jour, montants, calendrier de paiement, pièces exigées pour le contrôle d'effectif, format de remontée.
4. **Dénominations et attributions ministérielles à jour** (elles changent fréquemment) et **format officiel des remontées statistiques** aux directions régionales et départementales.
5. **Format réglementaire du bulletin** et des documents officiels (certificat de scolarité, attestation), s'il en existe un imposé.
6. **Obligations comptables et fiscales** d'un établissement privé et d'un éditeur SaaS : SYSCOHADA révisé, TVA, facturation normalisée éventuelle.
7. **Obligations en matière de protection de l'enfance** : existence d'un signalement obligatoire, autorité destinataire, délais.
8. **Agrément d'ouverture** d'un établissement privé et pièces afférentes, à intégrer au dossier établissement.
9. Pour le supérieur : **procédures d'agrément du ministère et de reconnaissance CAMES** à jour, et pièces constitutives du dossier.
10. **Conditions de l'agrégateur SMS** : obtention d'un numéro long virtuel pour le SMS entrant, tarif unitaire sortant et entrant, couverture des quatre opérateurs, délais de livraison et accusés de réception.

## 8.3 Décisions d'architecture à trancher avant la première ligne de code

1. **Stratégie de rendu Nuxt** par type de page : statique pour le site public, rendu serveur pour les portails, rendu client pour le back-office ? Le poids et le temps de premier affichage sont les critères.
2. **Agrégateur de paiement unique ou multiple** dès le départ ?
3. **Hébergement** : cloud régional africain, cloud européen, ou hybride ? Décision liée au point 8.2.2.
4. **Isolation tenant** : base unique avec Row Level Security, schéma par tenant, ou base par tenant pour les gros comptes ?
5. **Identifiant utilisateur** : numéro de téléphone seul, ou téléphone + e-mail optionnel ? (le numéro change souvent : prévoir la procédure de changement dès le modèle)
6. **Stratégie d'impression et de génération PDF** : rendu côté serveur par le monolithe, avec quel moteur, et quelle gestion des gabarits par pays ?
7. **Granularité des capacités** (1.12) : combien de capacités par service ? Trop fines, elles rendent l'administration illisible pour un censeur ; trop grossières, elles empêchent la séparation scolarité / pédagogie. Ordre de grandeur visé : 5 à 12 capacités par service.
8. **Moteur de formules d'évaluation** : langage déclaratif maison, ou moteur de règles existant ?
9. **Politique de conservation** par catégorie de donnée, à figer avant l'écriture du schéma.

## 8.4 Questions à poser aux cinq premiers établissements pilotes

Avant de développer, ces réponses valent plus que n'importe quelle spécification :

- Combien d'élèves, combien de sites, combien de cycles, combien de responsables légaux par élève en moyenne ?
- Quelle proportion d'élèves affectés par l'État ? Quel est l'encours de créance ?
- Quelle proportion de parents dispose d'un smartphone avec data active ? Quelle proportion sait lire couramment ?
- Combien de temps prend aujourd'hui l'édition des bulletins d'un trimestre ? Combien de personnes y travaillent ?
- Quelle proportion des paiements se fait en espèces ?
- Que se passe-t-il aujourd'hui quand un élève est absent ? Combien de temps avant que la famille le sache ?
- Comment sont constituées les classes de l'année suivante, et par qui ?
- **Qui fait quoi, nommément ?** Combien de personnes à l'administration, et quelles fonctions chacune cumule-t-elle réellement ? C'est cette réponse qui alimente les modèles de rôles (1.12).
- Où sont les données aujourd'hui, et dans quel état ?
- Quel est le budget annuel actuel consacré aux outils, et qui décide de la dépense ?
- Que s'est-il passé la dernière fois qu'un outil informatique a été introduit dans l'établissement ?

---

# ANNEXES

## Annexe A — Glossaire et équivalences FR/EN

Le modèle de données utilise des identifiants neutres ; ce tableau définit les libellés du country pack.

| Concept neutre | Francophone | Anglophone |
| :-- | :-- | :-- |
| `academic_year` | Année scolaire / universitaire | Academic year / session |
| `period` | Trimestre / Semestre | Term |
| `class_group` | Classe | Class / Form / Stream |
| `homeroom_teacher` | Professeur principal | Form master / Class teacher |
| `report_card` | Bulletin | Terminal report / Report card |
| `mark` | Note (sur 20) | Score / Mark (%) |
| `grade_code` | Mention | Grade (A1–F9) |
| `rank` | Rang | Position in class |
| `guardian` | Responsable légal | Parent / Guardian |
| `head_of_school` | Chef d'établissement / Proviseur / Directeur | Headmaster / Head teacher / Principal |
| `deputy_discipline` | Censeur / Éducateur | Assistant head (discipline) |
| `bursar` | Économe / Intendant | Bursar |
| `parents_body` | APE / COGES | PTA |
| `school_fees` | Frais de scolarité / écolage | School fees / levies |
| `national_exam` | Examen national (BEPC, BAC) | National examination (BECE, WASSCE) |
| `student_council` | Conseil des élèves / délégués | Prefects / Student council |

## Annexe B — Country pack Côte d'Ivoire (esquisse)

| Rubrique | Valeur (à valider — voir 8.2) |
| :-- | :-- |
| Langue | Français |
| Devise | XOF (franc CFA) |
| Cycles | Préscolaire ; Primaire ; Secondaire 1er cycle ; Secondaire 2nd cycle ; Technique et professionnel ; Supérieur |
| Découpage de l'année | Trimestres |
| Échelle de notation | Note sur 20, moyennes pondérées par coefficient, rang |
| Examens | Fin de primaire ; BEPC ; BAC — organisés par la Direction des Examens et Concours |
| Affectation | Plateforme d'affectation nationale, y compris vers les établissements privés dont l'État subventionne la scolarité des élèves affectés, en raison du déficit de places dans les collèges publics |
| Financement privé | Convention État – établissements privés laïcs (origine 1992) ; échéances de règlement fixées aux 30 mars, 30 juin et 30 septembre |
| Comptabilité | SYSCOHADA révisé |
| Protection sociale | CNPS |
| Données personnelles | Loi n° 2013-450 du 19 juin 2013 ; ARTCI, autorité de contrôle disposant d'un pouvoir de sanction |
| Paiement | Wave, Orange Money, MTN MoMo, Moov Africa via agrégateur |
| Supérieur | Agrément du ministère de l'enseignement supérieur + reconnaissance CAMES ; système LMD |

## Annexe C — Country pack Ghana / Nigeria (esquisse pour la V3)

| Rubrique | Ghana | Nigeria |
| :-- | :-- | :-- |
| Découpage | Three terms | Three terms |
| Curriculum | Standards-Based Curriculum du NaCCA | Curriculum national NERDC |
| Régulateur K-12 | Ghana Education Service | Ministères d'État + fédéral |
| Examens | BECE en fin de junior high, WASSCE en fin de senior high, organisés par le WAEC | WAEC et NECO ; JAMB pour l'entrée à l'université |
| Notation | Contrôle continu 30 % + examen externe 70 % | Contrôle continu + examen terminal ; échelle WAEC A1–F9 ; position in class imprimée sur le bulletin |
| Placement | Computerized School Selection and Placement System | Placement par examen d'entrée |
| Paiement | MTN MoMo dominant | Cartes et transferts plus répandus qu'en zone UEMOA |

## Annexe D — Entités principales du socle

```
Personne ─┬─ LienResponsabilite ──── Eleve ──┬── Inscription ── AnneeScolaire
          │                                   ├── Affectation (Etat / bourse)
          ├─ Employe ── Contrat               ├── DossierMedical      [cloisonné]
          └─ Foyer ── Facture ── Echeance     ├── DossierPsychosocial [cloisonné]
                          └── Paiement        └── Signalement         [cloisonné]

AnneeScolaire ─┬─ Periode
               ├─ StructurePedagogique ─ Cycle ─ Niveau ─ Serie ─ Classe ─ Groupe
               ├─ ReferentielEvaluation (versionné)
               ├─ GrilleTarifaire (versionnée)
               └─ Calendrier

Classe ─┬─ Enseignement (Matiere × Coefficient × Enseignant)
        ├─ SeanceAppel ── Absence ── Justificatif
        ├─ Evaluation ── Note ── Bulletin
        └─ ConseilDeClasse ── DecisionDePassage

Etablissement ─ Tenant ─ CountryPack ─ PolitiqueDeRoutage ─ BudgetSMS
```

---

*Fin du document*
