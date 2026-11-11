---
name: 3d-refine-view
description: "Retoucher un modèle Blender existant depuis une vue ciblée, face, profil ou trois-quarts. Conserver la version précédente, comparer avant/après à caméra fixe et revalider les autres angles et jalons affectés."
---

# 3D — Retoucher une vue du modèle

Corriger la géométrie réelle à partir d'un angle choisi, en conservant les acquis du modèle et en contrôlant les autres vues.

## Workflow requis

Lire [3d-reference-to-model](../3d-reference-to-model/SKILL.md), son [workflow de retouche ciblée](../3d-reference-to-model/references/targeted-retouch.md), la [validation visuelle](../3d-reference-to-model/references/visual-validation.md) et les [commandes de projet](../3d-reference-to-model/references/project-tools.md). Réutiliser ces outils et états ; ne pas créer un système de révision parallèle ni modifier les scripts ou le manifeste pour contourner un verrou.

Une installation de skill n'autorise pas une retouche. Pour une demande réelle, lire AGENTS.md, vérifier l'accès réel à Blender MCP selon [le prévol](../3d-reference-to-model/references/blender-mcp.md), inspecter scène et fichier chargés et préserver le travail existant. Blender est obligatoire ; aucun moteur ou générateur 3D externe payant.

## Vue, cible et contraintes

Lire project.yaml, analyse, rapports et références. Ouvrir réellement les sources originales, les vues du refpack pertinentes et les rendus précédents. Une vue synthétique ne l'emporte pas sur une observation originale.

Identifier vue, côté, pièces, défauts et invariants. Pour face/profil, contrôler largeur ou profondeur ; pour trois-quarts, contrôler raccords et silhouette. Consigner les axes : face -Y, haut +Z dans la convention du projet. Définir la vue par une direction de la cible vers l'œil ; le profil depuis -X n'est pas automatiquement le « profil gauche » anatomique. Déduire le côté des asymétries visibles ou clarifier s'il reste structurant.

Adapter la vue ciblée à la référence en tenant compte de sa perspective. Garder les caméras avant/après fixes ; ne pas déplacer la caméra, modifier la lumière ou aplatir le modèle pour faire disparaître un écart. Les paramètres estimés ne constituent pas une calibration exacte.

Choisir le premier jalon affecté :
- silhouette, proportions ou pose : blockout ;
- forme locale, épaisseur ou raccord : geometry ;
- détail ou matériau sans volume majeur : refinement ;
- présentation ou export seulement : finalization.

Le nom de ce skill ne force pas la reprise à refinement. Une correction de proportions rouvre les étapes antérieures nécessaires.

## Révision et état avant

Sur une livraison COMPLETE intègre, utiliser `project.py revise` avec la demande, le premier jalon, les `--target`, les `--preserve` et `--view-direction`. Suivre les commandes du workflow lié : elles préservent `model-before-rNNN.blend`, le manifeste et le rig, et rouvrent les jalons concernés.

Avant toute modification, lancer `blender_previews.py prepare-before`, exécuter son code via MCP, puis `finish-before`. Ouvrir les cinq vues avant : front, side, back, three-quarter et focus. Garder exactement rig, résolution et éclairage pour l'après. Si le focus ne convient pas, traiter ce problème avant de toucher au modèle, selon le workflow existant.

Pour un jalon ou une révision déjà en cours, continuer son cycle et son budget ; ne pas appeler revise pour le remettre à zéro. Préserver l'état courant avant une nouvelle retouche : utiliser les preuves correspondantes si elles représentent exactement cet état, sinon enregistrer une copie et des captures avant distinctes sans écraser les essais. Le helper prepare-before exige une révision : ne pas prétendre qu'il fonctionne hors de ce mode. Les comparaisons complémentaires d'un travail en cours ne remplacent pas les captures canoniques exigées par le jalon.

## Modifier, comparer et revalider

Corriger les pièces ciblées dans Blender, avec leurs détails liés : coque, optiques, motifs et fixations doivent suivre ensemble. Conserver l'éditabilité. Ne pas reconstruire un modèle livré à partir de primitives pour une correction locale.

Après modification :
1. Sauvegarder le maître et produire les captures après avec les helpers compatibles avec l'état du projet.
2. Ouvrir les cinq vues avant et après de la révision, ainsi que les sources. Comparer la vue ciblée puis toutes les autres.
3. Décrire l'amélioration observée et vérifier chaque invariant déclaré. Une amélioration locale avec régression ailleurs interdit PASS.
4. Remplir le rapport réel, notamment `comparison.changes`, `comparison.observations`, `comparison.outcome` et `comparison.preservation_checks`. Inclure les dix chemins inspectés pour une révision. À attempt-00, les changements demandés vont dans comparison.changes ; corrections reste vide.
5. Revalider le premier jalon concerné et tous les suivants. Garder seulement les PASS antérieurs réellement non affectés.

Un audit technique sans erreur ne suffit pas à prouver la ressemblance. Si une conséquence invalide un jalon plus ancien que prévu, expliquer les validations supplémentaires nécessaires et respecter le traitement du workflow existant, sans forcer son PASS.

Examen initial puis trois corrections maximum par jalon ; aucun changement de vue ne réinitialise le budget. Après échec persistant, garder/restaurer le meilleur checkpoint et arrêter en FAIL. Blender, captures ou vision indisponibles : BLOCKED, sans validation simulée.

## Livraison

Terminer avec audits appropriés, sauvegarde/réouverture du maître et `project.py validate --complete`. Réexporter seulement les formats demandés et les vérifier selon le workflow. Conserver les nouveaux rapports, checkpoints et exports dans l'espace rNNN ; ne pas écraser les rapports antérieurs.

Fournir maître, version précédente, comparaison avant/après ciblée affichée, contrôles des autres angles et limites réelles.

Exemple : « Utilise $3d-refine-view sur le profil du côté du canon. Réduis la profondeur du torse ; préserve la largeur de face, les matériaux et les détails. »
