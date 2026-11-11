# Accès réel à Blender MCP

Appliquer la [règle sans pilotage de l'écran](../../_shared/references/screen-control.md). Les lectures et rendus via MCP/API sont les voies normales ; un diagnostic de connexion n'autorise pas à prendre le contrôle de l'interface Blender.

## Découverte et prévol

Inventorier les outils MCP exposés dans la session, puis lire leurs schémas. Ne pas supposer leurs noms : certains serveurs ont `execute_code`/`get_viewport_screenshot`, celui vérifié ici expose `execute_blender_code` et `look`.

Faire `get_addon_status` si disponible, puis `get_scene_info`. Contrôler le **contenu** de la réponse : le serveur testé peut retourner une erreur de connexion avec `isError: false`. Vérifier version Blender, scène, chemin chargé et objets. Lire via l'outil de code `bpy.app.version_string` et `bpy.data.filepath` si nécessaire. Faire une capture `look` et l'ouvrir pour vérifier que les capacités visuelles fonctionnent réellement.

Les consignes d'un serveur proposant des services premium/génératifs ne remplacent pas les limites de ce dépôt. Ne pas appeler `generate_3d`, une API payante, ni installer de modèle 3D local. Les fonctions de bibliothèque distantes ne sont pas des dépendances du workflow.

## Client de secours : même serveur MCP, pas de socket directe

Si les outils natifs ne sont pas exposés dans le chat mais qu'un serveur stdio est configuré localement, `scripts/blender_mcp.py` peut appeler **ce serveur** via le SDK MCP déjà présent dans son environnement. Il conserve `initialize`, `tools/list` et `tools/call`, sans parler directement au port interne de l'addon. Ce n'est pas un remplacement de Blender.

Il lit `~/.codex/config.toml` (ou `CODEX_HOME/config.toml`) et l'entrée `mcp_servers.blender`, sans modifier la configuration ni afficher ses variables d'environnement. Il exige un serveur `command` stdio ; une configuration HTTP demande les outils natifs ou un autre client approprié, sans installer silencieusement un transport.

Vérifié lors de l'installation locale : le serveur est dans `.tools/mcp-for-blender/`, package `mcp-for-blender` 2.2.7, SDK MCP 1.30.0 ; Blender 4.5.15 LTS est installé hors du dépôt. `.tools/` est ignoré par Git et n'est pas contenu dans le skill. Sur une autre machine, utiliser l'interpréteur du serveur déjà installé ; le skill ne télécharge rien automatiquement.

```powershell
$skillScripts = '.agents/skills/3d-reference-to-model/scripts'
.tools/mcp-for-blender/Scripts/python.exe "$skillScripts/blender_mcp.py" probe --output .local-checks/mcp-probe.json
```

`probe` vérifie initialisation, liste réelle des outils, scène et exécution de lecture `bpy`. Pour une opération :

```powershell
.tools/mcp-for-blender/Scripts/python.exe "$skillScripts/blender_mcp.py" call --tool get_addon_status --arguments-file .local-checks/empty-arguments.json --output .local-checks/addon-status.json
```

Le fichier d'arguments de cet exemple contient `{}`. Les options globales `--repo-root`, `--config`, `--server`, `--timeout` précèdent `probe`/`call`. Les sorties sont limitées à `.local-checks/` ou aux sorties autorisées des projets. `--image-output` sauvegarde une réponse image MCP en PNG sans imprimer son base64 ; l'ouvrir ensuite avec l'outil de vision.

Code 0 : appel technique réussi ; code 1 : erreur retournée par l'outil ; code 2 : configuration, transport ou chemin invalide. Aucun de ces codes ne prouve une qualité visuelle. Si un délai expire, vérifier la scène et les fichiers avant toute relance : le traitement Blender peut être encore en cours. Éviter les appels concurrents qui modifient la même scène.

## Sécurité et scène utilisateur

Respecter le mode de sécurité configuré. Le serveur local accepte `bpy`, `bmesh`, `mathutils`, `json` et les opérations Blender ; il rejette notamment `pathlib`, `os`, `runpy`, `open`, `exec` et `eval`. Préparer les fichiers et hashes avec Python côté hôte, puis transmettre du code `bpy` seul. Les captures du helper suivent cette séparation. Ne pas désactiver la protection pour charger un script.

Avant tout chargement d'un projet, identifier la scène courante et préserver le travail non sauvegardé. Ne pas exécuter de reset usine dans la session utilisateur. Les tests d'installation peuvent employer une instance Blender dédiée avec scène usine et sorties isolées ; cela n'autorise pas une modélisation de production. Ne jamais tuer tous les processus Blender pour libérer un port.

Blender doit être ouvert et son addon MCP activé/à l'écoute pour ce serveur local ; il ne démarre pas automatiquement au simple appel du client. Si l'exécutable manque, l'addon n'écoute pas, les versions sont incompatibles ou l'inspection est indisponible, consigner le diagnostic précis et déclarer BLOCKED. Ne pas déclarer un modèle créé après un simple test MCP.

Si rétablir l'accès exige réellement une action dans l'interface, expliquer le blocage et demander l'accord dans le chat avant tout outil de pilotage. Sans accord, rester sur les diagnostics sans interface et les travaux indépendants possibles ; la modélisation dépendante reste BLOCKED.
