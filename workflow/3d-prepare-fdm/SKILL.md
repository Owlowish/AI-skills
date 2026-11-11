---
name: 3d-prepare-fdm
description: "Préparer un modèle ou une pose Blender validée pour l'impression FDM, notamment sur Bambu Lab A1 mini : échelle physique, socle, solidité, choix monobloc ou assemblage, orientation et export STL contrôlé."
---

# 3D — Préparer une impression FDM

Produire une variante de fabrication et un dossier de STL à la bonne taille. Préserver le maître et les variantes articulées ; les STL contiennent une pose figée.

## Prévol et paramètres

Lire AGENTS.md, le [contrat des variantes](../_shared/references/derived-workflow.md), les rapports de la source et le [prévol Blender MCP](../3d-reference-to-model/references/blender-mcp.md). Ouvrir la source et ses vues puis créer un run fdm ; ne pas appliquer les opérations de fabrication au maître.

Pour une A1 mini, lire [a1-mini.md](references/a1-mini.md). Connaître ou faire préciser buse installée, filament, taille cible et priorité qualité/montage. Distinguer une recommandation d'un équipement constaté. Continuer l'audit indépendant pendant l'attente ; ne pas certifier un profil inconnu.

Identifier le slicer disponible et sa version sans installation payante ni démarrage d'impression. Préparer des fichiers n'autorise pas à lancer la machine.

## Échelle, socle et géométrie

Lire [fabrication.md](references/fabrication.md). Fixer l'échelle physique avant épaisseurs, tenons et jeux. Mesurer hauteur, largeur et profondeur de la pose, puis avec socle. Garder la même échelle entre poses ; distinguer hauteur debout de référence et encombrement posé.

Créer le socle demandé, rond, ovale ou autre, avec bords et décor adaptés. Dimensionner selon emprise des appuis, débords, stabilité et attaches ; aucune formule universelle fondée sur la seule hauteur. Pour un usage de jeu réglementé, vérifier le format visé plutôt que prétendre qu'un socle proportionnel est officiel.

Sur la copie, figer la pose évaluée en préservant le détail utile. Convertir en géométrie les détails d'aspect qui doivent être imprimés. Former des volumes fermés et cohérents ; traiter intersections, doublons, volumes internes, épaisseurs et éléments fragiles. Des objets qui se touchent dans Blender ne constituent pas automatiquement une pièce imprimable.

## Stratégie de fabrication

Comparer monobloc et découpe selon surfaces visibles, supports, retrait des supports, orientation des couches, résistance, accès aux détails et assemblage. Regrouper les objets Blender selon la fabrication.

Retenir le nombre de pièces justifié par le modèle. Placer les joints discrètement et dans des zones accessibles ; ajouter tenons, logements ou détrompeurs utiles. Adapter les jeux au matériau, à l'orientation et à la calibration ; proposer un petit test d'emboîtement si nécessaire, sans inventer de précision mesurée.

Prévoir une orientation par pièce et vérifier l'encombrement utile du plateau, bordures et supports compris. Éviter supports emprisonnés et collage impossible.

## STL et validation

Exporter les pièces retenues en coordonnées correspondant à des millimètres. Réimporter réellement les STL dans une scène temporaire Blender et contrôler dimensions, nombre de pièces, géométrie et assemblage ; conserver les preuves de réimport.

Exécuter aussi l'audit STL partagé. Il contrôle géométrie, dimensions et fermeture mais ne remplace pas le slicer.

Si le slicer est accessible, trancher avec le profil retenu et ouvrir l'aperçu des couches : supports, îlots, détails disparus, parois, joints et orientation. Conserver captures et paramètres. Sans cette inspection, livrer GEOMETRY_PREPARED avec « tranchage non vérifié ». SLICER_VERIFIED exige ces preuves ; aucun de ces états ne signifie qu'un tirage physique a été testé.

## Livraison

Enregistrer l'examen selon le contrat partagé. Livrer .blend de fabrication, STL nommés, socle, dimensions en mm, vues assemblée et éclatée, orientation proposée, stratégie de supports et notice de montage. Un projet slicer 3MF peut compléter les STL si demandé et vérifié.

Examen initial puis trois corrections maximum ; garder sources et variantes antérieures. Ne pas contourner un défaut majeur ou une absence d'accès en déclarant une validation fictive.
