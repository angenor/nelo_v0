# ADR 008 — Local d'abord, VPS ensuite

**Statut** : accepté · **Date** : 2026-08-21

> **Amendé par [ADR 017](017-fastapi-et-pydantic-remplacent-rust-et-actix.md)** — le sidecar ayant
> disparu, `compose.yml` décrit **trois** services : postgres, valkey, garage. Le service
> d'inférence rejoint les intégrations externes derrière leur interface, avec leur implémentation
> simulée. **Le reste de la décision est intact** : tout tourne sur le poste, aucun service tiers
> distant n'est requis pour développer.

## Contexte

Un développeur seul, en Côte d'Ivoire, doit pouvoir travailler et démontrer le produit sans dépendre
du réseau. Une démonstration dans un établissement d'Abidjan où le Wi-Fi tombe ne peut pas être une
démonstration ratée.

## Décision

**Tout tourne sur le poste.** `compose.yml` décrit quatre services et rien d'autre : postgres, valkey,
garage, sidecar-ia. **Aucun service tiers distant n'est requis pour développer.**

**Les intégrations externes vivent derrière un trait, avec une implémentation simulée livrée en même
temps que l'interface** : agrégateur de paiement, passerelle SMS, WhatsApp Business. La simulation est
le mode par défaut en local.

Le passage en production est un **changement de configuration** : même image Docker, VPS, volumes
persistants. Rien d'autre ne change.

## Conséquences

- Un nouveau poste est opérationnel en une commande.
- La base locale est éphémère et recréable à volonté ; les migrations s'appliquent sur une base vierge
  à chaque vérification (porte P-01).
- Garage tourne en mono-nœud avec `replication_mode = 1` en local, en topologie répliquée en
  production. **Même API S3, donc migration possible vers un S3 managé sans réécriture.**

> ⚠️ **Une simulation doit savoir échouer aussi bien que réussir.** La passerelle SMS simulée doit
> pouvoir renvoyer un accusé en retard, en double, ou jamais — parce que c'est ce que fait la vraie.
> Un webhook de paiement qui n'arrive jamais est le cas nominal à concevoir, pas l'exception.

**Le prix accepté** : maintenir une simulation par intégration externe est du code qui ne part jamais
en production. C'est le prix d'un environnement de développement qui ne dépend de personne — et ce
code sert aussi de banc d'essai pour les cas d'échec, qu'on ne peut pas provoquer chez le vrai
fournisseur.

## Alternatives écartées

| Alternative | Motif du refus |
|---|---|
| Services managés en développement | Rend le développement dépendant du réseau et d'un compte fournisseur |
| Environnement de recette partagé comme cible principale | Un développeur seul n'a pas besoin d'un environnement partagé, et il coûte |
| Appels réels aux intégrations en développement | Un SMS de test coûte, et un webhook de paiement réel ne se rejoue pas |
