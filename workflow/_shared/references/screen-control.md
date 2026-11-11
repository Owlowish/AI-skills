# Travail sans pilotage de l'écran

Cette règle s'applique à tous les skills du workflow 3D, y compris à leurs diagnostics et outils de secours.

## Voie par défaut

Utiliser les outils intégrés, Blender MCP et son API `bpy`, les API ou CLI disponibles, les fichiers locaux et les rendus produits sans pilotage d'interface. L'inspection d'un PNG rendu par Blender ou d'un aperçu de couches enregistré reste une inspection réelle ; elle ne nécessite pas de prendre la souris ou le clavier.

Ne pas initialiser un outil de contrôle d'écran, lancer une application graphique pour la piloter, activer une fenêtre, cliquer, saisir, envoyer des raccourcis ou déplacer des éléments d'interface par commodité. Une automatisation d'interface en arrière-plan reste un pilotage et suit la même règle. Vérifier qu'une commande est réellement utilisable sans interface avant de la lancer comme solution de fond.

## Exception sur accord dans le chat

Si une étape demandée est réellement bloquée et qu'aucune voie adaptée sans interface ne permet de l'effectuer :

1. Expliquer dans le chat le blocage constaté, les solutions sans pilotage examinées et pourquoi elles ne suffisent pas.
2. Préciser l'application, les actions nécessaires et leur périmètre, puis demander explicitement l'accord pour ce pilotage.
3. Attendre la réponse avant tout appel de contrôle d'écran. L'absence de réponse, la disponibilité d'un outil ou l'invocation du skill ne valent pas accord.

Un accord explicite déjà donné pour les mêmes actions et le même objectif reste valable dans son périmètre ; ne pas le redemander à chaque étape. Un refus, un retrait d'accord ou un arrêt du contrôle doit être respecté. L'accord ne remplace pas les autres limites du workflow, notamment la préservation des ressources et l'absence de lancement d'impression.

Continuer les travaux indépendants autorisés pendant l'attente. Si l'utilisateur préfère effectuer l'étape lui-même, lui fournir des instructions précises puis examiner les résultats qu'il transmet. Consigner la limite réelle plutôt qu'inventer une validation.

## Cas de la préparation FDM

La présence d'un slicer graphique n'autorise pas à le piloter. Préférer ses API/CLI documentées et les fichiers d'aperçu réellement exploitables. Une vue du modèle non tranché ne remplace pas un aperçu de couches.

Si le tranchage ou son inspection ne sont pas disponibles sans pilotage, terminer les contrôles de géométrie possibles et livrer `GEOMETRY_PREPARED`, avec « tranchage non vérifié ». Cette étape facultative ne bloque pas la livraison de STL géométriquement validés. Si la demande exige `SLICER_VERIFIED` et qu'un pilotage est indispensable, demander l'accord selon la procédure ci-dessus ; l'étape concernée reste non vérifiée tant que ses preuves manquent.
