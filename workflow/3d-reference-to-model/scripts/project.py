#!/usr/bin/env python3
"""Create projects and check declared evidence. Does NOT perform visual inspection."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

STAGES = ("blockout", "geometry", "refinement", "finalization")
VIEWS = ("front", "side", "back", "three-quarter")
CHECKS = ("normals", "degenerate_faces", "intersections", "duplicates", "modifiers", "topology")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".exr"}
REVISION_ID = re.compile(r"r[0-9]{3,}")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    temporary.replace(path)


def inside(root, relative, prefix=None, required=False):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError(f"Chemin relatif invalide : {relative!r}")
    target = (root / relative).resolve()
    target.relative_to(root)
    if prefix:
        target.relative_to((root / prefix).resolve())
    if required and (not target.is_file() or target.stat().st_size == 0):
        raise ValueError(f"Fichier absent ou vide : {relative}")
    return target


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} est obligatoire")
    return value


def strings(value, label, nonempty=False):
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value) or (nonempty and not value):
        raise ValueError(f"{label} doit être une liste de textes renseignée")
    return value


def load_project(project):
    root = Path(project).resolve(strict=True)
    if root.parent.name != "projects":
        raise ValueError("Le projet doit être un enfant direct de projects/")
    for item in root.rglob("*"):
        if item.is_symlink() or (hasattr(item, "is_junction") and item.is_junction()):
            raise ValueError(f"Lien de fichiers interdit dans un projet : {item}")
    data = read_json(root / "project.yaml")
    if data.get("schema_version") != 1 or data.get("id") != root.name:
        raise ValueError("Version de manifeste ou identifiant incohérent")
    limit = data.get("correction_limit", 3)
    if type(limit) is not int or not 0 <= limit <= 10:
        raise ValueError("correction_limit doit être un entier de 0 à 10")
    if limit > 3:
        text(data.get("correction_limit_reason"), "Justification du dépassement")
    if not data.get("sources"):
        raise ValueError("Aucune référence source enregistrée")
    for source in data["sources"]:
        path = inside(root, source["path"], "references/source", required=True)
        if sha256(path) != source["sha256"]:
            raise ValueError(f"Référence source modifiée : {source['path']}")
    return root, data


def new_project(repo, slug, references, model_type="hybrid"):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) or len(slug) > 64:
        raise ValueError("Slug : 1 à 64 caractères minuscules, chiffres et tirets")
    if re.fullmatch(r"con|prn|aux|nul|com[1-9]|lpt[1-9]", slug):
        raise ValueError("Nom réservé sous Windows")
    repo = Path(repo).resolve(strict=True)
    projects = repo / "projects"
    if projects.resolve() != projects or projects.is_symlink():
        raise ValueError("projects/ doit être un dossier réel à la racine choisie")
    sources = [Path(p).resolve(strict=True) for p in references]
    if not sources or any(not p.is_file() or p.suffix.lower() not in IMAGE_EXTENSIONS or p.stat().st_size == 0 for p in sources):
        raise ValueError("Fournir au moins une image source non vide")
    if len({p.name.casefold() for p in sources}) != len(sources):
        raise ValueError("Noms de références identiques : attribuer des noms distincts")
    target = projects / slug
    if target.exists():
        raise FileExistsError(f"Projet existant, utiliser la reprise : {target}")
    projects.mkdir(exist_ok=True)
    target.mkdir()
    source_dir = target / "references/source"
    source_dir.mkdir(parents=True)
    entries = []
    for source in sources:
        output = source_dir / source.name
        shutil.copy2(source, output)
        entries.append({"path": output.relative_to(target).as_posix(), "original_name": source.name, "sha256": sha256(output)})
    write_json(target / "project.yaml", {
        "schema_version": 1, "id": slug, "title": slug,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "objective": "À préciser après inspection des références", "model_type": model_type,
        "status": "READY", "current_stage": "analysis", "sources": entries,
        "assumptions": [], "authoritative_reference": entries[0]["path"],
        "requested_exports": [], "correction_limit": 3, "correction_limit_reason": "", "stages": {},
    })
    return target


def stage_revision(data, stage):
    revision = data.get("revision")
    if revision and stage in STAGES[STAGES.index(revision["from_stage"]):]:
        return revision["id"]
    return data.get("stages", {}).get(stage, {}).get("revision_id")


def stage_path(kind, stage, revision_id=None):
    if kind not in {"reports", "previews"} or stage not in STAGES:
        raise ValueError("Chemin de jalon invalide")
    if revision_id is not None and (not isinstance(revision_id, str) or not REVISION_ID.fullmatch(revision_id)):
        raise ValueError("Identifiant de révision invalide")
    return f"{kind}/{stage}" + (f"/{revision_id}" if revision_id else "")


def revision_info(root, data, revision_id=None, check_protected=False):
    pointer = data.get("revision")
    if revision_id is not None:
        pointer = next((p for p in [data.get("revision"), *data.get("revision_history", [])] if p and p["id"] == revision_id), None)
    if not pointer:
        raise ValueError("Aucune révision correspondante")
    rid = pointer["id"]
    if not isinstance(rid, str) or not REVISION_ID.fullmatch(rid) or pointer["metadata"] != f"revisions/{rid}/revision.json":
        raise ValueError("Identifiant ou métadonnées de révision invalides")
    path = inside(root, pointer["metadata"], "revisions", required=True)
    if sha256(path) != pointer["sha256"]:
        raise ValueError("Métadonnées de révision modifiées")
    info = read_json(path)
    if info["id"] != rid or info["from_stage"] != pointer["from_stage"] or info["from_stage"] not in STAGES:
        raise ValueError("Révision incohérente")
    for key in ("previous_model", "previous_manifest", "rig"):
        entry = info[key]
        path = inside(root, entry["path"], required=True)
        if sha256(path) != entry["sha256"]:
            raise ValueError(f"Version précédente ou cadrage modifié : {entry['path']}")
    if check_protected:
        for relative, digest in info["protected_files"].items():
            path = inside(root, relative)
            if not path.is_file() or sha256(path) != digest:
                raise ValueError(f"Historique protégé modifié : {relative}")
    return info


def rig_path(data):
    return f"revisions/{data['revision']['id']}/camera-rig.json" if data.get("revision") else "previews/camera-rig.json"


def capture_views(revision_id=None):
    return (*VIEWS, "focus") if revision_id else VIEWS


def baseline_evidence(root, data, revision_id=None):
    info = revision_info(root, data, revision_id)
    receipt = read_json(inside(root, info["before_capture"], "previews", required=True))
    folder = str(Path(info["before_capture"]).parent).replace("\\", "/")
    if receipt.get("purpose") != "before" or receipt.get("revision_id") != info["id"] or receipt.get("stage") != info["from_stage"] or not receipt.get("neutral_settings") or receipt.get("engine") != "BLENDER_WORKBENCH":
        raise ValueError("Capture avant incompatible avec la révision")
    if receipt.get("blend_sha256") != info["previous_model"]["sha256"] or receipt.get("rig_sha256") != info["rig"]["sha256"]:
        raise ValueError("La capture avant ne correspond pas à la version précédente et à son cadrage")
    expected_views = [["front", [0, -1, 0]], ["side", [1, 0, 0]], ["back", [0, 1, 0]], ["three-quarter", [1, -1, 0.7]], ["focus", info["focus_direction"]]]
    if receipt.get("rig") != read_json(root / info["rig"]["path"]) or receipt.get("view_specs") != expected_views:
        raise ValueError("Les caméras de la capture avant ne correspondent pas à la révision")
    if set(receipt.get("images", {})) != set(capture_views(info["id"])):
        raise ValueError("Les quatre vues et la vue ciblée avant sont requises")
    for view in capture_views(info["id"]):
        entry = receipt["images"][view]
        if entry["path"] != f"{folder}/{view}.png" or sha256(inside(root, entry["path"], "previews", required=True)) != entry["sha256"]:
            raise ValueError(f"Capture avant modifiée ou invalide : {view}")
    return info, receipt


def revise(project, from_stage, request, targets=(), preserve=(), view_direction=(-1.0, 0.0, 0.0)):
    root, data = load_project(project)
    if data.get("status") != "COMPLETE":
        raise ValueError("Une révision ciblée exige un projet terminé ; reprendre le cycle actif sans remettre son compteur à zéro")
    validate(root, complete=True)
    if from_stage not in STAGES:
        raise ValueError("Jalon de reprise inconnu")
    text(request, "Demande de retouche")
    strings(list(targets), "Éléments ciblés")
    strings(list(preserve), "Éléments à préserver")
    direction = [float(v) for v in view_direction]
    if len(direction) != 3 or not all(math.isfinite(v) for v in direction) or sum(v*v for v in direction) <= 0:
        raise ValueError("La direction de comparaison doit être un vecteur fini non nul")
    original_rig = inside(root, rig_path(data), required=True)
    rig = read_json(original_rig)
    if len(rig.get("target", [])) != 3 or not all(math.isfinite(float(v)) for v in rig["target"]) or not math.isfinite(float(rig.get("ortho_scale", 0))) or rig["ortho_scale"] <= 0 or not math.isfinite(float(rig.get("diameter", 0))) or rig["diameter"] <= 0:
        raise ValueError("Le cadrage sauvegardé est invalide")
    numbers = [int(path.name[1:]) for path in (root / "revisions").glob("r*") if REVISION_ID.fullmatch(path.name)]
    rid = f"r{max(numbers, default=0)+1:03d}"
    directory = inside(root, f"revisions/{rid}", "revisions")
    previous_model = inside(root, f"blender/model-before-{rid}.blend", "blender")
    if directory.exists() or previous_model.exists():
        raise FileExistsError("Cette version précédente existe déjà")
    # Existing artifacts stay in place. All new outputs get a revision namespace.
    protected = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in {"project.yaml", "blender/model.blend"} or "__pycache__" in path.parts or path.suffix in {".tmp", ".pyc"} or re.fullmatch(r"model\.blend[0-9]+", path.name):
            continue
        protected[relative] = sha256(path)
    directory.mkdir(parents=True)
    created = []
    try:
        with (root / "blender/model.blend").open("rb") as source, previous_model.open("xb") as output:
            created.append(previous_model)
            shutil.copyfileobj(source, output)
        previous_manifest = directory / "project-before.json"
        previous_manifest.write_bytes((root / "project.yaml").read_bytes())
        created.append(previous_manifest)
        frozen_rig = directory / "camera-rig.json"
        frozen_rig.write_bytes(original_rig.read_bytes())
        created.append(frozen_rig)
        info = {
            "schema_version": 1, "id": rid, "from_stage": from_stage,
            "request": request, "targets": list(targets), "preserve": list(preserve),
            "focus_direction": direction, "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "previous_model": {"path": previous_model.relative_to(root).as_posix(), "sha256": sha256(previous_model)},
            "previous_manifest": {"path": previous_manifest.relative_to(root).as_posix(), "sha256": sha256(previous_manifest)},
            "rig": {"path": frozen_rig.relative_to(root).as_posix(), "sha256": sha256(frozen_rig)},
            "before_capture": stage_path("previews", from_stage, rid) + "/before/capture.json",
            "protected_files": protected,
        }
        metadata = directory / "revision.json"
        write_json(metadata, info)
        created.append(metadata)
        if data.get("revision"):
            data.setdefault("revision_history", []).append(data["revision"])
        data["revision"] = {"id": rid, "from_stage": from_stage, "metadata": metadata.relative_to(root).as_posix(), "sha256": sha256(metadata)}
        data["stages"] = {stage: state for stage, state in data["stages"].items() if STAGES.index(stage) < STAGES.index(from_stage)}
        data["status"], data["current_stage"] = "IN_PROGRESS", from_stage
        write_json(root / "project.yaml", data)
    except Exception:
        # No original artifact or working master was changed by this operation.
        for path in reversed(created):
            path.unlink(missing_ok=True)
        if directory.exists() and not any(directory.iterdir()):
            directory.rmdir()
        raise
    return {"revision": rid, "previous_model": info["previous_model"]["path"], "revalidate": list(STAGES[STAGES.index(from_stage):]), "before_capture": info["before_capture"]}


def attempts(root, stage, data=None):
    data = read_json(root / "project.yaml") if data is None else data
    records = sorted((root / stage_path("reports", stage, stage_revision(data, stage))).glob("attempt-[0-9][0-9].json"))
    values = [read_json(path) for path in records]
    if [v.get("attempt") for v in values] != list(range(len(values))):
        raise ValueError(f"Historique discontinu pour {stage}")
    return values


def validate_review(root, data, review, current_model=True):
    stage, status, attempt = review.get("stage"), review.get("status"), review.get("attempt")
    if stage not in STAGES or status not in {"PASS", "FAIL", "BLOCKED"}:
        raise ValueError("Jalon ou statut inconnu")
    text(review.get("justification"), "Justification")
    if type(attempt) is not int or not 0 <= attempt <= data.get("correction_limit", 3):
        raise ValueError("Limite de corrections atteinte ou numéro d'essai invalide")
    if status == "BLOCKED":
        return
    inspection = review.get("inspection", {})
    text(inspection.get("method"), "Méthode d'inspection visuelle effective")
    strings(inspection.get("observations"), "Observations visuelles", True)
    inspected = set(strings(inspection.get("inspected_images"), "Images réellement inspectées", True))
    if not {item["path"] for item in data["sources"]}.issubset(inspected):
        raise ValueError("Toutes les sources doivent avoir été réellement inspectées")
    revision_id = review.get("revision_id")
    folder = stage_path("previews", stage, revision_id) + f"/attempt-{attempt:02d}"
    receipt = read_json(inside(root, f"{folder}/capture.json", required=True))
    if receipt.get("stage") != stage or receipt.get("attempt") != attempt:
        raise ValueError("La capture ne correspond pas à cet essai")
    model = inside(root, "blender/model.blend", required=True)
    if current_model and sha256(model) != receipt.get("blend_sha256"):
        raise ValueError("Le .blend a changé depuis les captures ; recapturer et inspecter")
    views = capture_views(revision_id)
    if set(receipt.get("images", {})) != set(views):
        raise ValueError("Quatre vues Blender et la vue ciblée sont requises" if revision_id else "Quatre vues Blender sont requises")
    for view in views:
        entry, expected = receipt["images"][view], f"{folder}/{view}.png"
        if entry["path"] != expected or expected not in inspected:
            raise ValueError(f"Vue non inspectée ou chemin incohérent : {view}")
        if sha256(inside(root, expected, "previews", required=True)) != entry["sha256"]:
            raise ValueError(f"Capture modifiée : {view}")
    if revision_id:
        info, before = baseline_evidence(root, data, revision_id)
        if receipt.get("revision_id") != revision_id or receipt.get("purpose") != "stage" or receipt.get("rig_sha256") != before["rig_sha256"] or receipt.get("rig") != before.get("rig") or receipt.get("resolution") != before.get("resolution") or receipt.get("collection") != before.get("collection") or receipt.get("view_specs") != before.get("view_specs") or receipt.get("engine") != before.get("engine") or receipt.get("neutral_settings") != before.get("neutral_settings"):
            raise ValueError("Avant/après incompatible : mêmes caméras, résolution, collection et éclairage requis")
        if not {entry["path"] for entry in before["images"].values()}.issubset(inspected):
            raise ValueError("Les images avant doivent avoir été réellement inspectées")
        comparison = review.get("comparison", {})
        strings(comparison.get("observations"), "Observations avant/après", True)
        strings(comparison.get("changes"), "Modifications ciblées", True)
        if comparison.get("outcome") not in {"improved", "equivalent", "regressed"}:
            raise ValueError("Bilan avant/après attendu : improved, equivalent ou regressed")
        if status == "PASS" and comparison["outcome"] == "regressed":
            raise ValueError("Une régression avant/après interdit PASS")
        for constraint in info["preserve"]:
            text(comparison.get("preservation_checks", {}).get(constraint), f"Vérification de préservation : {constraint}")
    corrections = strings(review.get("corrections"), "Corrections")
    if (attempt == 0 and corrections) or (attempt > 0 and not corrections):
        raise ValueError("L'essai initial précède les corrections ; les suivants doivent les décrire")
    defects = review.get("defects")
    if not isinstance(defects, list) or len(defects) > 3:
        raise ValueError("Documenter au plus trois défauts prioritaires")
    for defect in defects:
        if defect.get("category") not in {"proportions", "silhouette", "geometry", "detail"} or defect.get("severity") not in {"major", "minor"} or type(defect.get("resolved")) is not bool:
            raise ValueError("Catégorie, gravité ou résolution du défaut invalide")
        text(defect.get("description"), "Description du défaut")
        if status == "PASS" and defect["severity"] == "major" and not defect["resolved"]:
            raise ValueError("Un défaut majeur non résolu interdit PASS")
    strings(review.get("remaining_issues"), "Problèmes restants")
    if status == "FAIL" and not review["remaining_issues"]:
        raise ValueError("FAIL doit préciser les problèmes restants")
    checkpoint = review.get("best_checkpoint")
    if status == "FAIL" and not checkpoint:
        raise ValueError("Conserver un meilleur checkpoint avant de déclarer FAIL")
    checkpoint_prefix = "blender/checkpoints" + (f"/{revision_id}" if revision_id else "")
    if checkpoint and inside(root, checkpoint, checkpoint_prefix, required=True).suffix != ".blend":
        raise ValueError("Le checkpoint doit être un fichier .blend")
    if status == "PASS" and stage in {"geometry", "finalization"}:
        for key in CHECKS:
            text(review.get("geometry_checks", {}).get(key), f"Contrôle Blender : {key}")
    if status == "PASS" and stage == "finalization":
        text(review.get("scene_check"), "Contrôle du .blend sauvegardé/réouvert")
        extensions = set()
        for entry in review.get("export_checks", []):
            path = inside(root, entry["path"], "exports" + (f"/{revision_id}" if revision_id else ""), required=True)
            text(entry.get("method"), "Méthode de contrôle de l'export")
            if entry.get("status") != "PASS":
                raise ValueError("Un export final n'a pas passé son contrôle")
            extensions.add(path.suffix.lower().lstrip("."))
        if not set(data.get("requested_exports", [])).issubset(extensions):
            raise ValueError("Des formats d'export demandés ne sont pas contrôlés")


def record(project, review):
    root, data = load_project(project)
    # A prior PASS is usable only while its recorded evidence remains intact.
    validate(root)
    stage = review.get("stage")
    if stage not in STAGES:
        raise ValueError("Jalon inconnu")
    for previous in STAGES[:STAGES.index(stage)]:
        if data["stages"].get(previous, {}).get("status") != "PASS":
            raise ValueError(f"{previous} doit être PASS avant {stage}")
    revision_id = stage_revision(data, stage)
    if review.get("revision_id") is not None and review["revision_id"] != revision_id:
        raise ValueError("La déclaration concerne une autre révision")
    review = dict(review)
    if revision_id:
        review["revision_id"] = revision_id
    history = attempts(root, stage, data)
    if history and history[-1]["status"] == "PASS":
        raise ValueError("Jalon déjà validé ; reprendre le jalon suivant")
    if review.get("attempt") != len(history):
        raise ValueError(f"Prochain essai attendu : {len(history)}")
    validate_review(root, data, review)
    report = dict(review, recorded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    name = "blocked" if report["status"] == "BLOCKED" else f"attempt-{report['attempt']:02d}"
    path = root / stage_path("reports", stage, revision_id) / f"{name}.json"
    if path.exists() and name != "blocked":
        raise FileExistsError("Un rapport d'essai existant ne doit pas être écrasé")
    if report["status"] != "BLOCKED":
        report["blend_sha256"] = sha256(root / "blender/model.blend")
    write_json(path, report)
    lines = [f"# {stage} — {report['status']}", "", report["justification"], "", f"Corrections : {report['attempt']}/{data.get('correction_limit', 3)}", ""]
    for label, values in (("Observations", report.get("inspection", {}).get("observations", [])), ("Corrections effectuées", report.get("corrections", [])), ("Problèmes restants", report.get("remaining_issues", []))):
        lines.extend([f"## {label}", ""] + [f"- {value}" for value in values] + [""])
    if revision_id and report["status"] != "BLOCKED":
        info, before = baseline_evidence(root, data, revision_id)
        after = read_json(root / stage_path("previews", stage, revision_id) / f"attempt-{report['attempt']:02d}" / "capture.json")
        def link(relative):
            return quote(os.path.relpath(root / relative, path.parent).replace("\\", "/"), safe="/")
        comparison = report["comparison"]
        lines += ["## Avant / après — vue ciblée", "", "| Avant | Après |", "| --- | --- |",
                  f"| ![Avant]({link(before['images']['focus']['path'])}) | ![Après]({link(after['images']['focus']['path'])}) |", "",
                  f"Bilan déclaré : {comparison['outcome']}.", ""]
        lines += [f"- {value}" for value in comparison["observations"]] + [""]
        lines += [f"- {constraint} : {result}" for constraint, result in comparison.get("preservation_checks", {}).items()]
    path.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")
    data["stages"][stage] = {"status": report["status"], "attempt": report["attempt"], "report": path.relative_to(root).as_posix()}
    if revision_id:
        data["stages"][stage]["revision_id"] = revision_id
    exhausted = report["status"] == "FAIL" and report["attempt"] >= data.get("correction_limit", 3)
    data["status"] = "BLOCKED" if report["status"] == "BLOCKED" or exhausted else "IN_PROGRESS"
    data["current_stage"] = stage
    if report["status"] == "PASS":
        index = STAGES.index(stage)
        data["current_stage"] = STAGES[index + 1] if index < len(STAGES) - 1 else "complete"
        if stage == "finalization":
            data["status"] = "COMPLETE"
    write_json(root / "project.yaml", data)
    return path


def validate(project, complete=False):
    root, data = load_project(project)
    for pointer in [*data.get("revision_history", []), data.get("revision")]:
        if pointer:
            revision_info(root, data, pointer["id"], check_protected=True)
    if data.get("revision"):
        info = revision_info(root, data)
        if (root / info["before_capture"]).exists():
            baseline_evidence(root, data)
    earlier_passed = True
    for stage in STAGES:
        records = attempts(root, stage, data)
        state = data["stages"].get(stage)
        if (records or state) and not earlier_passed:
            raise ValueError(f"{stage} a commencé avant validation du précédent")
        for index, review in enumerate(records):
            if review.get("stage") != stage or review.get("revision_id") != stage_revision(data, stage) or (index < len(records) - 1 and review.get("status") == "PASS"):
                raise ValueError("Historique des jalons incohérent")
            validate_review(root, data, review, current_model=False)
        if state:
            report = read_json(inside(root, state["report"], f"reports/{stage}", required=True))
            if (report.get("status"), report.get("stage"), report.get("attempt"), report.get("revision_id")) != (state["status"], stage, state["attempt"], stage_revision(data, stage)):
                raise ValueError("Le manifeste ne correspond pas au rapport")
            if state["status"] != "BLOCKED" and (not records or report != records[-1]):
                raise ValueError("Le manifeste ne pointe pas vers le dernier essai")
            validate_review(root, data, report, current_model=False)
        elif records:
            raise ValueError("Rapports absents du manifeste")
        earlier_passed = bool(state and state["status"] == "PASS")
        if complete and not earlier_passed:
            raise ValueError(f"Jalon non validé : {stage}")
    if complete:
        if data.get("status") != "COMPLETE":
            raise ValueError("Le projet n'est pas déclaré terminé")
        final = read_json(root / data["stages"]["finalization"]["report"])
        if sha256(inside(root, "blender/model.blend", required=True)) != final["blend_sha256"]:
            raise ValueError("Le modèle final a changé depuis sa validation")
    return {"id": data["id"], "status": data["status"], "current_stage": data["current_stage"], "structural_validation": "PASS", "visual_validation": "déclarée par les rapports ; non effectuée par ce script"}


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("new")
    create.add_argument("--repo", type=Path, default=Path.cwd())
    create.add_argument("--slug", required=True)
    create.add_argument("--reference", action="append", required=True)
    create.add_argument("--model-type", choices=("organic", "hard-surface", "hybrid"), default="hybrid")
    check = commands.add_parser("validate")
    check.add_argument("project", type=Path)
    check.add_argument("--complete", action="store_true")
    review = commands.add_parser("record")
    review.add_argument("project", type=Path)
    review.add_argument("--review", type=Path, required=True)
    revision = commands.add_parser("revise", help="Préserver la livraison et ouvrir une retouche ciblée, sans modifier le modèle")
    revision.add_argument("project", type=Path)
    revision.add_argument("--from-stage", choices=STAGES, required=True)
    revision.add_argument("--request", required=True)
    revision.add_argument("--target", action="append", default=[])
    revision.add_argument("--preserve", action="append", default=[])
    revision.add_argument("--view-direction", type=float, nargs=3, default=(-1.0, 0.0, 0.0))
    args = parser.parse_args()
    try:
        if args.command == "new":
            print(new_project(args.repo, args.slug, args.reference, args.model_type))
        elif args.command == "validate":
            print(json.dumps(validate(args.project, args.complete), ensure_ascii=False, indent=2))
        elif args.command == "revise":
            print(json.dumps(revise(args.project, args.from_stage, args.request, args.target, args.preserve, args.view_direction), ensure_ascii=False, indent=2))
        else:
            print(record(args.project, read_json(args.review)))
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"ERREUR : {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
