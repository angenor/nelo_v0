# Le mouvement

*Ce qui bouge dans l'interface, et pourquoi presque rien ne bouge. Écrit avec le ruban de T0b.*

## Une seule animation

L'interface a **une** animation : **le point qui pulse** du ruban d'état de saisie, pendant
l'envoi (« Envoi de 2 saisies »). Elle dit que quelque chose est en cours et qu'il n'y a rien à
faire.

| Ce qui bouge | Durée | Courbe | Ce qui varie | Où |
|---|---|---|---|---|
| Le point d'envoi du ruban | `--pulsation-duree` (1,2 s) | `--pulsation-courbe` (`ease-in-out`) | L'opacité, de 1 à 0,3 et retour, en boucle | `RubanSaisie.vue`, état `envoi` |

Les deux valeurs viennent de `docs/design/mesures.css`, copié tel quel dans l'application ; la
planche 13 les fixe.

## Réduire les animations

Sous la préférence de l'appareil **« réduire les animations »** (`prefers-reduced-motion:
reduce`), le point **ne pulse plus**. Il reste affiché, avec sa forme et son mot : l'état se lit
toujours, seul le mouvement disparaît. Un test le vérifie dans un vrai navigateur
(`web/tests/e2e/ruban.spec.ts`).

## Ce qui ne bouge pas

- **Rien ne clignote**, sous aucun état. Le ruban hors ligne est ocre et immobile : une coupure
  n'est pas une alarme.
- **Aucune transition de page**, aucun glissement de tiroir, aucun fondu d'alerte. Le tiroir de
  navigation apparaît et disparaît sans animation.
- **Le survol ne révèle rien** : il change une teinte, jamais la présence d'un élément.

## La règle

**Aucune autre durée n'existe.** Une durée nouvelle entre dans `docs/design/mesures.css` avant
d'entrer dans un composant, avec sa raison, puis ici, dans le tableau ci-dessus. Un composant qui
écrit une durée en dur crée la seconde vérité que le projet interdit.
