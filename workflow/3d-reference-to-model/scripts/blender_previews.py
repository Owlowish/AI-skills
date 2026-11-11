#!/usr/bin/env python3
"""Prepare safe bpy code; seal real Blender render receipts outside Blender."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from project import (STAGES, VIEWS, attempts, baseline_evidence, capture_views, inside,
                     load_project, read_json, revision_info, rig_path, sha256,
                     stage_path, stage_revision, validate, write_json)


def prepare(project, stage=None, attempt=None, collection="MODEL", resolution=768, before=False):
    root, data = load_project(project)
    validate(root)
    info = revision_info(root, data) if data.get("revision") else None
    if before:
        if not info:
            raise ValueError("Créer une révision ciblée avant la capture avant")
        stage, attempt = info["from_stage"], 0
    if stage not in STAGES or type(attempt) is not int or not 0 <= attempt <= data.get("correction_limit", 3):
        raise ValueError("Jalon/essai invalide ou limite de corrections atteinte")
    for previous in STAGES[:STAGES.index(stage)]:
        if data["stages"].get(previous, {}).get("status") != "PASS":
            raise ValueError(f"Jalon précédent non validé : {previous}")
    history = attempts(root, stage, data)
    if not before and (attempt != len(history) or (history and history[-1]["status"] == "PASS")):
        raise ValueError("Essai incompatible avec l'historique du projet")
    if not 128 <= resolution <= 2048 or not collection:
        raise ValueError("Résolution attendue de 128 à 2048 ; collection explicite requise")
    model = inside(root, "blender/model.blend", required=True)
    revision_id = stage_revision(data, stage)
    if before and sha256(model) != info["previous_model"]["sha256"]:
        raise ValueError("Le maître a déjà été modifié : la capture avant doit précéder toute retouche")
    if revision_id and not before:
        _, baseline = baseline_evidence(root, data, revision_id)
        if resolution != baseline["resolution"] or collection != baseline["collection"]:
            raise ValueError("Conserver la même résolution et la même collection que la capture avant")
    relative = stage_path("previews", stage, revision_id) + ("/before" if before else f"/attempt-{attempt:02d}")
    folder = inside(root, relative, "previews")
    if folder.exists():
        raise FileExistsError("Cet essai a déjà été préparé : réutiliser ses arguments MCP, sans écraser ses captures")
    rig_file = root / rig_path(data)
    rig = read_json(rig_file) if rig_file.exists() else None
    folder.mkdir(parents=True)
    views = [("front", (0, -1, 0)), ("side", (1, 0, 0)), ("back", (0, 1, 0)), ("three-quarter", (1, -1, 0.7))]
    if revision_id:
        views.append(("focus", info["focus_direction"]))
    config = {"project": str(root), "model": model.as_posix(), "collection": collection,
              "stage": stage, "attempt": attempt, "folder": folder.as_posix(),
              "resolution": resolution, "rig": rig, "views": views,
              "purpose": "before" if before else "stage", "revision_id": revision_id}
    # Only bpy/mathutils/json inside the MCP safe-mode payload. No open/exec/pathlib.
    code = 'import bpy\nimport json\nfrom mathutils import Vector\nsettings = json.loads(' + repr(json.dumps(config)) + ')\n' + CAPTURE_CODE
    report_folder = root / stage_path("reports", stage, revision_id)
    report_folder.mkdir(parents=True, exist_ok=True)
    code_path = report_folder / ("preview-before.py" if before else f"preview-attempt-{attempt:02d}.py")
    code_path.write_text(code, encoding="utf-8")
    arguments = code_path.with_suffix(".arguments.json")
    write_json(arguments, {"code": code})
    write_json(folder / "prepared.json", {"stage": stage, "attempt": attempt, "blend_sha256": sha256(model), "collection": collection, "resolution": resolution, "rig": rig,
                                          "views": views, "purpose": config["purpose"], "revision_id": revision_id})
    return arguments


CAPTURE_CODE = r'''
if bpy.data.filepath.replace(chr(92), "/") != settings["model"]:
    raise RuntimeError("Ouvrir le model.blend du projet avant la capture")
if bpy.data.is_dirty:
    raise RuntimeError("Sauvegarder les modifications du modèle avant la capture")
source = bpy.context.scene
collection = bpy.data.collections.get(settings["collection"])
if collection is None or collection.name not in [child.name for child in source.collection.children_recursive]:
    raise RuntimeError("Collection MODEL absente de la scène active")
preview = bpy.data.scenes.new("Validation temporaire")
created_objects = []
created_meshes = []
camera_data = None
world = None
try:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    corners = []
    for obj in list(collection.all_objects):
        if obj.type not in {"MESH", "CURVE", "SURFACE", "FONT", "META"} or obj.hide_render:
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=depsgraph)
        created_meshes.append(mesh)
        copied = bpy.data.objects.new("Validation " + obj.name, mesh)
        created_objects.append(copied)
        copied.matrix_world = obj.matrix_world.copy()
        preview.collection.objects.link(copied)
        if mesh.vertices:
            low = [min(vertex.co[i] for vertex in mesh.vertices) for i in range(3)]
            high = [max(vertex.co[i] for vertex in mesh.vertices) for i in range(3)]
            corners.extend([obj.matrix_world @ Vector((x, y, z))
                            for x in (low[0], high[0]) for y in (low[1], high[1])
                            for z in (low[2], high[2])])
    if not corners:
        raise RuntimeError("Aucune géométrie visible à capturer")
    minimum = Vector([min(p[i] for p in corners) for i in range(3)])
    maximum = Vector([max(p[i] for p in corners) for i in range(3)])
    diameter = (maximum - minimum).length
    if diameter <= 0:
        raise RuntimeError("Dimensions du modèle nulles")
    rig = settings["rig"]
    if rig is None:
        rig = {"version": 1, "target": list((minimum + maximum) / 2), "diameter": diameter,
               "ortho_scale": diameter * 1.25, "front_axis": "-Y", "up_axis": "+Z"}
    target = Vector(rig["target"])
    world = bpy.data.worlds.new("Validation neutre")
    world.color = (0.12, 0.12, 0.12)
    preview.world = world
    preview.render.engine = "BLENDER_WORKBENCH"
    preview.display.shading.light = "STUDIO"
    preview.display.shading.studio_light = "paint.sl"
    preview.display.shading.studiolight_rotate_z = 0
    preview.display.shading.color_type = "SINGLE"
    preview.display.shading.single_color = (0.62, 0.62, 0.62)
    preview.display.shading.background_type = "WORLD"
    preview.display.shading.show_shadows = True
    preview.display.shading.show_cavity = True
    preview.view_settings.view_transform = "Standard"
    preview.view_settings.exposure = 0
    preview.view_settings.gamma = 1
    preview.render.resolution_x = settings["resolution"]
    preview.render.resolution_y = settings["resolution"]
    preview.render.resolution_percentage = 100
    preview.render.film_transparent = False
    preview.render.image_settings.file_format = "PNG"
    preview.render.image_settings.color_mode = "RGB"
    preview.render.image_settings.color_depth = "8"
    camera_data = bpy.data.cameras.new("Validation caméra")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = rig["ortho_scale"]
    camera_data.clip_start = max(rig["diameter"] * 0.00001, 0.000001)
    camera_data.clip_end = rig["diameter"] * 20
    camera = bpy.data.objects.new("Validation caméra", camera_data)
    created_objects.append(camera)
    preview.collection.objects.link(camera)
    preview.camera = camera
    rendered = []
    for view, direction in settings["views"]:
        camera.location = target + Vector(direction).normalized() * rig["diameter"] * 3
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        inverse_rotation = camera.rotation_euler.to_matrix().transposed()
        for corner in corners:
            point = inverse_rotation @ (corner - target)
            if max(abs(point.x), abs(point.y)) > rig["ortho_scale"] * 0.49:
                raise RuntimeError("Modèle hors cadrage fixe : documenter puis réviser le camera-rig, sans recadrage silencieux")
        preview.render.filepath = settings["folder"] + "/" + view + ".png"
        bpy.ops.render.render(write_still=True, scene=preview.name)
        rendered.append(view)
    print("REFERENCE_TO_3D_CAPTURE=" + json.dumps({"stage": settings["stage"], "attempt": settings["attempt"],
          "rendered": rendered, "rig": rig, "blender_version": bpy.app.version_string,
          "engine": preview.render.engine, "resolution": settings["resolution"], "source_scene": source.name,
          "purpose": settings["purpose"], "revision_id": settings["revision_id"], "view_specs": settings["views"],
          "neutral_settings": {"light": preview.display.shading.light, "studio_light": preview.display.shading.studio_light,
                               "rotation": preview.display.shading.studiolight_rotate_z, "color_type": preview.display.shading.color_type,
                               "color": list(preview.display.shading.single_color), "view_transform": preview.view_settings.view_transform,
                               "exposure": preview.view_settings.exposure, "gamma": preview.view_settings.gamma}}))
finally:
    bpy.data.scenes.remove(preview)
    for obj in created_objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in created_meshes:
        bpy.data.meshes.remove(mesh)
    if camera_data is not None:
        bpy.data.cameras.remove(camera_data)
    if world is not None:
        bpy.data.worlds.remove(world)
'''


def find_capture(value):
    marker = "REFERENCE_TO_3D_CAPTURE="
    if isinstance(value, str):
        for line in value.splitlines():
            if marker in line:
                return json.loads(line.split(marker, 1)[1])
    if isinstance(value, dict):
        for child in value.values():
            result = find_capture(child)
            if result:
                return result
    if isinstance(value, list):
        for child in value:
            result = find_capture(child)
            if result:
                return result
    return None


def finish(project, stage, attempt, result_path, before=False):
    root, data = load_project(project)
    info = revision_info(root, data) if data.get("revision") else None
    if before:
        if not info:
            raise ValueError("Aucune révision pour la capture avant")
        stage, attempt = info["from_stage"], 0
    if stage not in STAGES or type(attempt) is not int or attempt < 0:
        raise ValueError("Jalon ou essai invalide")
    revision_id = stage_revision(data, stage)
    relative = stage_path("previews", stage, revision_id) + ("/before" if before else f"/attempt-{attempt:02d}")
    folder = inside(root, relative, "previews")
    if (folder / "capture.json").exists():
        raise FileExistsError("Reçu de capture déjà présent")
    prepared = read_json(folder / "prepared.json")
    purpose = "before" if before else "stage"
    # Initial projects made before revision support have no purpose/view_specs.
    # Their original four-view payload remains finishable; revisions stay strict.
    legacy = revision_id is None and "purpose" not in prepared
    prepared_views = prepared.get("views", [["front", [0, -1, 0]], ["side", [1, 0, 0]], ["back", [0, 1, 0]], ["three-quarter", [1, -1, 0.7]]])
    if prepared.get("purpose", "stage" if legacy else None) != purpose or prepared.get("revision_id") != revision_id or prepared.get("stage") != stage or prepared.get("attempt") != attempt:
        raise ValueError("La préparation ne correspond pas à cette capture")
    response = read_json(result_path)
    if isinstance(response, dict) and (response.get("status") == "FAIL" or response.get("isError")):
        raise ValueError("L'appel MCP de capture a échoué")
    capture = find_capture(response)
    if not capture or capture.get("stage") != stage or capture.get("attempt") != attempt or capture.get("rendered") != list(capture_views(revision_id)):
        raise ValueError("Le résultat MCP ne confirme pas les quatre rendus Blender de cet essai")
    if capture.get("purpose", "stage" if legacy else None) != purpose or capture.get("revision_id") != revision_id or capture.get("view_specs", prepared_views if legacy else None) != prepared_views:
        raise ValueError("La réponse Blender ne confirme pas les mêmes vues et la même révision")
    if sha256(inside(root, "blender/model.blend", required=True)) != prepared["blend_sha256"]:
        raise ValueError("Le .blend a changé pendant la capture")
    if prepared["rig"] is not None and prepared["rig"] != capture["rig"]:
        raise ValueError("Le cadrage de capture a changé")
    if before and prepared["blend_sha256"] != info["previous_model"]["sha256"]:
        raise ValueError("La capture avant ne correspond pas au modèle précédent")
    if revision_id and not before:
        _, baseline = baseline_evidence(root, data, revision_id)
        if capture.get("rig") != baseline["rig"] or capture.get("resolution") != baseline["resolution"] or prepared["collection"] != baseline["collection"] or capture.get("neutral_settings") != baseline.get("neutral_settings") or capture.get("engine") != baseline.get("engine"):
            raise ValueError("Avant/après incompatible : cadrage, éclairage ou résolution différents")
    images = {}
    for view in capture_views(revision_id):
        path = inside(root, f"{relative}/{view}.png", "previews", required=True)
        header = path.read_bytes()[:24]
        if not header.startswith(b"\x89PNG\r\n\x1a\n") or int.from_bytes(header[16:20], "big") != prepared["resolution"] or int.from_bytes(header[20:24], "big") != prepared["resolution"]:
            raise ValueError(f"PNG invalide ou dimensions inattendues : {view}")
        images[view] = {"path": path.relative_to(root).as_posix(), "sha256": sha256(path)}
    rig_file = root / rig_path(data)
    if rig_file.exists() and read_json(rig_file) != capture["rig"]:
        raise ValueError("Le cadrage enregistré a changé depuis la préparation")
    if not rig_file.exists():
        write_json(rig_file, capture["rig"])
    write_json(folder / "capture.json", dict(capture, blend_sha256=prepared["blend_sha256"], collection=prepared["collection"], images=images, rig_sha256=sha256(rig_file)))
    return folder / "capture.json"


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "finish", "prepare-before", "finish-before"):
        cmd = commands.add_parser(name)
        cmd.add_argument("project", type=Path)
        if not name.endswith("-before"):
            cmd.add_argument("--stage", choices=STAGES, required=True)
            cmd.add_argument("--attempt", type=int, required=True)
        if name.startswith("prepare"):
            cmd.add_argument("--collection", default="MODEL")
            cmd.add_argument("--resolution", type=int, default=768)
        else:
            cmd.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    try:
        before = args.command.endswith("-before")
        stage, attempt = getattr(args, "stage", None), getattr(args, "attempt", None)
        result = prepare(args.project, stage, attempt, args.collection, args.resolution, before) if args.command.startswith("prepare") else finish(args.project, stage, attempt, args.result, before)
        print(result)
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"ERREUR : {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
