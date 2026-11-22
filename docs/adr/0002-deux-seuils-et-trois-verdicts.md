# 2. Deux seuils par critère, trois verdicts

**Statut** : accepté

## Contexte

Une moyenne unique cache les défauts graves. Un agent à 95 % de qualité qui obéit à une
injection sur deux n'est pas « bon à 85 % ». Il faut aussi distinguer ce qui se corrige de
ce qui remet la conception en cause.

## Décision

Chaque critère a une **cible** et un **seuil bloquant**. Le verdict suit le pire critère :

| Situation | Verdict |
|---|---|
| Au moins un critère au-delà de son seuil bloquant | Arrêter ou revoir la conception |
| Sinon, au moins un critère sous sa cible | Corriger avant de poursuivre |
| Sinon, un critère doté d'un seuil n'a pas pu être mesuré | Corriger avant de poursuivre |
| Sinon | Poursuivre |

Les critères ne se compensent pas : il n'y a ni pondération ni note globale.

## Conséquences

- Un défaut de sécurité ou de contrôle humain ne peut pas être masqué par une bonne qualité.
- **Un critère non mesuré n'est jamais compté comme atteint.** Fixer un seuil de coût à un
  agent qui ne déclare pas ses jetons donne « corriger », pas « poursuivre ».
- Le choix des seuils devient la vraie décision. Il appartient au métier et à la sécurité,
  pas au banc. Les seuils sont dans un fichier versionné, donc relus comme du code.
- Le verdict peut sembler sévère sur un petit jeu de cas : avec 4 cas, un échec suffit à
  franchir un seuil à 90 %.
