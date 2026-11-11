---
name: 3d-pose-model
description: Mettre un modèle Blender existant en pose depuis une consigne écrite ou une image de référence. Réutiliser son rig ou ses éléments rigides, conserver les variantes et contrôler appuis, articulations et collisions sous plusieurs angles.
---

# 3D — Mettre un modèle en pose

Produire une attitude lisible et cohérente, sans altérer le maître de sculpture ou le rig source. Ce skill crée des poses ; une séquence animée complète est un besoin distinct.

Appliquer la [règle sans pilotage de l'écran](../_shared/references/screen-control.md) : tout recours indispensable à une interface pilotée exige un accord explicite préalable dans le chat.

## Source et variante

Lire AGENTS.md, le projet, les rapports et le [contrat des variantes](../_shared/references/derived-workflow.md). Vérifier accès Blender MCP, scène chargée et travail non sauvegardé selon le [prévol](../3d-reference-to-model/references/blender-mcp.md).

Pour un sujet articulé, utiliser une variante rig validée par [3d-rig-model](../3d-rig-model/SKILL.md). Inspecter et tester un rig existant non documenté avant usage, sans le reconstruire par défaut. Un objet fixe peut utiliser les transformations de ses éléments dans une variante statique.

Créer un run pose distinct, lié à l'empreinte du rig ou du modèle statique approuvé. Chaque pose a son label et son historique. Charger la source puis sauvegarder la variante via Blender en remappant les ressources relatives.

## Interpréter l'intention

Lire [pose-reference.md](references/pose-reference.md) pour une image ou une demande ambiguë. Déduire action, regard, ligne de mouvement, appuis et accessoires concernés. « Pose dynamique de combat » autorise une proposition concrète et ses corrections ordinaires ; clarifier seulement un choix structurant non inférable.

Ouvrir réellement la référence, préserver l'original et documenter perspective et membres masqués. Une image 2D ne calibre pas les profondeurs. Préserver identité, proportions et latéralité.

## Construire et contrôler

Utiliser les commandes du rig ; ne pas déplacer indépendamment les pièces attachées pour simuler une bonne pose dans une seule vue. Adapter vérins, genouillères, accessoires et appuis. Respecter les limites articulaires ou signaler celles qui empêchent la pose.

Conserver l'échelle entre poses : une figurine accroupie ne doit pas être agrandie pour retrouver automatiquement sa hauteur debout. Rapporter les dimensions posées ; elles ne deviennent des millimètres que si l'échelle physique est définie.

Inspecter face, profil, dos et trois-quarts, à cadrages avant/après constants, et une vue proche de la référence si utile. Contrôler collisions, étirements, pièces oubliées, contacts main/arme et pied/sol, équilibre visuel et angles cachés. Pour une future figurine, signaler les appuis ou soutiens de décor nécessaires.

## Validation et suite

Sauvegarder, rouvrir la variante et remplir les checks pose du contrat partagé. Examen initial puis trois corrections maximum ; préserver le meilleur état et les poses précédentes. Sans capture ou inspection : BLOCKED.

Livrer le .blend posé, les vues comparatives et les limites observées. Si la demande enchaîne explicitement pose et impression, poursuivre avec [3d-prepare-fdm](../3d-prepare-fdm/SKILL.md) après contrôle. Si l'utilisateur demande de choisir ou valider une pose avant impression, présenter cette pose concrète puis attendre ce choix.
