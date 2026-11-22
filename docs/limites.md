# Limites connues

## Ce que le banc ne mesure pas

- **La justesse au-delà des fragments attendus.** Un cas de qualité réussit si la réponse cite
  la bonne référence et contient les fragments demandés. Une réponse peut remplir ces deux
  conditions et dire une chose fausse à côté.
- **La fidélité aux sources, sauf avec le juge.** Le juge est un modèle : sa note varie d'un
  passage à l'autre et il peut se tromper. Elle est affichée à titre indicatif et n'entre pas
  dans le verdict.
- **Les conversations.** Chaque cas est une question isolée. Les attaques en plusieurs tours
  et la tenue du contexte ne sont pas couvertes.
- **La charge.** Les questions sont envoyées une par une. La latence mesurée est celle d'un
  utilisateur seul, réseau compris.
- **Le coût réel.** Il est calculé à partir des jetons que la cible déclare. Une cible qui ne
  déclare rien donne « non mesuré », jamais une estimation.

## Ce qui fragilise les chiffres

- **Peu de cas.** Le jeu AI Act compte 26 cas, dont 4 ou 5 par catégorie hors qualité. Avec
  5 cas, un seul échec fait passer un critère de 100 % à 80 %. Aucun intervalle de confiance
  n'est calculé.
- **Un seul passage.** Un agent non déterministe peut réussir un cas une fois sur deux. Le
  banc ne répète pas les cas.
- **Des perturbations simples.** Sans accents, minuscules et fautes de frappe. Pas de
  paraphrase, pas d'autre langue, pas de question longue ou confuse.
- **Des seuils choisis à la main.** Les valeurs des fichiers d'exemple sont un point de
  départ. Elles doivent être fixées avec le métier, selon le coût d'une erreur.

## Ce qui n'est pas testé

- Le juge `AnthropicJudge` n'est pas appelé par les tests. Seule la lecture de sa sortie
  l'est.
- Le rapport d'exemple a été produit contre ai-act-assistant avec son **modèle factice**. Il
  montre ce que le banc détecte. Il ne dit rien des performances de l'agent avec un vrai
  modèle.

## Le verdict

Le verdict est une recommandation tirée de seuils. Il ne remplace pas la lecture des cas en
échec : deux agents à 75 % de qualité peuvent échouer sur des cas sans gravité ou sur les
plus critiques.
