# 00 — Brief produit

*Nelo — plateforme de gestion pour établissements scolaires.*
*Pilote : établissements privés d'Abidjan, Côte d'Ivoire — **par le cycle primaire**
([ADR 018](adr/018-le-mvp-commence-par-le-primaire.md)).*

---

## 1. Le problème

Un groupe scolaire privé d'Abidjan tient sa scolarité dans un classeur, ses notes dans un fichier
Excel par maître, et sa communication aux familles dans un groupe WhatsApp. Trois fois par an,
l'édition des bulletins mobilise le secrétariat pendant une semaine : on ressaisit les notes de
quarante feuilles de classeur, on recalcule les moyennes pondérées à la calculatrice, on découvre les
erreurs à la relecture des parents.

Quatre conséquences, et ce sont elles qu'on attaque :

1. **L'absence n'atteint pas la famille le jour même.** L'appel se fait sur une feuille, la feuille
   remonte au bureau des surveillants en fin de journée, et le parent l'apprend au mieux le
   lendemain — souvent jamais. C'est le premier motif de perte de confiance envers l'établissement,
   et le premier argument de vente du produit.
2. **Le bulletin coûte une semaine de travail par trimestre**, et il est contestable : une moyenne
   recalculée à la main est un litige en puissance, et les règles d'arrondi ne sont écrites nulle
   part.
3. **L'établissement ne connaît pas sa trésorerie.** Le solde d'une famille se reconstitue en
   feuilletant un carnet de reçus. Pour un établissement conventionné, la créance sur l'État — versée
   avec retard, parfois d'une année sur l'autre — n'est chiffrée par personne.
4. **La donnée est ailleurs.** Excel, papier, ou un logiciel abandonné faute de support. La reprise
   n'est pas une étape du projet : **c'est la première fonctionnalité vendue.**

Le concurrent réel n'est pas un éditeur : **c'est Excel plus WhatsApp.** Il est gratuit, il
fonctionne, et tout le monde sait s'en servir. On ne le bat pas sur les fonctionnalités.

## 2. Ce qu'on construit

Une application web unique, **mobile-first et responsive**, dont la surface se compose à partir des
**capacités effectives** de la personne connectée. Le même code sert le téléphone d'un enseignant en
salle de classe, la tablette de la saisie de notes, le poste de l'économe et le portail du parent.

**Il n'y a pas d'« interface du censeur » ni d'« interface de l'économe ».** Dans une école de
400 élèves, une seule personne tient la scolarité, la pédagogie et l'emploi du temps ; dans un groupe
de 3 000, ce sont trois services. Un produit qui impose un découpage fixe force le petit établissement
à jongler entre plusieurs comptes — avec le partage de mots de passe qui s'ensuit — et oblige le grand
à accorder des droits trop larges. La composition par capacités n'est pas un raffinement
d'ergonomie : c'est une exigence structurante, et elle est dans le MVP.

### Les quatre piliers

| Pilier | Ce que ça veut dire concrètement |
|---|---|
| **Le SMS est un canal de premier rang** | Une part significative des responsables légaux n'a ni smartphone ni forfait data actif. Chaque notification métier a une variante SMS de moins de 160 caractères, **rédigée pour ce canal** — pas un push tronqué |
| **Le référentiel d'évaluation est une donnée, pas du code** | Échelle, conversion en mention, formule de composition, règles d'arrondi et de rang : tout est versionné par pays et par année. Sans cela, chaque nouveau pays devient un déploiement, et un bulletin réédité trois ans plus tard est faux |
| **Une application, des capacités cumulées** | Un censeur qui tient aussi la pédagogie ouvre une seule application. Ses capacités sont l'union de ses affectations, et la navigation se compose à partir de cette union |
| **Le cloisonnement prime sur les habilitations** | Santé, psychosocial, protection de l'enfance, paie individuelle : ces données sortent du système de rôles et s'attribuent nominativement. Un chef d'établissement n'a pas accès par défaut au contenu d'un signalement qui le concerne |

## 3. Objectif

**L'école primaire d'un groupe scolaire d'Abidjan édite ses bulletins du trimestre dans Nelo, et
encaisse la scolarité du trimestre suivant dedans.** C'est le seul critère de réussite du premier
jalon.

Indicateurs qui le mesurent :

| Métrique | Vert | Rouge |
|---|---|---|
| Durée de l'appel d'une classe de 40 élèves | < 45 s | > 2 min |
| Délai entre l'absence et le SMS à la famille | < 10 min | > 2 h |
| Saisies perdues sur coupure réseau | **0** | ≥ 1 |
| Durée d'édition des bulletins d'un trimestre | < 1 jour | > 3 jours |
| Bulletins contestés pour erreur de calcul | 0 | ≥ 2 |
| Poids de l'écran d'appel | < 120 Ko | > 400 Ko |
| Reprise d'un établissement de 800 élèves | < 2 semaines | > 6 semaines |

**La saisie perdue est le seul indicateur dont le rouge est fatal.** Un enseignant qui perd quarante
notes à la dernière ligne ne rouvre pas l'application, et il le raconte en salle des professeurs.

## 4. Les huit contraintes qui dictent la conception

Ce ne sont pas des limitations à contourner : ce sont les données d'entrée.

| # | Contrainte | Ce qu'elle impose |
|---|---|---|
| 1 | **Le parent n'a pas forcément de smartphone ni de data** | Toute fonction critique existe en SMS — absence, convocation, échéance |
| 2 | **L'électricité est intermittente** | Pas de serveur dans l'école. Le modèle est le cloud |
| 3 | **La connectivité est lente, intermittente et coûteuse** | Budget de poids par écran, écriture idempotente, reprise sans perte |
| 4 | **Le paiement est mobile money, pas carte bancaire** | Wave, Orange Money, MTN MoMo, Moov. Une intégration carte seule est inutilisable |
| 5 | **L'État est un payeur majeur et un mauvais payeur** | La créance sur l'État et son ancienneté sont des entités du modèle financier |
| 6 | **L'établissement n'a ni DSI ni informaticien** | Administrable par un censeur ou un économe. Le support est humain et local |
| 7 | **Les données existantes sont dans Excel ou sur papier** | L'import tolérant au désordre est une fonctionnalité du MVP, pas un outil interne |
| 8 | **Le prix de référence est bas** | Tarification par élève et par an en francs CFA. Chaque Mo de RAM et chaque appel d'inférence comptent |

## 5. Ce que le MVP fait

**Le critère d'entrée tient en deux tests.** Un module entre si **il fait acheter** — le bulletin,
l'appel, la notification d'absence — ou si **il fait payer** — la facturation et l'encaissement mobile
money. Tout le reste attend, et le refus se documente.

**Le socle** — personnes, foyers et liens de responsabilité ; année scolaire ; structure pédagogique ;
référentiel d'évaluation configurable ; capacités, cloisonnement et composition de l'interface ;
communication multicanale ; country pack Côte d'Ivoire.

**Le fonctionnel** — inscription et réinscription ; dossier élève ; appel et absences ; notification
d'absence par SMS ; saisie de notes ; bulletin conforme ; conseil des maîtres et décision de passage ;
facturation et échéancier ; encaissement mobile money et espèces ; financement public et créance sur
l'État ; messagerie et circulaires ; registre de signalement de protection de l'enfance ;
import Excel.

**Le segment** — **le primaire, et lui seul** : six niveaux du CP1 au CM2, un maître polyvalent par
classe, un appel par demi-journée, aucune série. Les quatre autres segments sont datés dans
[06-apres-mvp.md § 4](06-apres-mvp.md), dans l'ordre préscolaire, secondaire général, technique,
supérieur — et le motif de cet ordre est dans
[ADR 018](adr/018-le-mvp-commence-par-le-primaire.md).

**L'IA** — deux capacités seulement : la rédaction assistée d'appréciations et de courriers, **en
proposition validée par une personne nommée**, et l'extraction documentaire pour l'import. Rien
d'autre. L'IA n'est pas ce qui fait acheter la première année ; la fiabilité, oui.

## 6. Ce que le MVP ne fait pas

C'est la section la plus utile du document. Chaque ligne évite d'écrire du code qui n'a pas lieu
d'être.

### Écarté durablement — ce n'est pas le métier

| Ce qu'on ne fait pas | Pourquoi |
|---|---|
| Du contenu pédagogique propriétaire | La plateforme héberge et distribue, elle ne produit pas le curriculum |
| Un LMS complet type Moodle | Un dépôt de ressources et un cahier de textes suffisent |
| De la comptabilité générale certifiée | On produit les écritures et l'export SYSCOHADA, on ne remplace pas le logiciel comptable |
| De la paie déclarative | On prépare ; la responsabilité déclarative CNPS et fiscale reste à l'établissement |
| Les concours nationaux et l'affectation d'État | Ces plateformes appartiennent aux ministères. On s'y interface, on ne s'y substitue pas |
| La reconnaissance faciale | Donnée biométrique, régime renforcé, aucun gain proportionné |

### Différé — la décision est prise, l'échéance ne l'est pas

| Ce qui est différé | Jusqu'à quand |
|---|---|
| **Le mode hors connexion** | Réexaminé une fois le produit installé et la couverture réseau réelle mesurée en salle de classe. **Différé n'est pas exclu** : quatre fondations se posent maintenant pour que la reprise soit additive — [ADR 001](adr/001-hors-connexion-differe.md) |
| **L'application native** | L'accès se fait par le web, installable sur l'écran d'accueil. Capacitor enveloppera la même base Nuxt le jour où les notifications natives ou la caméra en usage intensif le justifieront — [ADR 002](adr/002-web-d-abord-capacitor-plus-tard.md) |
| **Le SMS entrant par mot-clé** | V2. Le numéro long virtuel et le contrôle d'accès par numéro appelant sont conçus dès le socle, pas construits |
| **Le préscolaire et le secondaire général** | V2. Ce sont les deux autres cycles du groupe scolaire, et ils arrivent dans cet ordre — [ADR 018](adr/018-le-mvp-commence-par-le-primaire.md) |
| **Les segments supérieur et technique** | V3. Le socle doit les absorber sans réécriture ; il ne les sert pas |
| **Le monde anglophone** | V3. Le passage n'est pas une traduction, c'est un changement de modèle d'évaluation — et c'est précisément pour cela que le référentiel est une donnée versionnée dès le premier jour |

### Hors périmètre technique

Pas de microservices, pas de bus de messages, pas de Kubernetes, pas d'ORM. Un monolithe modulaire
dont les frontières de modules sont les futures frontières de services — et la condition pour que
l'extraction reste indolore est que **les modules ne partagent jamais de transaction de base de
données** ([ADR 003](adr/003-monolithe-modulaire-microservices-plus-tard.md)).

## 7. L'ordre de grandeur, dit franchement

Le document de conception d'origine décrit **55 services et modules**, six segments d'établissements
et trois vagues de pays. C'est une feuille de route d'éditeur sur cinq ans, pas un périmètre de
première version.

Le MVP retenu ici en garde **le socle complet, douze modules fonctionnels et un seul segment — le
primaire**. C'est encore considérable pour un développeur seul, et la roadmap le découpe en tranches
dont chacune se livre et se vérifie séparément. Ce qui n'entre pas est rangé dans
[06-apres-mvp.md](06-apres-mvp.md), avec son ordre et son coût — **et ce fichier ne s'ouvre pas pour coder.**

Deux choses ne se négocient pas dans ce découpage, parce qu'elles sont des refontes de schéma si
elles arrivent après coup :

1. **Le référentiel d'évaluation configurable.** Coder une moyenne pondérée sur 20 en dur, c'est
   condamner l'extension anglophone à une réécriture.
2. **Les capacités et le cloisonnement.** Un système de rôles fixes ne se transforme pas en ABAC par
   ajout : il se remplace, et avec lui toutes les vérifications d'accès du produit.

## 8. Ce qu'on saura seulement en allant voir

Treize questions à poser aux cinq premiers établissements pilotes valent plus que n'importe quelle
spécification. Elles sont listées dans [progress.md](progress.md), section « Ce qui attend une
réponse » — parce que ce sont des questions ouvertes, pas des décisions prises.

Trois d'entre elles peuvent changer l'architecture :

- **Quelle est la couverture réseau réelle dans les salles de classe, aux étages, dans les bâtiments
  en dur ?** Si un pilote n'a pas de réseau utilisable en classe, l'appel s'y fera sur papier puis en
  saisie différée au bureau. C'est un compromis acceptable, mais il doit être identifié **avant la
  vente**, pas après.
- **Quelle proportion de parents dispose d'un smartphone avec data active ?** Elle décide du poids
  relatif du canal SMS dans le modèle économique.
- **Qui fait quoi, nommément, dans l'administration ?** C'est cette réponse qui alimente les modèles
  de rôles livrés, et les personas sur lesquels les cumuls de capacités seront testés.

---

**Suite** → [01-stack.md](01-stack.md) pour la structure du dépôt, [02-domaine.md](02-domaine.md) pour
le modèle.
