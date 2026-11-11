# Retouche ciblée d'une livraison

Utiliser ce mode lorsqu'une nouvelle demande porte sur un projet terminé : « rapproche le profil de la référence », « raccourcis la tête », « affine cette articulation », « change ce matériau ». Pour un jalon encore en cours, continuer sa boucle existante. Une simple question ou réflexion sur une retouche n'autorise pas à l'exécuter.

## Périmètre et première étape affectée

Lire le projet, les rapports, la version livrée et les sources ; ouvrir réellement les images. Reformuler brièvement l'objectif, les pièces ciblées et ce qui doit rester préservé. Une hypothèse raisonnable suffit sans confirmation systématique ; clarifier seulement une ambiguïté structurante.

| Demande | Reprendre depuis | Revalider |
| --- | --- | --- |
| Silhouette ou proportions majeures, pose, rapport tête/corps | `blockout` | Les quatre jalons |
| Forme locale d'une pièce, épaisseur, assemblage, transition | `geometry` | Géométrie, raffinement, finalisation |
| Détail, motif, matériau, couleur sans changement de volume majeur | `refinement` | Raffinement, finalisation |
| Lumière, caméra de présentation ou export seulement | `finalization` | Finalisation |

Choisir le jalon le plus tôt si la demande recouvre plusieurs catégories. Cela rouvre une **validation du modèle existant**, sans effacer ses détails ni recommencer la construction. Si une nouvelle conséquence dépasse le périmètre prévu, ne pas conserver artificiellement un ancien PASS : arrêter et expliquer les validations supplémentaires nécessaires.

Pour un profil, rapprocher l'angle de la caméra de celui de la référence, qui peut être en perspective. Une vue orthographique exactement latérale n'est pas nécessairement l'angle de la photo. Conserver également les quatre vues standard pour détecter une dégradation des autres angles.

## Ouvrir la révision, sans modifier la géométrie

Exemple depuis la racine, pour la demande hypothétique de profil du robot :

```powershell
$skillScripts = '.agents/skills/3d-reference-to-model/scripts'
python "$skillScripts/project.py" revise projects/robot-demo --from-stage blockout --request 'Rapprocher le profil de la référence, surtout tête et cou' --target tete --target cou --preserve couleurs --preserve motifs --view-direction -1 -0.18 0.05
```

La commande exige une livraison `COMPLETE` dont les preuves sont intègres. Elle ne modifie pas `blender/model.blend` et ne lance pas Blender. Elle :

- copie le maître en `blender/model-before-r001.blend`, à côté du maître pour conserver le sens des liens relatifs vers les ressources ;
- conserve le manifeste précédent et une copie du rig dans `revisions/r001/`, avec demande, cibles, contraintes, direction de vue et empreintes ;
- protège les fichiers antérieurs par leurs empreintes, sans déplacer ni supprimer leurs images, rapports, ressources, checkpoints ou exports ;
- conserve les PASS strictement antérieurs au jalon repris et rouvre celui-ci et les suivants. Les nouveaux compteurs commencent à zéro pour cette nouvelle demande ; une révision inachevée ne peut pas en ouvrir une autre.

Le numéro est stable et croissant (`r001`, `r002`, …). Ne jamais écraser les copies `model-before-*`. Les sources et anciennes ressources doivent rester intactes ; si une retouche de texture est demandée, créer une nouvelle ressource et mettre à jour uniquement la version courante, afin que le modèle précédent continue à fonctionner.

Tous les **nouveaux** fichiers doivent utiliser l'espace de la révision :

```text
blender/model.blend                      Maître courant
blender/model-before-r001.blend          Version précédente préservée
blender/checkpoints/r001/                Nouveaux checkpoints
revisions/r001/revision.json             Périmètre et empreintes protégées
revisions/r001/project-before.json       Ancien état de validation
revisions/r001/camera-rig.json           Cadrage figé
previews/<stage>/r001/before/             État avant, au premier jalon rouvert
previews/<stage>/r001/attempt-00/         État après de chaque jalon concerné
reports/<stage>/r001/                    Nouveaux scripts, appels MCP et examens
exports/r001/                            Nouveaux exports, si demandés
```

Les anciens exports restent consultables mais ne peuvent pas valider la nouvelle livraison. Ne pas réécrire les anciens rapports, y compris `reports/delivery.md` : écrire le nouveau bilan dans `reports/finalization/r001/delivery.md`.

## Capturer l'état avant, puis seulement retoucher

Vérifier Blender MCP et le fichier chargé. Avant de toucher aux pièces, le maître sur disque doit encore correspondre à la version précédente. Préserver séparément tout autre travail non sauvegardé dans Blender, puis recharger ce maître si nécessaire avec `bpy.ops.wm.open_mainfile(filepath=..., load_ui=False)` via MCP. Cette opération est admise par le mode de sécurité du serveur configuré ; elle ne doit jamais faire perdre un travail non sauvegardé. Ne pas sauvegarder un état déjà modifié sur le maître avant la capture de référence de la révision.

```powershell
python "$skillScripts/blender_previews.py" prepare-before projects/robot-demo
```

Pour l'exemple `blockout/r001`, envoyer le code du fichier généré au vrai outil Blender MCP :

```powershell
.tools/mcp-for-blender/Scripts/python.exe "$skillScripts/blender_mcp.py" --timeout 120 call --tool execute_blender_code --arguments-file projects/robot-demo/reports/blockout/r001/preview-before.arguments.json --output projects/robot-demo/reports/blockout/r001/capture-before-result.json
python "$skillScripts/blender_previews.py" finish-before projects/robot-demo --result projects/robot-demo/reports/blockout/r001/capture-before-result.json
```

Les cinq images `front`, `side`, `back`, `three-quarter`, `focus` doivent être **ouvertes et inspectées**, ainsi que la référence originale. `focus` est la direction choisie à l'ouverture de la révision. Le cadrage, la résolution et l'éclairage neutre sont figés pour les images après. Une capture avant ne peut plus être écrasée. Si le maître a déjà changé, ne pas inventer une image avant : retrouver la version préservée et rétablir un prérequis cohérent avant de poursuivre.

Si le cadrage choisi ne convient pas, signaler le blocage avant modification, sans changer discrètement le rig. Ne pas comparer deux cadrages différents en les présentant comme identiques.

Modifier ensuite seulement les pièces ciblées dans Blender via MCP. Déplacer leurs éléments liés ensemble (par exemple coque, œil et motif de tête), conserver les matériaux/motifs demandés et contrôler l'effet sur les autres angles. Sauvegarder le maître.

## Après et revalidation

```powershell
python "$skillScripts/blender_previews.py" prepare projects/robot-demo --stage blockout --attempt 0
# Exécuter le code MCP généré dans reports/blockout/r001/.
python "$skillScripts/blender_previews.py" finish projects/robot-demo --stage blockout --attempt 0 --result projects/robot-demo/reports/blockout/r001/capture-attempt-00-result.json
```

L'examen initial de l'état retouché est l'essai 00. Les modifications demandées sont décrites dans `comparison.changes` ; `corrections` reste vide à cet examen initial. Les corrections supplémentaires suivent les essais 01 à 03. Les pannes d'outil donnent BLOCKED et ne consomment pas de correction.

Ouvrir toutes les images avant et après, comparer réellement à la source et compléter l'examen habituel de [visual-validation.md](visual-validation.md). Ajouter :

```json
"comparison": {
  "outcome": "improved",
  "changes": ["Décrire la modification effectivement réalisée."],
  "observations": ["Décrire le changement visible entre les deux profils et son rapport à la source."],
  "preservation_checks": {
    "couleurs": "Décrire le contrôle effectif des couleurs.",
    "motifs": "Décrire le contrôle effectif des motifs."
  }
}
```

Les contraintes sont exactement celles déclarées avec `--preserve`. `inspection.inspected_images` doit contenir les sources et les **dix** chemins d'images : cinq avant et cinq après. Les observations ne doivent pas être remplies sans inspection réelle. Le résultat `outcome` est `improved`, `equivalent` ou `regressed` ; une régression déclarée interdit PASS. Une équivalence peut être acceptable pour un jalon ultérieur conservant la correction, mais ne prouve pas qu'une amélioration demandée a été obtenue.

```powershell
python "$skillScripts/project.py" record projects/robot-demo --review projects/robot-demo/reports/blockout/r001/review-input.json
```

Le script ajoute l'identifiant de révision, vérifie les preuves et produit le rapport Markdown avec les deux images `focus` côte à côte. Il contrôle la compatibilité technique des images et les attestations, sans juger lui-même la ressemblance. Refaire ensuite les jalons suivants, les audits appropriés, la réouverture du maître et les exports demandés. Aucun PASS antérieur invalidé ne peut servir de raccourci.

En cas de FAIL, conserver le meilleur checkpoint dans `blender/checkpoints/r001/`. À la limite des trois corrections, conserver ce meilleur état et la version précédente, exposer les écarts restants et arrêter. Ne pas lancer `r002` pour contourner cette limite.

Après les PASS concernés : `project.py validate <projet> --complete`. Livrer le maître courant, le lien vers la version précédente, les avant/après et les limites observées. Afficher les deux images ciblées dans la réponse avec leurs chemins absolus, afin que l'utilisateur voie la comparaison directement. Le projet conserve le même identifiant et les révisions successives restent consultables.
