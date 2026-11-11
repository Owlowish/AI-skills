# Validation visuelle obligatoire

## Preuves et capture reproductible

Un examen initial puis au maximum trois corrections par jalon : essais 00, 01, 02, 03. Une correction est un lot cohérent de changements prioritaires, suivi d'une nouvelle capture et d'une nouvelle inspection. Une erreur d'outil ne constitue pas une correction géométrique.

Pour chaque examen :

1. Sauvegarder le maître Blender avant capture. Produire les vues depuis sa géométrie réelle, avec éclairage neutre et cadrages reproductibles. Le helper décrit dans [project-tools.md](project-tools.md) copie temporairement la géométrie évaluée de `MODEL` dans une scène de rendu jetable, sans sauvegarder cette scène dans le maître. Il utilise Workbench gris, studio fixe et quatre caméras orthographiques (dont une orientation trois-quarts).
2. Ouvrir **réellement les quatre PNG** avec l'outil d'inspection d'images ou les réponses images du MCP. Ouvrir également toutes les sources pertinentes ; en reprise ne pas supposer les avoir déjà vues. Un tableau de fichiers, des hashes, un texte d'outil ou un contact sheet trop petit ne prouvent pas une inspection. S'assurer que les images montrent bien le sujet, sans écran noir ni cadrage tronqué. Un échec de capture/visualisation impose BLOCKED.
3. Comparer formes visibles et référence originale en tenant compte de sa perspective. Les vues du dos et surfaces cachées contrôlent cohérence, épaisseurs et intersections ; elles ne prouvent pas la fidélité à des parties invisibles. Au besoin ajouter une vue perspective correspondant à la source et un gros plan, sans remplacer les quatre vues standard.
4. Identifier **au plus trois défauts prioritaires** parmi `proportions`, `silhouette`, `geometry`, `detail`, avec gravité `major` ou `minor`. Décrire leur emplacement et conséquence visible. Ne pas inventer de score objectif de similarité.
5. Si les critères du jalon sont satisfaits et aucun majeur ne reste, enregistrer PASS. Sinon préserver la meilleure version, enregistrer FAIL, corriger les défauts les plus importants puis recapturer et réinspecter. Ne jamais passer au jalon suivant avec un majeur non résolu.
6. Après essai 03 insuffisant : arrêter, garder/restaurer la meilleure version, exposer les problèmes persistants. Une prolongation exceptionnelle exige une justification circonstanciée, consignée avant dépassement dans `correction_limit_reason` et le rapport ; ne pas augmenter automatiquement la limite pour obtenir un PASS.

Le cadrage initial est mémorisé dans `previews/camera-rig.json`. Garder le même centre, échelle, studio, résolution et axes pour comparer les essais. Si une évolution justifiée dépasse le cadre, consigner la raison, préserver l'ancien rig dans le rapport, réviser explicitement le rig et refaire les vues utiles. Aucun recadrage silencieux qui dissimule un défaut de proportions.

## Rapport d'examen

Préparer un JSON sous `reports/<stage>/review-input.json`, **après** l'inspection. Le script `project.py record` crée le rapport d'essai JSON et sa version Markdown. Les chemins sont relatifs au projet. Exemple de structure à renseigner avec les observations réelles (ces textes ne sont pas une validation) :

```json
{
  "stage": "blockout",
  "attempt": 0,
  "status": "FAIL",
  "justification": "La largeur observée dépasse la silhouette de référence.",
  "inspection": {
    "method": "Outil de vision utilisé pour ouvrir les originaux et les quatre rendus",
    "inspected_images": [
      "references/source/reference.png",
      "previews/blockout/attempt-00/front.png",
      "previews/blockout/attempt-00/side.png",
      "previews/blockout/attempt-00/back.png",
      "previews/blockout/attempt-00/three-quarter.png"
    ],
    "observations": ["Décrire la différence effectivement vue et la zone concernée."]
  },
  "defects": [
    {"category": "proportions", "severity": "major", "description": "Décrire le défaut constaté.", "resolved": false}
  ],
  "corrections": [],
  "remaining_issues": ["Décrire le point empêchant le passage."],
  "best_checkpoint": "blender/checkpoints/blockout-best.blend"
}
```

Les essais 01–03 renseignent les corrections réellement apportées depuis l'examen précédent. Au premier FAIL, sauvegarder le meilleur checkpoint avant de l'enregistrer. Ne remplacer `<stage>-best.blend` que si l'examen montre que la nouvelle tentative est meilleure ; expliquer le choix. Conserver les captures des essais pour la comparaison. À PASS, retenir les checkpoints importants indiqués dans workflow.md, sans créer une nouvelle variante pour chaque commande Blender.

Pour `geometry` et `finalization` PASS, ajouter `geometry_checks` avec les six clés `normals`, `degenerate_faces`, `intersections`, `duplicates`, `modifiers`, `topology`. Chaque valeur décrit le contrôle réellement effectué dans Blender, son résultat et les limites (pas simplement « OK » sans méthode). Une auto-intersection intentionnelle peut être acceptable selon l'usage ; expliquer sa décision. Un défaut structurel majeur interdit PASS même si le rendu paraît correct.

Pour `finalization` PASS, ajouter `scene_check` décrivant la réouverture du maître, et `export_checks`, liste d'objets `{ "path": "exports/model.glb", "method": "Réimport Blender et contrôles réellement effectués", "status": "PASS" }`. S'il n'y a aucun export demandé : liste vide, sans créer d'export artificiel. Chaque format dans `project.yaml.requested_exports` doit être vérifié.

## Outil ou vision indisponible

Enregistrer une déclaration honnête et minimale :

```json
{
  "stage": "blockout",
  "attempt": 0,
  "status": "BLOCKED",
  "justification": "Décrire la capacité indisponible et le résultat de la tentative réelle."
}
```

Elle devient `reports/<stage>/blocked.json` et `.md`, sans inventer de capture ni consommer une correction. Le numéro doit être le prochain essai attendu ; au retour de la capacité, réutiliser ce numéro pour l'examen réel. Le rapport BLOCKED reste une trace ; `project.yaml.stages` indique le statut courant. Si la limite des corrections est déjà épuisée, conserver FAIL et le meilleur état plutôt qu'essayer de contourner la limite par BLOCKED.

## Portée du contrôle automatique

Les scripts refusent PASS sans chemins d'images inspectées, observations, quatre captures hachées, source intacte, maître correspondant à la capture, ou avec un majeur non résolu. Ils vérifient aussi l'ordre des jalons et la limite. Ils **ne peuvent pas prouver qu'un humain ou un modèle a regardé une image**, ni mesurer la ressemblance. Ne jamais remplir ces champs sans examen réel. Un reçu technique de capture n'est pas un PASS artistique.

Pour une révision ciblée, ajouter la comparaison obligatoire de [targeted-retouch.md](targeted-retouch.md) : cinq vues avant et cinq après, caméras et éclairage identiques, observations, changements et vérifications de préservation. Le rapport contient la paire d'images de la vue ciblée. Une régression interdit PASS ; les preuves des anciennes versions ne sont jamais écrasées.
