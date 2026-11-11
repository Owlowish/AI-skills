# Fichiers et commandes

Tous les chemins de sortie sont dans le projet. Les scripts de projet et capture fonctionnent avec Python 3.12 sans dépendance supplémentaire. `project.yaml` est écrit en JSON UTF-8, compatible YAML 1.2 ; conserver ce format JSON en l'éditant pour éviter une dépendance PyYAML au runtime.

Depuis la racine de l'espace (PowerShell) :

```powershell
$skillScripts = '.agents/skills/3d-reference-to-model/scripts'
python "$skillScripts/project.py" new --repo . --slug fantasy-knight --reference 'C:/images/reference.png' --model-type organic
python "$skillScripts/project.py" validate projects/fantasy-knight
```

`--reference` est répétable. Le slug est stable (minuscules ASCII/chiffres/tirets, maximum 64), exclusif et sans nom réservé Windows. Un nom déjà utilisé est refusé. Les noms de sources doivent être distincts. Les images sont copiées, jamais déplacées, et hachées SHA-256. Seuls `project.yaml` et les sources sont créés initialement ; le reste apparaît lorsqu'il sert.

Renseigner ensuite `objective`, `model_type`, `assumptions`, `authoritative_reference` et `requested_exports` (formats sans point, minuscules, par exemple `["glb"]`). L'état initial `READY` signifie dossier préparé, sans attester l'accès Blender ni la qualité du futur modèle. `status`, `current_stage` et `stages` sont maintenus par `record` ; ne pas les forcer pour contourner un échec.

## Captures via MCP avec mode de sécurité actif

1. Dans Blender via MCP, créer les répertoires utiles côté hôte, puis sauvegarder le maître via `bpy.ops.wm.save_as_mainfile(filepath=...)`. La collection `MODEL` doit contenir la géométrie à examiner. Les caméras, lumières et images de référence ne deviennent pas de la géométrie de validation.
2. Préparer le code sans exécuter Blender :

```powershell
python "$skillScripts/blender_previews.py" prepare projects/fantasy-knight --stage blockout --attempt 0
```

La commande crée `reports/blockout/preview-attempt-00.py`, son `.arguments.json` et `previews/blockout/attempt-00/prepared.json`. Envoyer la valeur `code` de l'arguments JSON à l'outil de code MCP réellement découvert. Le code ne contient que `bpy`, `mathutils` et `json` ; les opérations fichier/hachage sont réalisées côté hôte, sans désactiver le mode de sécurité. Ne pas envoyer `exec(open(...).read())` : cette forme est rejetée par le serveur local.

3. Conserver la réponse MCP complète en JSON dans `reports/blockout/capture-attempt-00-result.json`. Avec le client de secours local déjà installé :

```powershell
.tools/mcp-for-blender/Scripts/python.exe "$skillScripts/blender_mcp.py" --timeout 120 call --tool execute_blender_code --arguments-file projects/fantasy-knight/reports/blockout/preview-attempt-00.arguments.json --output projects/fantasy-knight/reports/blockout/capture-attempt-00-result.json
python "$skillScripts/blender_previews.py" finish projects/fantasy-knight --stage blockout --attempt 0 --result projects/fantasy-knight/reports/blockout/capture-attempt-00-result.json
```

`finish` exige la confirmation de quatre rendus dans le retour Blender, les quatre PNG aux dimensions prévues et le même fichier maître. Il écrit `capture.json` avec empreintes, version Blender, moteur et cadrage. Il ne valide pas visuellement les images. Les ouvrir réellement après ce contrôle.

Les rendus sont conservés sous `previews/<stage>/attempt-00/`. La résolution est 768 carrés par défaut, configurable de 128 à 2048 lors de prepare ; garder la même valeur dans une série. Le helper ne sauvegarde pas sa scène jetable dans le maître. Il peut marquer la session Blender comme modifiée lors de la création/suppression des données temporaires : vérifier puis sauvegarder de nouveau le maître avant le prochain prepare. Ne pas exécuter une nouvelle modélisation dans la scène de validation.

Si prepare a déjà réussi, réutiliser les mêmes arguments pour une reprise de panne avant génération des images. Ne pas écraser des captures déjà inspectées : un changement de géométrie requiert l'essai suivant après son FAIL. Pour un rendu partiel raté, documenter la panne et retirer seulement les artefacts techniques incomplets de cet essai après vérification de leurs chemins ; ne pas supprimer de rapport ni de preuve d'un examen terminé.

## Rapports et contrôles

Après inspection et rédaction du JSON décrit dans [visual-validation.md](visual-validation.md) :

```powershell
python "$skillScripts/project.py" record projects/fantasy-knight --review projects/fantasy-knight/reports/blockout/review-input.json
python "$skillScripts/project.py" validate projects/fantasy-knight
python "$skillScripts/project.py" validate projects/fantasy-knight --complete
```

`record` refuse les preuves précédentes corrompues avant progression. `BLOCKED` ne consomme aucun essai. `FAIL` à l'essai 03 bloque la progression, conserve le statut du jalon FAIL et exige un meilleur checkpoint existant. `--complete` exige les quatre PASS et que le maître final corresponde à l'examen final. Un code de sortie 0 de validate signifie cohérence documentaire ; il ne constitue pas une inspection visuelle.

Les tests d'infrastructure utilisent des fixtures explicitement synthétiques et un dossier temporaire hors des projets :

```powershell
python "$skillScripts/test_project.py"
```

Ne pas traiter leurs PASS simulés comme des validations de modèles réels.

## Révision d'une livraison

Pour une retouche ciblée après livraison, lire [targeted-retouch.md](targeted-retouch.md). `project.py revise <projet> --from-stage <jalon> --request <demande>` conserve la version précédente, puis rouvre ce jalon et les suivants. `--target`, `--preserve` sont répétables ; `--view-direction X Y Z` définit la vue de comparaison.

Utiliser `blender_previews.py prepare-before <projet>` puis `finish-before <projet> --result <réponse-MCP>` avant toute modification. Les commandes prepare/finish habituelles produisent ensuite les vues après dans `previews/<stage>/r001/attempt-00/`. Chaque examen comporte la comparaison structurée et les cinq images avant et après effectivement inspectées. Les checkpoints et exports nouveaux vont respectivement dans `blender/checkpoints/r001/` et `exports/r001/`.

Tests du cycle de révision, toujours avec fixtures temporaires synthétiques : `python scripts/test_revisions.py` (chemin relatif au skill).
