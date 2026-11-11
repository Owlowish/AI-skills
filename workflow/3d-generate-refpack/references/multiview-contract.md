# Contrat multivue et révisions du refpack

Ce contrat est partagé par 3d-generate-refpack et 3d-refine-refpack-view. Il concerne les images uniquement ; les révisions Blender restent gérées par 3d-reference-to-model.

Appliquer la [règle sans pilotage de l'écran](../../_shared/references/screen-control.md) ; la génération intégrée et l'inspection des fichiers restent les voies normales.

## Autorité et cohérence

Ordre d'autorité : observations des sources originales, choix explicitement demandés par l'utilisateur, hypothèses de conception documentées, images synthétiques. En cas de nouvelle demande qui contredit une source, consigner le changement de conception au lieu de prétendre à une meilleure fidélité.

Un profil synthétique est une proposition de profondeur. Ne pas considérer deux images générées concordantes comme deux preuves indépendantes. Une contradiction avec l'original prime sur leur accord.

Définir le flanc du profil par rapport au sujet, avec un repère visible (bras armé, porte, appendice). Enregistrer aussi le côté vu en trois-quarts. Conserver :
- pose, nombre de pièces, latéralité et équipement ;
- rapports entre masses, hauteurs des articulations et points d'appui, en tenant compte de la projection ;
- profondeur et raccords compatibles entre face, profil, dos et trois-quarts ;
- cadrage, proportion d'image, marges, fond, lumière et échelle visuelle pour chaque vue avant/après ;
- les courbures caractéristiques dans la simplification.

Une comparaison de silhouette à caméra mal appariée est inconclusive. Ne pas modifier la forme pour compenser une différence de perspective. Les paramètres d'une image générée sont des contraintes de prompt et des observations, pas une calibration de caméra garantie.

Le dos appartient au minimum requis, en détaillé et en volumes. Contrôler la continuité des flancs, les attaches et la répartition des matières et détails. Son niveau de finition doit suivre l'intention des autres faces, sans imposer le même nombre d'ornements. Les zones non observées restent des choix documentés ; une cohérence synthétique ne les transforme pas en observations. Une surface arrière laissée vide faute de référence constitue un défaut de conception à résoudre avant `READY`.

## Fichiers et manifeste

Pour un nouveau pack, choisir un identifiant libre r001 ; pour une nouvelle demande sur un pack terminé, r002, etc. Ne pas employer les compteurs de révision Blender à cette fin.

- Images : `references/refpack/rNNN/<famille>-<vue>-a00.png`, puis a01 à a03 pour les images corrigées.
- Manifeste final : `references/refpack/rNNN/manifest.json`.
- Rapport et journal : `reports/refpack/rNNN/`.
- Avant d'une révision : `reports/refpack/rNNN/before.json`, copie de l'ancien manifeste et des paramètres utiles, chemins et SHA-256 des fichiers retenus avant modification.

Tous les chemins du manifeste sont relatifs au projet. Préserver les anciennes images et rapports. Les huit entrées minimales retenues peuvent référencer des images inchangées de versions antérieures ; ne pas les dupliquer ni les régénérer sans raison. Les noms des profils doivent préciser leur flanc.

Le manifeste JSON contient :
- `standard` (`four-views-v2` pour les nouveaux packs), `revision`, `parent_revision`, `request`, `status` (IN_PROGRESS, READY, BLOCKED ou FAIL) ;
- `sources` (chemin, SHA-256, rôle), `authoritative_source` ;
- `view_contract` : pose, profil et repère de latéralité, orientation du dos, côté trois-quarts, projection/cadrage/échelle par vue, invariants et hypothèses, notamment le traitement des surfaces arrière non observées ;
- `views` : au moins les huit clés détaillées/volumes du tableau de 3d-generate-refpack, dont `detailed-back` et `volumes-back`, chacune avec chemin, SHA-256, famille, vue, côté, sources et références d'entrée, statut d'inspection et lien vers l'examen ;
- `stages` : detailed, volumes et éventuels détails ; essai courant, historique d'examens, corrections utilisées, meilleur ensemble retenu et problèmes restants ;
- `comparison` pour une révision : chemins avant/après par vue, changements, résultat improved/equivalent/regressed et contrôles des invariants.

Ce manifeste documente le travail ; aucun script de validation du refpack n'est fourni. Ne pas le présenter comme une garantie automatique de cohérence visuelle.

## Jalons et budget

Le jalon detailed couvre les quatre vues détaillées ; volumes couvre les quatre vues simplifiées et les quatre paires avec detailed. Chaque gros plan nécessaire constitue un jalon supplémentaire.

a00 est l'examen initial de l'ensemble ; trois cycles de corrections maximum donnent a01, a02 et a03. Un cycle peut modifier plusieurs vues dépendantes, puis exige un nouvel examen croisé de l'ensemble. Une image conservée peut garder un numéro antérieur : le manifeste établit l'ensemble examiné.

Consigner les défauts, leur gravité, les corrections réellement effectuées et le meilleur ensemble. Ne pas réinitialiser un compteur en changeant le nom d'une vue, en changeant de skill ou en créant une révision pendant un travail inachevé. Une panne d'outil ne consomme pas une correction. Au-delà de trois corrections insuffisantes, déclarer FAIL, conserver la meilleure version et arrêter la progression ; ne pas fabriquer huit entrées READY.

Une nouvelle demande sur un pack terminé ouvre une révision ; une tâche en cours reprend son budget. Une révision avec FAIL non résolu ne peut pas être renommée pour contourner la limite.

## Révision et avant/après

Avant toute édition, inspecter l'original et toutes les vues existantes, dont les huit vues minimales pour un pack au standard courant. Préserver le manifeste précédent et ses empreintes, fixer cible et invariants. Pour un ancien pack de deux ou six images, enregistrer honnêtement son standard et son périmètre dans before.json, sans modifier ses preuves ni son statut historique. Ne pas inventer les vues manquantes ni déclarer ce pack conforme à `four-views-v2`. La complétion, notamment l'ajout de `detailed-back` et `volumes-back`, suit 3d-generate-refpack lorsqu'elle fait partie de la demande ; une retouche locale seule signale cette limite et ne déclare pas un READY au nouveau standard.

Modifier la vue ciblée à cadrage comparable. Vérifier ensuite toutes les vues existantes, particulièrement sa paire détaillé/volumes. Si une correction révèle une hypothèse géométrique incohérente, réconcilier les seules vues affectées et documenter la propagation. Les éléments non concernés restent des invariants.

Pour chaque vue modifiée, ouvrir l'avant et l'après au même angle et à la même échelle ; pour chaque vue conservée, contrôler qu'elle reste compatible avec la correction. Une vue nouvellement créée n'a pas d'avant : indiquer « ajout ».

Une régression interdit READY. Une équivalence ne prouve pas qu'une amélioration demandée a eu lieu. Après une modification amont, revalider les jalons dépendants dans leur budget courant. Livrer le nouvel ensemble retenu et les comparaisons ciblées, avec les anciens fichiers accessibles.
