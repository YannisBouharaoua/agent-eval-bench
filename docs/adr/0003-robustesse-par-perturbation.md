# 3. Mesurer la robustesse par des variantes des cas réussis

**Statut** : accepté

## Contexte

Un agent qui répond bien à une question soignée peut échouer dès qu'il manque un accent.
Cette fragilité est invisible si les cas sont tous écrits proprement.

## Décision

Chaque cas de qualité est rejoué sous trois formes : sans accents, en minuscules, avec des
fautes de frappe. Les variantes gardent les attentes du cas d'origine.

La robustesse est la part des variantes réussies **parmi celles dont l'original réussit**.

## Pourquoi cette définition

Si l'original échoue, sa variante échoue presque toujours aussi, pour la même raison. La
compter ferait baisser deux critères pour un seul défaut. La robustesse isole donc une seule
question : une réponse juste le reste-t-elle quand la forme de la question change ?

## Conséquences

- Les fautes de frappe sont tirées d'une graine calculée sur la question. Deux passages
  produisent les mêmes variantes, et un échec se rejoue à l'identique.
- Quand aucun cas d'origine ne réussit, la robustesse est « non mesurée », et non 0 %.
- Les variantes multiplient par 4 le nombre d'appels sur les cas de qualité.
- Ces perturbations portent sur la forme. Les paraphrases, qui changent les mots, ne sont
  pas couvertes (voir `docs/limites.md`).
