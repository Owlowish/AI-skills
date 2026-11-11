# Préparer la fabrication

## Géométrie et dimensions

La variante d'impression utilise la géométrie évaluée de la pose. Conserver le rig et les courbes éditables dans la source ; convertir les courbes utiles en solides sur la copie. Couleurs et shaders ne sont pas des reliefs STL.

Vérifier normales, dégénérescences, bords ouverts/nonmanifold, intersections, doublons et petits îlots. Fusionner les volumes d'une même pièce lorsque leurs recouvrements rendraient l'export ambigu. Après booléens ou remeshing, vérifier conservation des détails et des plans d'armure.

Appliquer l'échelle physique une fois. Rapporter les dimensions et les vérifier après réimport ; STL n'encode pas d'unité explicite.

## Socle

Définir emprise, débords, bord, épaisseur et attaches. Un décor peut recevoir tige, rocher de soutien, logement ou pions. Préserver accès aux supports et robustesse du décor.

La stabilité dépend de la pose, de la masse imprimée, du remplissage et des accessoires. Une estimation n'est pas un test physique. Un socle de jeu suit le format visé lorsqu'il est spécifié.

## Stratégie de pièces

Comparer les options pertinentes :
- Monobloc : peu de montage, mais surplombs, accès aux supports et petits appuis parfois défavorables.
- Assemblage : orientations et supports mieux maîtrisés, avec joints et collage.
- Mixte : corps principal, accessoires ou socle séparés.

Placer les coupes discrètement, avec sections de collage suffisantes et détrompeurs utiles. Adapter les jeux aux paramètres réels ; proposer un petit test de tenon/logement lorsque nécessaire. Vérifier le chemin d'insertion : un tenon ne doit pas être coincé par des pièces déjà assemblées.

Les unités de fabrication peuvent regrouper plusieurs objets Blender ou diviser une coque. Fournir une orientation proposée par pièce et une vue assemblée puis éclatée.

## Slicer

Appliquer la [règle sans pilotage de l'écran](../../_shared/references/screen-control.md). Réimporter les STL finaux avec profil machine et buse exacts par une API/CLI appropriée lorsqu'elle existe. Après tranchage, ouvrir les véritables aperçus de couches enregistrés autour des premiers îlots, petits appuis, doigts, antennes, tenons et joints. Vérifier détails disparus, parois, supports internes inaccessibles et marques sur les surfaces visibles. Une simple ouverture de l'application ou un rendu du maillage ne remplace pas ces preuves.

Si une interface pilotée est indispensable pour une vérification demandée, expliquer ce blocage et attendre l'accord explicite dans le chat avant de lancer le contrôle. En l'absence de cet accès autorisé, conserver la livraison géométrique validée en GEOMETRY_PREPARED, avec « tranchage non vérifié ».

Temps et consommation viennent du slicer réellement exécuté. Conserver paramètres, captures et éventuel projet 3MF. Sans inspection du tranchage, le livrable reste GEOMETRY_PREPARED.

## Formats

- [FAQ STL/3MF](https://3mf.io/resources/faq/).
- [Spécification 3MF et unités](https://3mf.io/wp-content/uploads/sites/106/2025/02/3MF_Core_Specification_v1.3.0.pdf).
