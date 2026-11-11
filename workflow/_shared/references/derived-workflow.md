# Variantes rig, pose et fabrication

Ces étapes prolongent le workflow de modélisation sans modifier ses quatre jalons ou forcer leurs PASS. Le modèle approuvé, ses sources et ses preuves restent intacts. Ne pas retoucher le modèle pendant une simple installation des skills.

## Runs et provenance

Depuis la racine de l'espace de travail :

~~~powershell
python .agents/skills/_shared/scripts/derived_workflow.py new projects/exemple --kind rig --label principal --mode rigid --source blender/model.blend --request 'Préparer les articulations du modèle approuvé'
~~~

Le helper vérifie le projet source COMPLETE avec le validateur existant. Pour une pose articulée, passer --upstream vers le manifeste PASS du rig ; pour FDM, vers le manifeste PASS de la pose. Un objet fixe peut partir directement du maître avec --mode static pour pose ou FDM.

Les chemins sont relatifs au projet, portables et numérotés sans écrasement :

~~~text
reports/<kind>/<label>/r001/manifest.json
blender/<kind>/<label>/r001/<kind>.blend
previews/<kind>/<label>/r001/
exports/fdm/<label>/r001/
~~~

Le helper réserve les dossiers ; il ne lance pas Blender et ne crée pas un modèle fictif. Charger la source approuvée dans Blender puis sauvegarder la variante avec remappage des liens. Ne pas écraser la source. Utiliser des captures avant/après au cadrage fixe et ouvrir réellement les images.

Chaque run conserve demande, type, source et SHA-256, run amont éventuel, examens et fichiers retenus. Une source ou preuve amont modifiée invalide la validation. Pour un run en cours, continuer le même budget, sans en ouvrir un autre pour repartir à zéro.

## Examen

Écrire le JSON de revue dans le dossier reports du run après les contrôles effectifs :

~~~json
{
  "attempt": 0,
  "status": "PASS",
  "justification": "Explication fondée sur les observations effectivement réalisées.",
  "inspection": {
    "method": "Outils et contrôles réellement utilisés.",
    "images": ["previews/rig/principal/r001/front.png", "previews/rig/principal/r001/side.png", "previews/rig/principal/r001/back.png", "previews/rig/principal/r001/three-quarter.png"],
    "observations": ["Observations réelles des différences et raccords."]
  },
  "checks": {},
  "reopen_evidence": "reports/rig/principal/r001/reopen-result.json",
  "remaining_issues": []
}
~~~

Ce schéma est un contrat de données, pas une attestation à recopier. Remplir checks avec les résultats et limites des contrôles pertinents, pas simplement « OK » :

- rig : rest_shape, controls, bindings, range_of_motion, collisions ;
- pose : intent, contacts_balance, joint_limits, collisions, hidden_views, scale_preserved ;
- fdm : scale, watertightness, thin_features, part_strategy, assembly, base_and_stability, orientation_and_supports, exports_reimport.

Le résultat brut du vrai appel MCP de réouverture est enregistré dans reopen_evidence. Les images de validation doivent être de vrais rendus Blender, inspectés sous quatre angles au minimum ; les références et gros plans peuvent compléter les observations.

~~~powershell
python .agents/skills/_shared/scripts/derived_workflow.py record projects/exemple/reports/rig/principal/r001/manifest.json --review projects/exemple/reports/rig/principal/r001/review-input-00.json
python .agents/skills/_shared/scripts/derived_workflow.py validate projects/exemple/reports/rig/principal/r001/manifest.json
~~~

PASS est une validation déclarée après inspection réelle. Le script vérifie chemins, empreintes, preuves et cohérence des données ; il ne sait pas juger une pose ou prouver que les images ont été regardées.

FAIL exige une justification et une variante sauvegardée ; choisir et documenter le meilleur état, sans jeter les essais. Examen initial 00 puis corrections 01–03 maximum. BLOCKED n'utilise pas de correction : décrire la capacité indisponible et arrêter le travail dépendant.

## Champs supplémentaires FDM

Pour un PASS FDM, renseigner :

~~~json
{
  "readiness": "GEOMETRY_PREPARED",
  "dimensions_mm": {"figure": [50, 45, 80], "with_base": [65, 65, 85]},
  "print_profile": {
    "machine": "Bambu Lab A1 mini",
    "nominal_volume_mm": [180, 180, 180],
    "usable_volume_mm": [170, 170, 175],
    "nozzle_mm": 0.4,
    "filament": "PLA",
    "assumptions": ["Ces valeurs sont un exemple de schéma, pas un profil validé."]
  },
  "exports": [{
    "path": "exports/fdm/combat/r001/01-corps.stl",
    "dimensions_mm": [50, 45, 80],
    "reimport_evidence": "reports/fdm/combat/r001/reimport-corps.json"
  }]
}
~~~

Employer les vraies dimensions, buse, matériau et marges, pas les valeurs de cet exemple. Toutes les pièces finales STL du dossier d'export doivent être listées ; chaque pièce est contrôlée par audit et réimport Blender.

Par défaut, un STL doit avoir une seule composante de surface fermée. Une cavité interne fermée peut avoir plusieurs surfaces sans constituer des pièces flottantes. Après examen réel de ces surfaces et de leur connexion physique, une exception peut déclarer `allow_multiple_shells: true` et `shells_justification` par pièce. Cette exception ne prouve pas que des volumes disjoints forment un seul objet : les pièces indépendantes doivent normalement être exportées séparément. En CLI, l'option correspondante est `--allow-multiple-shells`.

SLICER_VERIFIED demande en plus slicer_evidence (rapport ou projet du slicer) et slicer_images (captures de couches réellement ouvertes). Il faut vérifier supports, détails et assemblage, pas seulement produire un fichier. GEOMETRY_PREPARED signifie explicitement « tranchage non vérifié ». Aucun état ne certifie un tirage physique.

L'audit CLI peut aussi être exécuté directement :

~~~powershell
python .agents/skills/_shared/scripts/audit_stl.py chemin/01-corps.stl --expected-mm 50 45 80
~~~

L'audit STL porte sur triangles, dimensions, fermeture et volumes. Il ne détecte pas exhaustivement les auto-intersections, ne valide pas les supports et ne remplace ni réimport, ni inspection, ni calibration physique.
