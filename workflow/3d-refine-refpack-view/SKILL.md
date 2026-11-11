---
name: 3d-refine-refpack-view
description: "Retoucher une vue précise d'un refpack existant, face, profil ou trois-quarts, puis contrôler les autres vues et la paire détaillé/volumes. Préserver les versions et comparer avant/après ; ne pas modifier Blender."
---

# 3D — Retoucher une référence

La vue choisie guide la correction ; les autres vues contrôlent les régressions.

Lire les contraintes d'outils, d'original et d'analyse de [3d-generate-refpack](../3d-generate-refpack/SKILL.md) ainsi que son [contrat multivue et de révision](../3d-generate-refpack/references/multiview-contract.md). Appliquer leur budget et leur manifeste, sans relancer automatiquement une création complète. Ce skill utilise uniquement la génération d'images intégrée, sans service payant supplémentaire ni API séparée, et ne lance aucune modélisation.

## Définir la retouche

Identifier le projet, la famille détaillée ou volumes, la vue, le côté du profil ou du trois-quarts, les éléments à corriger et ceux à préserver. Déduire les choix du contexte et du manifeste ; clarifier seulement une ambiguïté structurante. Écrire un objectif observable, par exemple « réduire la profondeur du torse de profil en gardant sa largeur de face ».

Ouvrir l'original, le manifeste, le rapport et les six vues retenues. Vérifier les empreintes. Pour un ancien pack incomplet, appliquer la règle de migration du contrat ; ne pas confondre une retouche réussie avec la livraison de six vues.

## Préserver l'avant

Pour une nouvelle demande sur un pack terminé, ouvrir un identifiant de révision libre, préserver manifeste, rapport, fichiers et empreintes avant toute génération. Pour un travail en cours, continuer sa révision et ses compteurs. Fixer pose, cadrage, échelle, projection, lumière et invariants de la vue ciblée.

Noter quels jalons sont affectés : une retouche détaillée rouvre detailed et volumes ; une retouche des seuls volumes rouvre volumes. Réexaminer l'amont si elle révèle une contradiction, sans laisser un ancien READY masquer ce problème.

## Corriger et comparer

1. Vérifier l'outil réellement accessible. Lui transmettre l'original, l'image à éditer et les vues de contrôle pertinentes, avec rôles explicites. Demander une modification ciblée en répétant les invariants.
2. Enregistrer une nouvelle image, jamais sur l'ancien chemin. Ouvrir la sortie et l'avant au même cadrage ; vérifier l'amélioration recherchée contre l'original.
3. Ouvrir toutes les autres vues retenues. Contrôler les proportions, la pose, les raccords, la latéralité et les espaces négatifs ; vérifier particulièrement la paire détaillé/volumes de la vue modifiée.
4. Si nécessaire, corriger seulement les vues dépendantes incompatibles, dans le même cycle de correction. Ne pas faire dériver les autres vues pour s'aligner sur une erreur nouvelle.
5. Documenter improved/equivalent/regressed, les défauts restants et les contraintes effectivement préservées. Une régression interdit READY ; une équivalence n'est pas la preuve d'une amélioration.

Respecter a00 puis au plus trois corrections par jalon partagé. Changer de vue ou de skill ne remet pas le compteur à zéro. En cas d'outil/vision indisponible : BLOCKED. À épuisement avec défaut majeur : FAIL, meilleure tentative conservée.

## Livrer

Mettre à jour le nouveau manifeste avec les six chemins retenus, ou indiquer explicitement les vues absentes d'un ancien pack et son statut incomplet. Préserver toutes les versions antérieures. Le rapport comprend les comparaisons avant/après, les contrôles des autres angles, les propagations, les prompts et les limites. Afficher l'avant et l'après ciblés avec chemins absolus, puis lier le manifeste et le rapport.

Exemple : « Utilise $3d-refine-refpack-view sur le profil du côté du canon. Affine la profondeur du torse, conserve sa largeur de face et revalide le trois-quarts. »
