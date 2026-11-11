---
name: 3d-generate-refpack
description: "Créer un refpack cohérent d'au moins huit images depuis une source : face, profil identifié, dos et trois-quarts, en références détaillées puis en volumes simplifiés. Utiliser pour préparer les références d'une modélisation, sans lancer Blender."
---

# 3D — Générer un refpack

Livrer au moins huit véritables images générées du même sujet, puis vérifier leurs correspondances, dos inclus. Les images originales font autorité ; un angle synthétique précise une hypothèse de conception, pas une observation supplémentaire.

Appliquer la [règle sans pilotage de l'écran](../_shared/references/screen-control.md) : tout recours indispensable à une interface pilotée exige un accord explicite préalable dans le chat.

Pour toute production ou reprise, lire le [contrat multivue et de révision](references/multiview-contract.md). Pour une retouche locale d'un pack existant, suivre [3d-refine-refpack-view](../3d-refine-refpack-view/SKILL.md).

## Périmètre et disponibilité

Skill autonome de préparation d'images : ne pas invoquer `3d-reference-to-model`, créer de scène ou lancer automatiquement Blender. Une installation ou modification de ce skill seule n'autorise pas à produire un pack.

Employer l'outil de génération intégré réellement exposé dans la session, de préférence `image_gen`, après lecture de son schéma et du skill imagegen disponible. Aucun service externe payant supplémentaire, clé API, API facturée séparément, CLI de remplacement ou modèle génératif local. Ne pas promettre un quota illimité.

La première image demandée sert de vérification fonctionnelle : annoncer « outil détecté » avant l'appel, puis « génération vérifiée » après réception et inspection d'un fichier exploitable. Ne pas produire un test supplémentaire à chaque exécution. Si l'outil, la sauvegarde ou l'inspection visuelle manque, annoncer `BLOCKED` avec le résultat réel. Une seule relance pour une erreur transitoire clairement identifiée ; ne jamais substituer des descriptions, prompts, dessins programmatiques ou rendus Blender aux images demandées.

## Sources et analyse

Ouvrir réellement toutes les sources. Si une source manque, demander son fichier ou son chemin. Isoler le projet dans `projects/<nom>/` ; ne pas écraser un projet homonyme sans rapport avec la demande.

Copier les originaux octet pour octet dans `references/source/`, sans modifier les entrées, leur résolution, leurs métadonnées ni leur transparence. Vérifier les SHA-256 avant/après ; un recadrage de travail reste un dérivé. Si la récupération intégrale est impossible, signaler le blocage sans remplacer l'original par une capture.

Décrire sujet, pose, silhouette, masses, appuis, pièces distinctives, couleurs et matériaux. Distinguer **observé**, **ambigu** et **choisi**, avec raison et confiance. Relever les proportions projetées utiles sans inventer de dimension réelle ni confondre raccourcissement et taille 3D.

Fixer dans le manifeste :
- pose et disposition spatiale communes aux huit images ;
- face et côté du profil, repérés par rapport au sujet et à ses asymétries, jamais par « gauche de l'image » seul ;
- côté du trois-quarts, direction du regard, orientation du dos opposée à la face, projection recherchée, cadrage et échelle visuelle ;
- repères à conserver : sommets, articulations, centres des masses, appuis, ouvertures et raccords ;
- choix explicites de profondeur et de surfaces cachées.

Choisir le profil le plus informatif, par exemple celui de l'équipement distinctif. Si le côté demandé reste ambigu et change réellement la construction, poser une question ciblée. Sinon annoncer et consigner le choix. Conserver la pose source par défaut ; ne pas passer silencieusement en pose neutre.

Si le dos n'est pas visible dans les originaux, définir son traitement comme une hypothèse de conception : continuité des pièces et des matériaux, jonctions, équipements et détails plausibles. Préserver le même niveau de finition et le même langage de formes que les autres faces. Pour un robot, examiner par exemple panneaux, fixations, refroidissement et raccords des équipements ; adapter les détails au sujet au lieu d'ajouter des ornements arbitraires. Une surface arrière volontairement simple doit avoir une raison de conception documentée, pas résulter de l'absence de référence.

## Produire les huit références minimales

| Famille | Face | Profil identifié | Dos | Trois-quarts |
| --- | --- | --- | --- | --- |
| Détaillée / artistique | `detailed-front` | `detailed-profile-left` ou `-right` | `detailed-back` | `detailed-three-quarter` |
| Volumes simplifiés | `volumes-front` | `volumes-profile-left` ou `-right` | `volumes-back` | `volumes-three-quarter` |

Chaque case est un fichier distinct et inspectable. Une planche peut compléter la comparaison, mais ne remplace pas les huit fichiers. Le profil détaillé et simplifié montrent le même flanc. Le dos est obligatoire dans les deux familles ; les autres angles et gros plans restent conditionnels.

1. Générer d'abord la référence détaillée la plus proche de la source, généralement le trois-quarts. Garder le sujet entier, fond neutre, lumière douce, identité, asymétries et proportions. La finition artistique doit faciliter la lecture des formes.
2. Après inspection, générer face et profil en réutilisant l'original et les références pertinentes retenues, puis le dos avec ces ancrages et les hypothèses arrière documentées. Changer le point de vue, pas la pose, l'équipement ou la morphologie. Ne jamais créer quatre interprétations indépendantes à partir du seul texte ; un dos n'est pas une face retournée en miroir.
3. Examiner les quatre images détaillées ensemble. Contrôler en particulier les raccords du dos avec les flancs, les éléments visibles en trois-quarts, la latéralité, les couleurs et le niveau de finition. Corriger leurs contradictions avant de simplifier. Une image individuellement séduisante ne suffit pas.
4. Générer chaque vue de volumes à partir de l'original, de sa vue détaillée correspondante et des autres repères utiles. Garder le même cadrage et le même côté pour chaque paire. Employer des matériaux mats neutres et des masses lisibles.
5. Simplifier textures, petits ornements et microdétails tout en conservant courbures caractéristiques, profil, épaisseurs, raccords, espaces négatifs et rapports de taille. Ne pas remplacer systématiquement les coques courbes par des boîtes.
6. Inspecter les quatre volumes entre eux, puis chacune des quatre paires détaillé/volumes. La simplification du dos conserve ses équipements, épaisseurs, raccords et masses distinctives.

Pour face, profil et dos, demander une projection orthographique apparente ou à faible perspective, sans la présenter comme un plan coté exact. La rotation du point de vue peut déplacer visuellement les articulations d'une pose asymétrique : comparer les relations spatiales, pas imposer les mêmes coordonnées pixel partout.

Avec `image_gen`, ouvrir les fichiers locaux via `view_image` avant de les transmettre. Employer `referenced_image_paths` si toutes les entrées ont un chemin, sinon le minimum nécessaire de `num_last_images_to_include`, dans la limite réelle de l'outil ; jamais les deux. Si les entrées nécessaires ne peuvent être transmises, demander qu'elles soient jointes à nouveau. Lister leur rôle dans le prompt ; l'original reste prioritaire même lorsque plusieurs images synthétiques sont utilisées.

Copier chaque sortie réelle de l'outil dans `projects/<nom>/references/refpack/` selon le contrat. Ne pas inventer le chemin de sortie ni un argument de destination. Rouvrir les fichiers finaux.

## Comparaison et corrections

Appliquer les contrôles croisés et le budget du contrat. Pour chaque examen, ouvrir réellement les images concernées et identifier au plus trois défauts prioritaires. Examiner notamment :
- face : largeurs, proportions, position des membres, asymétries et espaces négatifs ;
- profil : profondeur, porte-à-faux, alignement des articulations, épaisseurs et appuis ;
- dos : continuité avec les flancs, attaches des équipements, détails fonctionnels, répartition des matériaux et finition cohérente avec les autres faces ;
- trois-quarts : raccords entre les dimensions, superpositions, silhouette et cohérence de la pose ;
- chaque paire détaillé/volumes : conservation de la géométrie caractéristique.

Ne pas masquer une contradiction avec du détail, un matériau, une lumière ou un changement de caméra. Si une référence amont change, revalider ses dépendances et les vues déjà retenues. Aucun majeur non résolu ne permet de passer au jalon suivant.

Produire un gros plan seulement si une zone nécessaire à la construction reste illisible ; justifier son apport. Il ne peut pas rendre connue une face cachée.

## Rapport et livraison

Dans le rapport versionné, fournir sources et empreintes, manifeste des huit vues minimales retenues, repères de proportions, hypothèses et confiance, paramètres de cadrage, prompts exacts et entrées de chaque appel (éventuellement en journal lié), observations par vue et croisées, essais et corrections, avant/après pour une révision, version retenue et limites. Distinguer explicitement les détails arrière observés de ceux conçus pour compléter les surfaces cachées.

Déclarer `READY` seulement après inspection des huit fichiers finaux, cohérence des deux ensembles de quatre vues et des quatre paires, dos suffisamment défini pour la construction, absence de majeur, sources intactes et rapport complet. Si la capacité manque, `BLOCKED` ; si le budget de corrections est épuisé sans résultat acceptable, `FAIL`, avec meilleure tentative préservée. Fournir les images et le rapport, sans déclencher de modélisation.
