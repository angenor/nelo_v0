# Specification Quality Checklist: Le socle d'interface (T0b)

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-15
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs) — **exception assumée et
      documentée** : l'epic T0 nomme la pile parce qu'elle est le sujet
      ([04-roadmap.md § T0](../../../docs/04-roadmap.md)). Elle est isolée dans « Contraintes de
      pile » (CP-01 à CP-06) ; les exigences décrivent ce qu'une personne ou une porte observe. Les
      formes citées (contexte § 1.9, en-têtes, clés de libellé) sont celles du contrat projet
- [x] Focused on user value and business needs — chaque story nomme la personne qu'elle sert
      (enseignante en classe, secrétaire sur poste partagé, parent au forfait compté, économe qui
      cumule) ou l'auteur de tranche qu'elle débloque, et le coût de son absence
- [x] Written for non-technical stakeholders — chaque exigence porte son « pourquoi » tiré du
      corpus ; les mots sont ceux du système de design, pas ceux d'un framework
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain — zéro marqueur ; les choix qui auraient pu en
      porter sont tranchés par défaut raisonné et exposés dans « Assumptions » (seuil de
      regroupement, administrateur dans le contexte, nom et icône provisoires, thème par appareil,
      service worker, réordonnancement différé)
- [x] Requirements are testable and unambiguous — FR-001 à FR-093, chacune vérifiable par un test,
      une mesure ou une porte
- [x] Success criteria are measurable — SC-001 à SC-012, chacun avec un compte, un délai, un
      poids ou un taux
- [x] Success criteria are technology-agnostic (no implementation details) — poids transférés,
      secondes, comptes d'états, moteurs de rendu nommés parce que le corpus les nomme
- [x] All acceptance scenarios are defined — huit stories, cinquante-sept scénarios
      Given/When/Then
- [x] Edge cases are identified — quatorze cas limites, dont deux écarts maquette / domaine tranchés
      par le domaine
- [x] Scope is clearly bounded — section « Hors périmètre » ; ce que T1a, T1b et T10b reprennent
      est nommé
- [x] Dependencies and assumptions identified — vingt hypothèses, dont un **diff appliqué sur
      `docs/03-api.md` § 1.9** (l'administrateur de l'établissement dans le contexte)

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows — les trois critères de fin (US1, US3 → US4, US6), le
      composant le plus important (US2), les garanties héritées (US5, US6, US7), la discipline de
      disposition (US8)
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification — hors la section d'exception assumée

## Notes

- Items marked incomplete require spec updates before `/speckit-clarify` or `/speckit-plan`
- **Un diff est appliqué, pas proposé** : `docs/03-api.md` § 1.9 porte désormais
  `administrateur` sur chaque établissement du contexte. Il dérive de la constitution (II) et de
  `02-domaine.md` § 3.4 ; il est tracé dans la spec, ici et dans le journal. T1a le sert.
- **Trois questions du journal touchent cette tranche** et sont traitées sans bloquer : Q1
  (polices) se tranche dans le plan sous contrainte ; Q2 (marque) reçoit un nom et une icône
  provisoires en un seul endroit ; Q4 (rendu) reste une hypothèse que le plan retient ou réexamine
  et le dit.
- **La revue visuelle prend la forme A** (`/design`, un artboard par user story), en session
  dédiée avant le plan : [design/prompt-design.md](../design/prompt-design.md). L'artboard de la
  page de style est transverse et va dans `docs/design/canvas/`.
- Validation faite en une itération : aucun item en échec.
