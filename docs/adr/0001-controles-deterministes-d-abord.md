# 1. Des contrôles déterministes pour le verdict, un juge par modèle à titre indicatif

**Statut** : accepté

## Contexte

Le banc doit produire un verdict qui sert à décider de la suite d'un prototype. Un verdict
qui change d'un passage à l'autre sans que l'agent ait changé ne peut pas servir de porte en
CI, et il se défend mal devant un comité.

## Options étudiées

| Option | Pour | Contre |
|---|---|---|
| Tout noter par un modèle juge | Juge le sens, peu de cas à écrire | Coûteux, variable, opaque. Le juge peut lui-même être trompé par la réponse |
| Similarité avec une réponse de référence (ROUGE, embeddings) | Automatique | Pénalise une bonne réponse formulée autrement, récompense une mauvaise réponse ressemblante |
| Contrôles déterministes : statut, références citées, fragments présents ou absents | Reproductible, gratuit, chaque échec s'explique | Demande d'écrire les attentes cas par cas. Ne juge pas le sens global |

## Décision

Le verdict repose uniquement sur des contrôles déterministes. Un juge par modèle, optionnel,
note la fidélité de la réponse aux sources. Sa note est affichée à part.

## Conséquences

- Deux passages sur le même agent déterministe donnent le même verdict.
- Chaque échec renvoie à une règle lisible (« absent : six mois »).
- Écrire un bon cas prend du temps : c'est là que se trouve la valeur du banc.
- La note du juge pourra entrer dans le verdict une fois sa stabilité mesurée, par exemple
  en répétant chaque jugement et en mesurant l'accord avec des annotations humaines.
