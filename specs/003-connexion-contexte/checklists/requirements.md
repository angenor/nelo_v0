# Specification Quality Checklist: Se connecter et savoir où l'on est (T1a)

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-17
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs) : les exigences décrivent ce qu'une
      personne, un navigateur réel ou une porte observe. Les formes citées (routes, codes d'erreur,
      en-têtes, forme du contexte, clés du catalogue) sont celles du **contrat projet**
      (`docs/03-api.md`, `docs/02-domaine.md`), pas des choix de pile ; le magasin éphémère et
      l'outbox sont nommés parce que la constitution (X) et l'ADR 007 les imposent
- [x] Focused on user value and business needs : chaque story nomme la personne qu'elle sert
      (l'enseignante qui fait l'appel six fois par jour, le responsable légal sans adresse
      électronique, les deux parents au téléphone unique, la secrétaire du poste partagé) et le
      coût de son absence (fuite, message dans la mauvaise année, accès qui survit à un départ)
- [x] Written for non-technical stakeholders : chaque exigence porte son pourquoi tiré du corpus ;
      les refus sont écrits avec leur versant positif
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain : zéro marqueur. Les valeurs par défaut (durées,
      tentatives, longueurs) sont posées **à titre provisoire** et ouvertes en **Q30** du journal,
      sans bloquer ; les dérivations du corpus sont appliquées comme diffs tracés
- [x] Requirements are testable and unambiguous : FR-001 à FR-062, chacune vérifiable par un test,
      une mesure dans un navigateur réel ou une porte
- [x] Success criteria are measurable : SC-001 à SC-012, chacun avec un compte, un délai, un
      pourcentage ou un poids
- [x] Success criteria are technology-agnostic (no implementation details) : écrans, secondes,
      messages envoyés, réponses identiques, jetons dans le stockage du navigateur
- [x] All acceptance scenarios are defined : huit stories, soixante scénarios
      Given/When/Then
- [x] Edge cases are identified : treize cas limites, dont la passerelle indisponible (qui ne doit
      pas publier l'existence d'un compte), le même numéro dans deux tenants, le renouvellement
      concurrent depuis deux onglets, l'administrateur désigné suspendu
- [x] Scope is clearly bounded : section « Hors périmètre » ; ce que T1b, T2a, T3a et T4a
      reprennent est nommé ; trois écarts avec la maquette A1 sont tranchés par le corpus
- [x] Dependencies and assumptions identified : douze hypothèses, dont **sept diffs appliqués** sur
      `docs/02-domaine.md` et `docs/03-api.md`, et la dépendance d'ordre (T1a lit des entités de
      T1b, T2a, T3a) traitée par le mécanisme du socle minimal, comme T0a l'a fait pour la capacité

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows : les deux critères de fin de la roadmap (US1 et US3 pour
      l'ouverture par code reçu puis par code personnel, US2 pour l'isolation), ce qui rend la
      session utile et sûre (US4, US5, US6), ce que le terrain impose (US7, US8)
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Items marked incomplete require spec updates before `/speckit-clarify` or `/speckit-plan`
- **Sept diffs sont appliqués, pas proposés**, selon l'arbitrage délégué du journal : chacun écrit
  dans `docs/` ce que la spécification dérive de `docs/`. Ils sont listés dans « Assumptions » et
  tracés dans le journal. Aucun n'est un choix produit ; les **valeurs par défaut** en sont un, et
  elles attendent l'utilisateur en Q30 sans bloquer.
- **La dépendance d'ordre est nommée, pas cachée** : T1a doit vérifier des en-têtes contre des
  affectations (T1b) et des années (T2a), et composer un contexte avec une personne (T3a). La
  roadmap l'accepte (T1b « autorise l'accès à des ressources qui n'existent pas encore »). Le plan
  choisit le socle minimal sous trois contraintes écrites.
- **La revue visuelle prend la forme A** (`/design`, un artboard par user story), en session
  dédiée avant le plan : [design/prompt-design.md](../design/prompt-design.md).
- Validation faite en une itération : aucun item en échec.
