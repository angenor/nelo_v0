# Specification Quality Checklist: Le socle serveur (T0a)

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-03
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs) — **exception assumée et
      documentée** : la pile est le sujet de la tranche ([04-roadmap.md § T0](../../../docs/04-roadmap.md)).
      Elle est isolée dans la section « Contraintes de pile » (CP-01 à CP-06) ; les exigences
      fonctionnelles décrivent des comportements observables. Les en-têtes et codes cités sont ceux
      du contrat projet (`03-api.md`), pas des choix d'implémentation
- [x] Focused on user value and business needs — l'utilisateur est le développeur seul et l'auteur
      de chaque tranche suivante ; chaque story dit ce qu'elle débloque et ce qu'elle empêche
- [x] Written for non-technical stakeholders — dans la mesure où une tranche d'infrastructure le
      permet : chaque exigence porte son « pourquoi » tiré du corpus
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain — zéro marqueur ; les trois choix qui auraient pu en
      porter sont tranchés par défaut raisonné et exposés dans « Assumptions » (module doré,
      clé du réglage d'assistance, résolution provisoire du tenant)
- [x] Requirements are testable and unambiguous — FR-001 à FR-049, chacune vérifiable par un test
      ou par une porte
- [x] Success criteria are measurable — SC-001 à SC-010, chacun avec un compte, un délai ou un
      taux
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined — sept stories, trente-huit scénarios Given/When/Then
- [x] Edge cases are identified — douze cas limites
- [x] Scope is clearly bounded — section « Hors périmètre » ; les sept portes nommées, les cinq
      autres renvoyées à leur tranche
- [x] Dependencies and assumptions identified — dix hypothèses, dont un **diff proposé sur
      `docs/02-domaine.md` § 17** à arbitrer avant le plan

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows — critère de fin (US1), fondations irrattrapables (US2,
      US3), frontières (US4), vérification (US5), simulations (US6), assistance (US7)
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification — hors la section d'exception assumée

## Notes

- Items marked incomplete require spec updates before `/speckit-clarify` or `/speckit-plan`
- **Un arbitrage attend avant le plan** : la clé du catalogue qui suspend l'assistance
  (`assistance.suspendue`, portée `ÉTABLISSEMENT`, défaut `false`) est **proposée**, pas décidée.
  Le plan ne peut pas la dériver de `02-domaine.md` tant que le diff n'est pas appliqué.
- **La revue visuelle prend la forme B** (planche de diagrammes Mermaid), en session dédiée avant
  le plan : [design/prompt-diagrammes.md](../design/prompt-diagrammes.md).
- Validation faite en une itération : aucun item en échec.
