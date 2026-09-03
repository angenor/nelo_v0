# ADR 005 — Isolation des tenants par RLS forcée, et double barrière

**Statut** : accepté · **Date** : 2026-08-21

## Contexte

Une fuite de données entre deux établissements est l'incident qui termine le produit. Il ne s'agit pas
de données commerciales : ce sont des dossiers de mineurs, des signalements de protection de
l'enfance, des dossiers médicaux.

Trois modèles d'isolation existent : base unique avec Row Level Security, schéma par tenant, base par
tenant.

## Décision

**Base unique, Row Level Security activée ET forcée sur chaque table, avec un rôle applicatif distinct
du propriétaire des tables.**

`SET LOCAL app.current_tenant` posé **dans chaque transaction**, jamais à l'ouverture de connexion.
Avec un pool de connexions, c'est exactement la différence entre l'isolation et la fuite.

**Et une deuxième barrière, applicative** : chaque appel revérifie la capacité et le périmètre du
compte. **Aucune des deux barrières n'est jamais la seule.**

## Conséquences

- La porte P-01 vérifie mécaniquement que chaque table porte `ENABLE` **et** `FORCE ROW LEVEL
  SECURITY` avec sa politique. `ENABLE` seul ne s'applique pas au propriétaire des tables : c'est le
  piège classique, et il est mécaniquement fermé.
- Tout nouveau schéma s'accompagne d'un test d'isolation entre deux tenants.
- Une ressource inexistante *dans le périmètre du tenant* répond `404`, jamais `403` : publier
  l'existence d'un établissement tiers est déjà une fuite.
- Le passage à une base par tenant reste possible pour un gros compte, sans changer une ligne de
  logique métier — la RLS devient alors redondante, pas fausse.

**Le prix accepté** : chaque transaction porte un `SET LOCAL`. C'est une ligne de plus dans chaque
ouverture de transaction, et un oubli est indétectable à la lecture. C'est pourquoi il est encapsulé
dans un unique point d'entrée, et pourquoi P-01 existe.

## Alternatives écartées

| Alternative | Motif du refus |
|---|---|
| Schéma par tenant | Les migrations se multiplient par le nombre de clients ; ingérable pour un développeur seul |
| Base par tenant dès le départ | Même problème, plus le coût d'infrastructure — incompatible avec un prix par élève bas |
| Filtrage applicatif seul | Un seul oubli dans une requête suffit. La RLS ne s'oublie pas |
| RLS seule, sans vérification applicative | Ne couvre pas le périmètre (classes, matières) : un enseignant du bon tenant verrait les notes d'une autre classe |
