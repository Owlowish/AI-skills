---
name: 3d-review-consistency
description: "Examiner la cohérence d'un modèle Blender avec ses références sous plusieurs angles, relever les écarts et les régressions et prioriser les corrections. Audit visuel sans retouche automatique ni modification des PASS du projet."
---

# 3D — Vérifier la cohérence

Produire un diagnostic étayé par des images réellement inspectées. Ce skill peut servir avant une retouche ou pour contrôler une correction, sans déclencher de modification géométrique.

Appliquer la [règle sans pilotage de l'écran](../_shared/references/screen-control.md) : tout recours indispensable à une interface pilotée exige un accord explicite préalable dans le chat.

## Préparer l'examen

Lire AGENTS.md et les règles de [validation visuelle](../3d-reference-to-model/references/visual-validation.md). Vérifier Blender via le [prévol MCP](../3d-reference-to-model/references/blender-mcp.md). Lire project.yaml, analyse, rapports, sources et éventuel manifeste du refpack. Identifier le modèle exact et son état sauvegardé ou non.

Ouvrir l'original et les références pertinentes. Distinguer observations originales, hypothèses du refpack et choix utilisateur. Les huit images détaillées/volumes, dos inclus, servent de contrôles complémentaires ; leurs contradictions doivent être signalées, pas imposées simultanément au modèle. Signaler les vues manquantes d'un ancien pack sans inventer leur contenu.

Si Blender ou l'inspection effective manque, rendre un diagnostic BLOCKED. Si une référence manque, limiter explicitement la conclusion ; ne pas inventer le profil ou les parties cachées.

## Obtenir les preuves sans retouche

Examiner face, profil, dos et trois-quarts neutres, plus la vue ciblée s'il y en a une. Vérifier le côté du profil et l'appariement de caméra avec la référence. Ajouter un rendu matière pour juger couleurs et motifs ; le gris seul ne permet pas de les vérifier.

Réutiliser des captures existantes uniquement si leur empreinte de maître correspond à l'état examiné et si le modèle n'a pas de modifications non sauvegardées ; les ouvrir à nouveau. Sinon capturer réellement l'état courant via Blender MCP, avec cadrage et éclairage reproductibles, en conservant puis en rétablissant les réglages temporaires. Sauvegarder les nouvelles preuves dans un dossier libre `previews/review/<audit-id>/`, et noter les réglages et l'identité du modèle. Un état non sauvegardé doit être déclaré comme tel ; le hash du fichier sur disque ne le représente pas.

Ne pas retoucher la géométrie, les matériaux ou les références pour rendre l'audit favorable. Ne pas écraser le maître, les preuves ou les rapports existants. Ne pas ouvrir de révision pour un simple audit. Les helpers prepare/record refusent certaines opérations sur un jalon PASS : ne pas les contourner pour enregistrer cet examen indépendant.

## Comparer les formes

Contrôler séparément :
- **Face** : largeurs, rapports tête/torse/bassin, disposition des membres, symétries voulues et équipement asymétrique.
- **Profil** : profondeur, épaisseur, porte-à-faux, jonctions, appuis et alignement des articulations.
- **Trois-quarts** : silhouette globale, raccords, occultations, espaces négatifs et lisibilité de la pose.
- **Dos** : comparer les références arrière détaillée et simplifiée, les assemblages, les attaches et la finition par rapport aux autres faces. Relever un dos anormalement sommaire sans raison de conception. Sans référence arrière originale, distinguer cohérence du choix synthétique et fidélité à une observation.
- **Références simplifiées** : conservation des courbures et masses caractéristiques, sans généraliser les formes en boîtes.
- **Matières/détails** : identité des pièces, nombre et placement des éléments, détails flottants, couleurs et motifs.

Un audit de normales, doublons ou faces dégénérées complète l'examen sans le remplacer. Ne pas conclure à une ressemblance suffisante au seul motif que le sujet est reconnaissable ou que les fichiers sont valides.

## Comparaison d'une révision

Si un état avant est disponible, ouvrir les cinq images avant et les cinq après prévues par le [workflow de révision](../3d-reference-to-model/references/targeted-retouch.md). Vérifier l'identité des caméras, de la résolution et de l'éclairage, puis examiner amélioration ciblée et conservation des autres angles.

Si les cadrages diffèrent ou si l'avant n'existe pas, déclarer la comparaison inconclusive et expliquer la preuve manquante. Ne pas reconstituer un faux avant. Une nouvelle vue n'est pas une comparaison avant/après. Un résultat équivalent n'atteste pas une amélioration demandée.

## Rapport et suite

Écrire un rapport inédit `reports/review/<audit-id>.md` avec :
- modèle/état examiné, sources et fichiers réellement ouverts, paramètres des vues et éventuelles lacunes ;
- observations par angle et éventuelles contradictions du refpack ;
- au plus trois défauts prioritaires, chacun avec gravité, pièce, vue, écart visible, conséquence, invariant à préserver et jalon à reprendre ;
- pour une révision, paires avant/après, improved/equivalent/regressed et contrôles des contraintes ;
- verdict indépendant : CONFORME AU PÉRIMÈTRE EXAMINÉ, ÉCARTS À CORRIGER, INCONCLUSIF ou BLOCKED, avec limites.

Ce verdict ne modifie ni project.yaml, ni les PASS, ni les compteurs. Une correction géométrique autorisée explicitement par l'utilisateur peut ensuite suivre [3d-refine-view](../3d-refine-view/SKILL.md). Une contradiction des images relève de [3d-refine-refpack-view](../3d-refine-refpack-view/SKILL.md). Un simple audit se termine par le diagnostic et les corrections proposées.

Exemple : « Utilise $3d-review-consistency pour comparer le robot à la face, au profil et au trois-quarts, et classer les trois écarts les plus importants. »
