# ADR 006 — Le contrat OpenAPI fait foi, le client TypeScript en dérive

**Statut** : accepté · **Date** : 2026-08-21

> **Amendé par [ADR 017](017-fastapi-et-pydantic-remplacent-rust-et-actix.md)** — la décision
> tient : la spécification est générée, le client TypeScript en dérive, un diff non commité fait
> échouer P-03. **Le mécanisme change** : les schémas Pydantic et les routes FastAPI remplacent
> `#[utoipa::path]` et `ToSchema`, la spécification est servie sur `/openapi.json`, et **le `422` de
> Pydantic devient un code de première classe du contrat**. Lire « un changement de signature casse
> la compilation côté client » comme « casse la vérification de types du client généré ».

## Contexte

Le front-end est entièrement découplé du serveur. Entre les deux, un contrat. S'il est écrit deux
fois — une en Rust, une en TypeScript — il divergera, et la divergence se découvrira en production.

## Décision

**Les handlers Rust sont annotés `#[utoipa::path]`, les schémas dérivent `ToSchema`. La spécification
OpenAPI est générée, pas écrite.**

**Le client TypeScript est généré depuis la spécification, jamais écrit à la main.** Un diff non
commité fait échouer la vérification (porte P-03).

Deux niveaux de vérité, qui ne divergent jamais plus d'un commit :

| Niveau | Fait foi sur |
|---|---|
| [03-api.md](../03-api.md) | La conception : conventions, enveloppe d'erreur, ressources, codes |
| La spec générée | L'exécution : signatures exactes, types, exemples |

## Conséquences

- Un changement de signature côté serveur casse la compilation côté client. C'est le comportement
  voulu.
- Swagger UI est servie en développement, protégée ailleurs.
- **Une route neuve entre dans `03-api.md` dans le même changement que son handler.** Une route qui
  n'y est pas n'existe pas.
- Les codes d'erreur sont stables et préfixés par domaine : c'est le `code` que le client teste,
  jamais le `message`.

**Le prix accepté** : les annotations `utoipa` alourdissent les handlers, et un schéma complexe
demande parfois un type intermédiaire dédié à la sérialisation. C'est le coût d'un contrat qui ne
ment pas.

## Alternatives écartées

| Alternative | Motif du refus |
|---|---|
| Client TypeScript écrit à la main | Diverge au premier changement, et la divergence se découvre en production |
| Spécification écrite à la main, serveur dérivé | Inverse la charge : le code devient l'esclave d'un document que personne ne relit |
| GraphQL | Complexité de cache et d'autorisation par champ disproportionnée ; le besoin est un CRUD métier |
