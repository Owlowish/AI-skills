---
name: 3d-reference-to-model
description: Créer, reprendre ou retoucher un modèle Blender depuis des références, avec révisions conservées, comparaisons visuelles et corrections bornées via Blender MCP.
---

# 3D — Modéliser depuis une référence

Produire dans Blender un modèle éditable fidèle aux caractéristiques observables des sources. Adapter les techniques aux sujets organiques, hard-surface ou hybrides ; les primitives de blockout ne constituent pas un résultat organique final.

Appliquer la [règle sans pilotage de l'écran](../_shared/references/screen-control.md) : tout recours indispensable à une interface pilotée exige un accord explicite préalable dans le chat.

## Démarrer ou reprendre

Pour une installation ou une préparation documentaire seule, respecter cette limite : créer/analyser les fichiers autorisés sans commencer la scène 3D. Un prévol non demandé ou hors périmètre reste « non vérifié », sans inventer un BLOCKED. L'accès effectif à Blender devient obligatoire avant toute modélisation.

1. Lire `AGENTS.md` à la racine de l'espace. Résoudre les scripts relativement à ce skill.
2. Avant de commencer/reprendre la modélisation, vérifier les outils réels selon [references/blender-mcp.md](references/blender-mcp.md), puis faire un appel de lecture à Blender avant toute modification. Une configuration ou un succès Python ne prouve pas l'accès à la scène. Utiliser Blender MCP, y compris `bpy` via son outil d'exécution. Blender background convient aux tâches appropriées sur copie sauvegardée ; ne pas s'en servir pour contourner silencieusement un MCP inaccessible. Aucun autre moteur, service 3D payant ou installation de modèle IA 3D.
3. Sans référence fournie, préparer ou diagnostiquer seulement l'installation. Sinon, ouvrir réellement toutes les images sources, puis utiliser `scripts/project.py new --repo <racine> --slug <nom> --reference <image>` (option répétable). Pour une reprise, lire `project.yaml`, les rapports et le meilleur checkpoint, puis lancer `scripts/project.py validate <projet>`. Ne pas recréer ni écraser le projet.
4. Si la modélisation est autorisée, examiner la scène ouverte et son chemin. Préserver tout travail existant avant de charger un autre fichier. Ne pas vider arbitrairement la scène utilisateur. Le maître est `projects/<slug>/blender/model.blend` ; regrouper la géométrie de production dans `MODEL`.
5. Suivre [references/workflow.md](references/workflow.md). Avant un jalon, lire [references/visual-validation.md](references/visual-validation.md). Les commandes et données sont décrites dans [references/project-tools.md](references/project-tools.md).

## Retouche ciblée après livraison

Pour modifier un modèle terminé (profil, proportions, pièce, détail, matériau ou présentation), lire [references/targeted-retouch.md](references/targeted-retouch.md). Déduire le périmètre de la demande et les éléments à préserver ; choisir le premier jalon affecté. Ouvrir une révision avec `project.py revise`, puis capturer et inspecter l'état **avant toute modification**. Conserver les pièces et détails existants ; rouvrir un jalon signifie réexaminer ce modèle, pas le reconstruire depuis des primitives.

La version précédente et ses preuves restent intactes. Chaque jalon rouvert exige les quatre vues neutres plus une vue ciblée, avant/après avec les mêmes caméras, résolution et éclairage, et un rapport de comparaison. Revalider le jalon concerné et tous les suivants ; conserver les PASS antérieurs non affectés. Ne pas contourner les verrous PASS en éditant le manifeste ni lancer une autre révision pour réinitialiser un cycle encore en cours. Une demande d'installation de ce mode n'autorise pas à retoucher le modèle lui-même.

## Contrat de progression

- Jalons : `blockout`, `geometry`, `refinement`, `finalization`, dans cet ordre. Chaque passage exige une inspection visuelle effective des captures Blender et une comparaison aux sources. Ni existence des fichiers, ni audit du maillage, ni absence d'erreur de script ne remplace cette inspection.
- Pour chaque jalon : captures neutres reproductibles, examen réel, au plus trois défauts prioritaires, corrections puis nouvelles captures et nouvel examen. `attempt-00` est l'examen initial ; trois corrections donnent au maximum `attempt-01` à `attempt-03`.
- Un défaut majeur non résolu interdit `PASS` et le jalon suivant. Après trois corrections insuffisantes, conserver/restaurer la meilleure version, déclarer `FAIL` et arrêter la progression. Une exception nécessite une justification explicite dans `project.yaml` et dans le rapport avant tout dépassement ; ne jamais relever la limite automatiquement.
- Si Blender, la capture ou l'inspection visuelle manque, déclarer le jalon `BLOCKED`, expliquer le problème et arrêter la modélisation. Ne pas inventer de validation. Les scripts vérifient des preuves déclarées ; seul l'agent ayant effectivement vu les images peut attester l'examen.
- Continuer de manière autonome tant que les jalons passent. Solliciter l'utilisateur seulement pour une ambiguïté structurante non résoluble par une hypothèse raisonnable, ou pour protéger un travail existant.

## Références et livraison

Conserver les originaux intacts dans `references/source/`. Consigner les surfaces cachées et les interprétations ; une vue perspective n'est pas un plan coté. Une vue trois-quarts peut suffire : aucune fiche multivue systématique.

Lorsqu'un refpack est fourni, exploiter aussi `detailed-back` et `volumes-back`, puis vérifier leurs raccords avec le profil et le trois-quarts. Développer les surfaces arrière avec une finition cohérente avec les autres faces. Si un ancien pack n'a pas de dos, signaler cette lacune et documenter les choix arrière ; ne pas laisser cette absence produire un dos sommaire sans justification, ni générer automatiquement un nouveau pack hors demande.

Les auxiliaires IA sont facultatifs et réservés à un besoin précis. Utiliser un outil effectivement disponible, sans facturation supplémentaire établie, après lecture de son skill disponible. Les conserver dans `references/generated/` avec provenance et hypothèse, puis les inspecter contre les originaux. Ils ne font jamais autorité sur la géométrie ; continuer sans eux si l'outil ou les conditions de coût sont inconnus.

Livrer le `.blend`, les rendus inspectés, les seuls exports demandés, les décisions et limites réelles. Impression 3D, volumes systématiquement fermés, rigging et topologie de jeu sont des options sur demande. Ne jamais annoncer une qualité ou une capacité non testée.
