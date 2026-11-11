#!/usr/bin/env python3
"""Provenance et examens des variantes Blender rig, pose et FDM."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import subprocess
import sys
from audit_stl import audit_stl

CHECKS = {
    "rig": ("rest_shape", "controls", "bindings", "range_of_motion", "collisions"),
    "pose": ("intent", "contacts_balance", "joint_limits", "collisions", "hidden_views", "scale_preserved"),
    "fdm": ("scale", "watertightness", "thin_features", "part_strategy", "assembly",
            "base_and_stability", "orientation_and_supports", "exports_reimport"),
}
CORE = Path(__file__).resolve().parents[2] / "3d-reference-to-model/scripts/project.py"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inside(root, value):
    p = Path(value)
    p = (root / p).resolve() if not p.is_absolute() else p.resolve()
    try:
        p.relative_to(root)
    except ValueError as exc:
        raise ValueError("Chemin hors du projet : " + str(value)) from exc
    return p


def relative(root, path):
    return str(Path(path).relative_to(root)).replace("\\", "/")


def evidence(root, value):
    p = inside(root, value)
    if not p.is_file() or p.stat().st_size == 0:
        raise ValueError("Preuve absente ou vide : " + str(value))
    return {"path": relative(root, p), "sha256": sha(p)}


def png(root, value):
    p = inside(root, value)
    data = p.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("Capture PNG invalide : " + str(value))
    if min(struct.unpack(">II", data[16:24])) < 128:
        raise ValueError("Capture trop petite pour l'inspection : " + str(value))
    return evidence(root, value)


def text(value, minimum=24):
    return isinstance(value, str) and len(value.strip()) >= minimum


def triple(value):
    return (isinstance(value, list) and len(value) == 3
            and all(isinstance(x, (int, float)) and not isinstance(x, bool)
                    and math.isfinite(x) and x > 0 for x in value))


def mcp_failed(value):
    if not isinstance(value, dict):
        return True
    if value.get("isError"):
        return True
    structured = value.get("structuredContent")
    messages = [value.get("result"), structured.get("result") if isinstance(structured, dict) else None]
    blocks = value.get("content")
    if isinstance(blocks, list):
        messages.extend(block.get("text") for block in blocks
                        if isinstance(block, dict) and block.get("type") == "text")
    messages = [message for message in messages if isinstance(message, str) and message.strip()]
    if not messages:
        return True
    for message in messages:
        lowered = message.strip().lower()
        if lowered.startswith(("error", "rejected", "traceback", "couldn't ", "could not ")) or "traceback (most recent call last)" in lowered:
            return True
    return False


def validate_base(root):
    result = subprocess.run([sys.executable, str(CORE), "validate", str(root), "--complete"],
                            capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise ValueError("Projet de modélisation non validé : " + (result.stderr or result.stdout).strip())


def locate(manifest):
    manifest = Path(manifest).resolve()
    for parent in manifest.parents:
        if (parent / "project.yaml").is_file():
            data = read(manifest)
            expected = parent / "reports" / data["kind"] / data["label"] / data["revision"] / "manifest.json"
            if expected.resolve() != manifest:
                raise ValueError("Manifeste hors de son espace de variante.")
            return parent, data
    raise ValueError("Aucun projet trouvé pour ce manifeste.")


def verify(manifest, require_pass=True, seen=None):
    root, data = locate(manifest)
    seen = set() if seen is None else seen
    key = str(Path(manifest).resolve())
    if key in seen:
        raise ValueError("Cycle de provenance.")
    seen.add(key)
    if require_pass and data["status"] != "PASS":
        raise ValueError("La variante amont n'est pas PASS.")
    source = inside(root, data["source"]["path"])
    if not source.is_file() or sha(source) != data["source"]["sha256"]:
        raise ValueError("La source a changé : variante périmée.")
    if data.get("upstream"):
        upstream = inside(root, data["upstream"]["path"])
        if sha(upstream) != data["upstream"]["sha256"]:
            raise ValueError("Le manifeste amont a changé.")
        up = verify(upstream, seen=seen)
        if data["source"]["path"] != up["master"]["path"]:
            raise ValueError("La source ne correspond pas au maître amont.")
    else:
        if source != (root / "blender/model.blend").resolve():
            raise ValueError("Source sans validation amont.")
        validate_base(root)
    for item in data.get("evidence", []):
        p = inside(root, item["path"])
        if not p.is_file() or sha(p) != item["sha256"]:
            raise ValueError("Preuve modifiée : " + item["path"])
    if data["status"] == "PASS":
        item = data["master"]
        if sha(inside(root, item["path"])) != item["sha256"]:
            raise ValueError("Le maître validé a changé.")
    return data


def new_run(root, kind, label, mode, source, request, upstream=None):
    root = Path(root).resolve(strict=True)
    if not (root / "project.yaml").is_file():
        raise ValueError("project.yaml absent.")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", label) or len(label) > 64:
        raise ValueError("Label invalide.")
    if kind not in CHECKS or not text(request, 8):
        raise ValueError("Type ou demande invalide.")
    source_path = inside(root, source)
    if source_path.suffix.lower() != ".blend" or not source_path.is_file():
        raise ValueError("Source .blend absente.")
    upstream_item = None
    if upstream:
        up_path = inside(root, upstream)
        up = verify(up_path)
        if source_path != inside(root, up["master"]["path"]):
            raise ValueError("La source ne correspond pas au maître amont.")
        wanted = {"pose": "rig", "fdm": "pose"}.get(kind)
        if up["kind"] != wanted:
            raise ValueError("Étape amont incompatible.")
        mode = mode or up["mode"]
        upstream_item = evidence(root, upstream)
    else:
        if source_path != (root / "blender/model.blend").resolve():
            raise ValueError("Une variante source exige --upstream.")
        validate_base(root)
        mode = mode or ("static" if kind != "rig" else None)
        if kind != "rig" and mode != "static":
            raise ValueError("Pose articulée : utiliser un rig validé.")
    if mode not in ("rigid", "deforming", "hybrid", "static") or (kind == "rig" and mode == "static"):
        raise ValueError("Mode invalide ; un objet fixe n'exige pas de rig.")
    folder = root / "reports" / kind / label
    previous = sorted(folder.glob("r[0-9][0-9][0-9]/manifest.json"))
    if previous and read(previous[-1])["status"] != "PASS":
        raise ValueError("Continuer le run existant et son budget ; ne pas le réinitialiser.")
    revision = f"r{len(previous)+1:03d}"
    report = folder / revision
    master = root / "blender" / kind / label / revision / (kind + ".blend")
    previews = root / "previews" / kind / label / revision
    exports = root / "exports/fdm" / label / revision
    for p in [report, master.parent, previews] + ([exports] if kind == "fdm" else []):
        p.mkdir(parents=True, exist_ok=False)
    data = {"schema_version": 1, "kind": kind, "label": label, "revision": revision,
            "mode": mode, "request": request, "status": "DRAFT", "next_attempt": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": evidence(root, source), "upstream": upstream_item,
            "master": {"path": relative(root, master), "sha256": None},
            "previews": relative(root, previews), "exports": relative(root, exports) if kind == "fdm" else None,
            "reviews": [], "evidence": []}
    target = report / "manifest.json"
    write_new(target, data)
    return {"manifest": str(target), "master": str(master), "status": "DRAFT"}


def fdm_review(root, data, review):
    profile = review.get("print_profile", {})
    nominal, usable = profile.get("nominal_volume_mm"), profile.get("usable_volume_mm")
    nozzle = profile.get("nozzle_mm")
    if (not text(profile.get("machine"), 3) or not text(profile.get("filament"), 2)
        or not triple(nominal) or not triple(usable) or any(a > b for a, b in zip(usable, nominal))
        or not isinstance(nozzle, (int, float)) or isinstance(nozzle, bool)
        or not math.isfinite(nozzle) or nozzle <= 0):
        raise ValueError("Profil machine, buse, filament ou volume utile incomplet.")
    if "a1mini" in re.sub(r"[^a-z0-9]", "", profile["machine"].lower()) and nominal != [180, 180, 180]:
        raise ValueError("Volume nominal A1 mini incohérent.")
    sizes = review.get("dimensions_mm", {})
    if not all(triple(sizes.get(key)) for key in ("figure", "with_base")):
        raise ValueError("Dimensions de la figurine et avec socle requises en mm.")
    parts = review.get("exports")
    if not isinstance(parts, list) or not parts:
        raise ValueError("Aucun STL final déclaré.")
    export_dir = inside(root, data["exports"])
    actual = {p.resolve() for p in export_dir.rglob("*") if p.is_file() and p.suffix.lower() == ".stl"}
    selected, files, audits = set(), [], []
    for part in parts:
        p = inside(root, part["path"])
        if not p.is_relative_to(export_dir) or p.suffix.lower() != ".stl" or p in selected:
            raise ValueError("STL hors du run, dupliqué ou extension incorrecte.")
        selected.add(p)
        allow = part.get("allow_multiple_shells", False)
        if allow and not text(part.get("shells_justification"), 30):
            raise ValueError("Plusieurs surfaces : justification et examen requis.")
        result = audit_stl(p, part.get("dimensions_mm"), allow)
        if not triple(part.get("dimensions_mm")) or result["status"] != "PASS":
            raise ValueError("STL invalide : " + str(result["issues"]))
        if any(x > y + .001 for x, y in zip(result["dimensions_mm"], usable)):
            raise ValueError("Pièce trop grande dans l'orientation proposée : " + part["path"])
        files.extend([evidence(root, part["path"]), evidence(root, part["reimport_evidence"])])
        if mcp_failed(read(inside(root, part["reimport_evidence"]))):
            raise ValueError("Le réimport Blender a échoué.")
        audits.append({"path": part["path"], **result})
    if actual != selected:
        raise ValueError("La liste des STL ne correspond pas au dossier final.")
    ready = review.get("readiness")
    if ready not in ("GEOMETRY_PREPARED", "SLICER_VERIFIED"):
        raise ValueError("État de préparation FDM absent ou invalide.")
    if ready == "SLICER_VERIFIED":
        files.append(evidence(root, review["slicer_evidence"]))
        images = review.get("slicer_images", [])
        if not images:
            raise ValueError("Captures du tranchage inspecté requises.")
        files.extend(png(root, image) for image in images)
    return files, audits


def record(manifest, review_path):
    manifest = Path(manifest).resolve()
    root, data = locate(manifest)
    verify(manifest, require_pass=False)
    if data["status"] in ("PASS", "FAIL_FINAL"):
        raise ValueError("Run terminé ; ne pas écraser ses examens.")
    review_path = inside(root, review_path)
    if review_path.parent != manifest.parent:
        raise ValueError("La revue doit être dans le dossier du run.")
    review = read(review_path)
    status, attempt = review.get("status"), review.get("attempt")
    if status not in ("PASS", "FAIL", "BLOCKED") or attempt != data["next_attempt"]:
        raise ValueError("Statut ou numéro d'examen invalide.")
    if not text(review.get("justification"), 20):
        raise ValueError("Justification réelle requise.")
    files, audits = [], None
    if status != "BLOCKED":
        files.append(evidence(root, data["master"]["path"]))
    if status == "FAIL":
        best = evidence(root, review["best_checkpoint"])
        if best["path"] == data["master"]["path"]:
            raise ValueError("Conserver un checkpoint distinct du maître modifiable.")
        files.append(best)
    if status == "PASS":
        inspection = review.get("inspection", {})
        images = inspection.get("images", [])
        if len(set(images)) < 4 or not text(inspection.get("method")) or not inspection.get("observations"):
            raise ValueError("Quatre vues distinctes réellement inspectées et observations requises.")
        files.extend(png(root, value) for value in images)
        checks = review.get("checks", {})
        if any(not text(checks.get(key)) for key in CHECKS[data["kind"]]):
            raise ValueError("Contrôles documentés manquants pour " + data["kind"])
        if any(d.get("severity") == "major" and not d.get("resolved", False) for d in review.get("defects", [])):
            raise ValueError("Défaut majeur non résolu.")
        files.append(evidence(root, review["reopen_evidence"]))
        reopened = read(inside(root, review["reopen_evidence"]))
        if mcp_failed(reopened):
            raise ValueError("La réouverture Blender a échoué.")
        if data["kind"] == "fdm":
            extra, audits = fdm_review(root, data, review)
            files.extend(extra)
            data["readiness"] = review["readiness"]
    suffix = f"blocked-{len(data['reviews']):03d}" if status == "BLOCKED" else f"attempt-{attempt:02d}"
    saved = manifest.parent / (suffix + ".json")
    payload = {**review, "evidence": files, "validation_scope": "Cohérence documentaire ; inspection visuelle déclarée, non effectuée par ce script."}
    if audits is not None:
        payload["stl_audits"] = audits
    write_new(saved, payload)
    data["reviews"].append(relative(root, saved))
    data["status"] = "FAIL_FINAL" if status == "FAIL" and attempt == 3 else status
    if status != "BLOCKED":
        data["next_attempt"] += 1
    if status == "PASS":
        data["master"] = evidence(root, data["master"]["path"])
        data["evidence"] = files + [evidence(root, relative(root, saved))]
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"status": data["status"], "report": str(saved), "next_attempt": data["next_attempt"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    new = sub.add_parser("new")
    new.add_argument("project", type=Path)
    new.add_argument("--kind", choices=CHECKS, required=True)
    new.add_argument("--label", required=True)
    new.add_argument("--mode", choices=["rigid", "deforming", "hybrid", "static"])
    new.add_argument("--source", required=True)
    new.add_argument("--request", required=True)
    new.add_argument("--upstream")
    review = sub.add_parser("record")
    review.add_argument("manifest", type=Path)
    review.add_argument("--review", type=Path, required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        if args.action == "new":
            result = new_run(args.project, args.kind, args.label, args.mode, args.source, args.request, args.upstream)
        elif args.action == "record":
            result = record(args.manifest, args.review)
        else:
            data = verify(args.manifest)
            result = {"status": data["status"], "readiness": data.get("readiness"),
                      "structural_validation": "PASS", "visual_validation": "déclarée ; non effectuée par ce script"}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("ERREUR : " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
