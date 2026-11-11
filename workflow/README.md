# Workflow 3D

| Skill | Usage |
|---|---|
| [3d-generate-refpack](3d-generate-refpack/SKILL.md) | Références cohérentes depuis une source |
| [3d-reference-to-model](3d-reference-to-model/SKILL.md) | Modélisation Blender et quatre jalons inspectés |
| [3d-refine-refpack-view](3d-refine-refpack-view/SKILL.md) | Retouche d'une vue du refpack |
| [3d-refine-view](3d-refine-view/SKILL.md) | Retouche ciblée d'un modèle existant |
| [3d-review-consistency](3d-review-consistency/SKILL.md) | Audit de cohérence multivue |
| [3d-rig-model](3d-rig-model/SKILL.md) | Rig organique, mécanique ou hybride |
| [3d-pose-model](3d-pose-model/SKILL.md) | Pose depuis texte ou image |
| [3d-prepare-fdm](3d-prepare-fdm/SKILL.md) | Échelle, socle, découpe et STL FDM |

La chaîne complète conserve le modèle approuvé, puis les variantes de rig, de pose et de fabrication. Les objets fixes peuvent passer directement à la préparation FDM. Les vues et rapports de chaque étape sont inspectés dans Blender ; aucune validation graphique n'est simulée par les tests.

## Installation Windows avec suivi Git direct

Prérequis : Git, Python 3.12 et Blender avec un serveur MCP accessible lors des tâches 3D. Aucun de ces outils n'est installé par le script de liaison.

~~~powershell
git clone https://github.com/Owlowish/AI-skills.git C:/chemin/espace/AI-skills
powershell -ExecutionPolicy Bypass -File C:/chemin/espace/AI-skills/workflow/_shared/scripts/link-workspace.ps1 -WorkspacePath C:/chemin/espace
~~~

Le script vérifie les copies existantes avant de les déplacer dans .local-checks/skills-backups, puis crée une jonction de .agents/skills vers le dossier workflow du clone. Il refuse une divergence ou un skill étranger à la bibliothèque pour éviter de masquer des ressources locales. Utiliser -WhatIf pour examiner les opérations.

Dans cette disposition, les chemins des skills restent .agents/skills/... et le client MCP existant retrouve sa racine de travail. Pour une autre disposition, fournir explicitement --repo-root au client blender_mcp.py. Conserver AGENTS.md à la racine du projet 3D.

## Suivre et publier les changements

~~~powershell
git -C C:/chemin/espace/AI-skills status --short
git -C C:/chemin/espace/AI-skills diff
git -C C:/chemin/espace/AI-skills add workflow
git -C C:/chemin/espace/AI-skills commit -m "Affiner le workflow 3D"
git -C C:/chemin/espace/AI-skills push
~~~

Le suivi local est direct ; commit et push restent explicites. Pour mettre à jour le clone, garder d'abord ses changements locaux puis utiliser git pull --ff-only.

## Validation de la bibliothèque

Les outils de production des variantes et de l'audit STL utilisent seulement la bibliothèque standard Python. Le validateur de skills emploie PyYAML.

~~~powershell
python -m pip install -r requirements-dev.txt
python workflow/_shared/scripts/check_library.py
python -m unittest discover -s workflow/3d-reference-to-model/scripts -p "test_*.py"
python -m unittest discover -s workflow/_shared/tests -p "test_*.py"
~~~

Les tests utilisent des fichiers synthétiques dans des dossiers temporaires ; ils ne lancent pas Blender, un slicer ou une impression. Le validateur de structure ne prouve pas l'inspection visuelle d'un modèle.

[Contrat des variantes rig/pose/FDM](_shared/references/derived-workflow.md).
