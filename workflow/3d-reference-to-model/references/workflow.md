# Production à partir des références

## Analyse et préparation

Ouvrir réellement chaque image originale. Décrire dans `reports/analysis.md` le sujet, le style, l'intention, les masses principales, proportions, silhouette, éléments secondaires et détails caractéristiques. Classer `organic`, `hard-surface` ou `hybrid` dans `project.yaml`. Préciser l'objectif, l'échelle si connue, les contraintes et formats demandés.

Distinguer ce qui est visible, ce qui est estimé et ce qui reste inconnu. Tenir compte de la perspective, des déformations artistiques et des surfaces occultées. Pour plusieurs images, signaler les contradictions et choisir la vue qui fait autorité dans `authoritative_reference` ; expliquer la décision. Une seule vue trois-quarts peut permettre de commencer avec des hypothèses raisonnables documentées.

Choisir la stratégie Blender selon les formes : sculpture/remesh, subdivision, courbes, modifiers, booléens, assemblages ou travail direct du maillage. Aucun procédé universel. Au début de la modélisation autorisée seulement, préparer une collection `MODEL` et appliquer les axes : Z vers le haut, face vers -Y. Orienter le sujet une fois, sans changer arbitrairement les axes entre validations. Si la référence impose une autre convention, documenter la conversion. Une demande de préparation seule s'arrête à l'analyse et aux fichiers de projet.

Les références sources sont des copies immuables dont les empreintes sont vérifiées. Ne pas recadrer, repeindre ou remplacer ces fichiers ; conserver les préparations séparément. Créer les répertoires utiles au moment où leur contenu est produit.

## Blockout — `blockout`

Construire les volumes principaux seulement. Les primitives conviennent pour chercher la silhouette ; éviter les détails et matériaux qui distraient de la forme. Vérifier les rapports de hauteur/largeur/profondeur et le placement relatif des grandes masses.

Sauvegarder `blender/model.blend` puis appliquer la [validation visuelle](visual-validation.md). Produire au minimum face orthographique, profil orthographique, dos et trois-quarts, avec éclairage neutre. Comparer surtout silhouette et proportions. **Passage : silhouette reconnaissable et proportions principales acceptables.** Conserver `blender/checkpoints/blockout.blend` après PASS.

## Construction — `geometry`

- Organique : construire des volumes continus et des transitions plausibles ; sculpture, remesh et subdivision selon le sujet. Sur les personnages, contrôler anatomie stylisée ou réaliste, épaisseur des membres et articulations. Les chevauchements de primitives ne remplacent pas des transitions abouties.
- Hard-surface : organiser les pièces, maîtriser les surfaces, épaisseurs, chanfreins et assemblages. Distinguer joint mécanique volontaire et intersection accidentelle.
- Hybride : adapter la technique à chaque composant ; aucune topologie unique imposée à tout le sujet.

Développer les formes secondaires, sans microdétails. Auditer dans Blender normales, faces dégénérées, intersections problématiques, doublons accidentels, modifiers et défauts topologiques significatifs. Les bords ouverts ou pièces séparées ne sont pas systématiquement des erreurs pour un modèle éditable ; les interpréter selon l'usage demandé.

**Passage : volumes cohérents, transitions satisfaisantes, absence de défaut structurel majeur.** Capturer, inspecter, corriger puis enregistrer le rapport ; conserver `blender/checkpoints/geometry.blend` après PASS.

## Raffinement — `refinement`

Ajouter progressivement les détails essentiels à l'identité du sujet. Préférer un détail juste et lisible aux ornements masquant de mauvaises masses. Vérifier sa profondeur et sa lecture sous plusieurs angles. Réutiliser des gros plans sources lorsqu'ils existent.

Une image auxiliaire IA n'est justifiée que pour un besoin précis : détail illisible, simplification des masses, finition, hypothèse d'une zone occultée. Avant utilisation : vérifier disponibilité et absence de frais additionnels, puis lire le skill correspondant. Sinon continuer sans génération. Enregistrer dans `references/generated/` avec un fichier voisin décrivant `synthetic: true`, outil, source, intention et incertitudes. Ouvrir l'auxiliaire et l'original, constater leurs cohérences/incohérences, puis consigner l'examen. Aucun multivue généré systématiquement ; ne jamais faire passer une invention pour une surface connue.

**Passage : détails lisibles et conformes aux caractéristiques essentielles de la source.** Répéter la validation ; un checkpoint supplémentaire n'est utile que si le travail le justifie.

## Finalisation — `finalization`

Nettoyer et organiser la scène, nommer objets et collections explicitement. Préserver l'éditabilité du maître. Retirer les éléments de test du projet courant, sans supprimer de ressources utilisateur ni modifier d'autres projets. Sauvegarder le maître et vérifier son ouverture effective dans Blender sur copie ou après protection de la scène courante.

Répéter les contrôles géométriques et la validation visuelle neutre. Des rendus avec matériaux/éclairage de présentation peuvent compléter les quatre vues neutres, sans les remplacer.

Exporter seulement les formats demandés dans `exports/`. Fixer et consigner unités, axes, sélection d'objets, modifiers et matériaux selon le format. Vérifier l'export en le réimportant dans une scène temporaire Blender : objets attendus, échelle, orientation, géométrie, matériaux si pris en charge. L'existence d'un GLB/STL/OBJ ne suffit pas. Ne pas imposer rigging, optimisation jeu ou préparation impression. Les contraintes manifold, découpe, supports et étanchéité sont activées uniquement sur demande.

**Passage : scène propre, maître sauvegardé/réouvert, captures inspectées, exports demandés contrôlés.** Conserver `blender/checkpoints/finalization.blend`, puis `project.py validate <projet> --complete`.

## Reprise et arrêt

Lire `project.yaml`, `reports/analysis.md`, les rapports du dernier jalon et ses captures ; ouvrir ces dernières avant de se fier au PASS déclaré. Vérifier les sources, les capacités MCP, le fichier chargé et le checkpoint retenu. Reprendre le premier jalon non PASS, sans consommer de correction pour une simple panne d'outil. Pour une nouvelle retouche d'une livraison terminée, appliquer [targeted-retouch.md](targeted-retouch.md), qui préserve la version précédente et rouvre les validations affectées. Une source modifiée ou une demande structurante invalide les validations concernées : garder l'historique et expliquer quels jalons doivent être réexaminés, plutôt que forcer leurs statuts.

En cas de FAIL après trois corrections, conserver le meilleur checkpoint et restaurer ce meilleur état dans le maître si la dernière tentative est moins bonne. Expliquer le défaut persistant, les trois corrections tentées et la prochaine action utile. Livrer l'état réel et les preuves disponibles. Ne pas continuer le raffinement d'une structure rejetée.
