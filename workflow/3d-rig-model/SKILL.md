---
name: 3d-rig-model
description: Préparer et valider un rig Blender adapté à un modèle 3D existant, organique, mécanique ou hybride. Préserver le modèle approuvé et tester les articulations avant une mise en pose ou une animation.
---

# 3D — Articuler un modèle

Créer une copie articulable du modèle approuvé. Un rig validé prépare la mise en pose ; la création d'une séquence animée et la préparation d'impression sont des tâches distinctes.

Appliquer la [règle sans pilotage de l'écran](../_shared/references/screen-control.md) : tout recours indispensable à une interface pilotée exige un accord explicite préalable dans le chat.

## Source et prévol

Lire AGENTS.md, le projet et ses rapports. Appliquer le [prévol Blender MCP](../3d-reference-to-model/references/blender-mcp.md) : accès réel, scène, chemin et travail non sauvegardé vérifiés avant toute mutation. Aucun générateur 3D payant ou installation de modèle IA local.

Lire le [contrat des variantes](../_shared/references/derived-workflow.md), puis créer un run rig avec le helper associé. Conserver blender/model.blend et les références intacts. Sauvegarder la variante depuis Blender en remappant les ressources relatives ; une simple copie dans un autre dossier ne remappe pas les textures.

Ouvrir la source et ses rendus. Relever les pièces liées, pivots, symétries, unités, modificateurs et dépendances. Réutiliser un rig existant s'il convient. Garder détails, matériaux et apparence au repos.

## Adapter le rig

Lire le mode utile de [rig-types.md](references/rig-types.md).

- Organique : armature de déformation, topologie ou cage adaptée, pondérations contrôlées autour des articulations.
- Mécanique : pivots et liaisons rigides ; déplacer ensemble coque, vis, optique, panneaux et marquages. Articuler vérins et pièces dépendantes sans ramollir l'armure.
- Hybride : séparer les surfaces déformables et les éléments rigides.
- Objet fixe : identifier les parties réellement mobiles. Un bâtiment statique ne nécessite pas de squelette ; orienter vers une variante statique de pose ou directement vers la préparation FDM.

Choisir les commandes selon les mouvements attendus, les nommer et documenter leurs axes et limites. Préserver les transformations mondiales lors du parentage et prévenir les doubles transformations. Employer l'IK lorsqu'elle simplifie les appuis ; aucun squelette humanoïde imposé à tous les sujets.

Une retopologie ou cage reste une variante de travail, sans remplacer la sculpture approuvée. Comparer son résultat détaillé au repos sous les mêmes vues ; rouvrir la validation de forme si l'apparence change significativement.

## Validation et livraison

Capturer avant/après au repos à cadrages constants et tester les amplitudes utiles. Ouvrir réellement face, profil, dos et trois-quarts, puis les gros plans d'articulation nécessaires.

Contrôler forme au repos, commandes utilisables, liaisons et détails entraînés, amplitudes, collisions, échelle et pièces oubliées. Une pondération automatique n'est pas une validation. Revenir au repos dans le fichier livré, garder les poses d'essai disponibles et rouvrir réellement la variante sauvegardée.

Renseigner les checks rig du contrat partagé et enregistrer l'examen réel. Examen initial puis trois corrections maximum ; outil ou inspection indisponible : BLOCKED. Conserver le meilleur état en cas d'échec.

Livrer le .blend articulé, les vues inspectées, la carte des commandes et objets liés, les amplitudes testées et les limites. Ne pas annoncer d'animation produite ou d'aptitude d'impression non testée.
