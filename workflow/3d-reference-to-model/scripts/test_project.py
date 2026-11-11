#!/usr/bin/env python3
"""Contract tests with synthetic fixtures, outside the repository.

No Blender model is produced, rendered, inspected or quality-validated here.
PASS/FAIL declarations below are deliberately synthetic test inputs only.
"""
from __future__ import annotations

import base64
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("project.py")
SPEC = importlib.util.spec_from_file_location("reference_to_3d_project", SCRIPT)
project = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(project)

# A one-pixel PNG is only a file-integrity fixture, never a rendered preview.
SYNTHETIC_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/WZ0AAAAASUVORK5CYII="
)
SYNTHETIC_BLEND = b"SYNTHETIC UNIT TEST ONLY; not a valid Blender file\n"


class ProjectContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="3d-reference-to-model-synthetic-test-")
        self.addCleanup(self.temporary.cleanup)
        self.sandbox = Path(self.temporary.name).resolve()
        self.repo = self.sandbox / "workspace"
        self.repo.mkdir()
        self.source = self.sandbox / "synthetic-reference.png"
        self.source.write_bytes(SYNTHETIC_PNG)
        self.root = project.new_project(self.repo, "synthetic-model", [self.source], "hybrid")

    def manifest(self):
        return project.read_json(self.root / "project.yaml")

    def master(self):
        path = self.root / "blender/model.blend"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(SYNTHETIC_BLEND)
        return path

    def evidence(self, stage="blockout", attempt=0):
        master = self.master()
        folder = self.root / "previews" / stage / f"attempt-{attempt:02d}"
        folder.mkdir(parents=True, exist_ok=True)
        images = {}
        for view in project.VIEWS:
            image = folder / f"{view}.png"
            image.write_bytes(SYNTHETIC_PNG)
            images[view] = {
                "path": image.relative_to(self.root).as_posix(),
                "sha256": project.sha256(image),
            }
        receipt = {
            "stage": stage,
            "attempt": attempt,
            "blend_sha256": project.sha256(master),
            "images": images,
            "producer": "SYNTHETIC UNIT TEST FIXTURE; not Blender",
        }
        project.write_json(folder / "capture.json", receipt)
        return receipt

    def review(self, stage="blockout", attempt=0, status="PASS", capture=True):
        receipt = self.evidence(stage, attempt) if capture else None
        source_paths = [entry["path"] for entry in self.manifest()["sources"]]
        image_paths = [entry["path"] for entry in receipt["images"].values()] if receipt else []
        review = {
            "stage": stage,
            "attempt": attempt,
            "status": status,
            "justification": "Synthetic contract-test declaration only; no model quality claim.",
            "inspection": {
                "method": "SYNTHETIC FIXTURE; no actual visual inspection",
                "observations": ["Synthetic evidence exercises the file contract only."],
                "inspected_images": source_paths + image_paths,
            },
            "corrections": [] if attempt == 0 else [f"Synthetic correction batch {attempt}."],
            "defects": [],
            "remaining_issues": [],
        }
        if status == "FAIL":
            checkpoint = self.root / f"blender/checkpoints/{stage}-best.blend"
            checkpoint.parent.mkdir(parents=True, exist_ok=True)
            if not checkpoint.exists():
                checkpoint.write_bytes(SYNTHETIC_BLEND + b"best synthetic fixture\n")
            review["best_checkpoint"] = checkpoint.relative_to(self.root).as_posix()
            review["remaining_issues"] = ["Synthetic unresolved issue for the contract test."]
        if stage in {"geometry", "finalization"}:
            review["geometry_checks"] = {name: "Synthetic check only." for name in project.CHECKS}
        if stage == "finalization":
            review["scene_check"] = "Synthetic check only; Blender was not run."
            review["export_checks"] = []
        return review

    def test_creation_copies_sources_and_preserves_hashes(self):
        data = self.manifest()
        self.assertEqual(data["id"], "synthetic-model")
        self.assertEqual(data["status"], "READY")
        copied = self.root / data["sources"][0]["path"]
        self.assertNotEqual(copied, self.source)
        self.assertEqual(copied.read_bytes(), self.source.read_bytes())
        self.assertEqual(data["sources"][0]["sha256"], project.sha256(self.source))
        self.assertEqual(project.validate(self.root)["structural_validation"], "PASS")

    def test_creation_has_no_outputs_at_repository_root(self):
        self.assertEqual({p.name for p in self.repo.iterdir()}, {"projects"})
        relative_files = {p.relative_to(self.root).as_posix() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(relative_files, {"project.yaml", "references/source/synthetic-reference.png"})

    def test_creation_rejects_existing_project_without_overwrite(self):
        before = (self.root / "project.yaml").read_bytes()
        with self.assertRaises(FileExistsError):
            project.new_project(self.repo, "synthetic-model", [self.source])
        self.assertEqual((self.root / "project.yaml").read_bytes(), before)

    def test_creation_rejects_traversal_and_windows_reserved_names(self):
        for slug in ("../escape", "a/b", "a\\b", "con", "prn", "aux", "nul", "com1", "lpt9", "UPPER", "bad--slug"):
            with self.subTest(slug=slug), self.assertRaises(ValueError):
                project.new_project(self.repo, slug, [self.source])
        self.assertEqual({p.name for p in (self.repo / "projects").iterdir()}, {"synthetic-model"})

    def test_creation_requires_reference_and_distinct_source_names(self):
        with self.assertRaises(ValueError):
            project.new_project(self.repo, "no-source", [])
        other = self.sandbox / "other" / self.source.name
        other.parent.mkdir()
        other.write_bytes(SYNTHETIC_PNG)
        with self.assertRaises(ValueError):
            project.new_project(self.repo, "duplicate-source", [self.source, other])
        self.assertFalse((self.repo / "projects/no-source").exists())
        self.assertFalse((self.repo / "projects/duplicate-source").exists())

    def test_source_changes_are_rejected(self):
        copied = self.root / self.manifest()["sources"][0]["path"]
        copied.write_bytes(b"SYNTHETIC ALTERED SOURCE")
        with self.assertRaisesRegex(ValueError, "source modifiée"):
            project.validate(self.root)
        self.assertEqual(self.source.read_bytes(), SYNTHETIC_PNG)

    def test_blocked_needs_no_fake_inspection_and_consumes_no_correction(self):
        blocked = {"stage": "blockout", "attempt": 0, "status": "BLOCKED", "justification": "Synthetic missing visual tool."}
        report = project.record(self.root, blocked)
        self.assertEqual(report.name, "blocked.json")
        self.assertNotIn("inspection", project.read_json(report))
        self.assertEqual(project.attempts(self.root, "blockout"), [])
        self.assertEqual(self.manifest()["status"], "BLOCKED")
        project.validate(self.root)
        project.record(self.root, self.review(status="FAIL"))
        self.assertEqual(len(project.attempts(self.root, "blockout")), 1)
        self.assertEqual(self.manifest()["stages"]["blockout"]["attempt"], 0)
        blocked["attempt"] = 1
        project.record(self.root, blocked)
        self.assertEqual(len(project.attempts(self.root, "blockout")), 1)
        project.record(self.root, self.review(attempt=1, status="FAIL"))
        self.assertEqual(len(project.attempts(self.root, "blockout")), 2)

    def test_pass_without_captures_is_rejected(self):
        with self.assertRaises((ValueError, OSError)):
            project.record(self.root, self.review(capture=False))
        self.assertEqual(project.attempts(self.root, "blockout"), [])

    def test_pass_with_missing_view_is_rejected(self):
        review = self.review()
        receipt_path = self.root / "previews/blockout/attempt-00/capture.json"
        receipt = project.read_json(receipt_path)
        del receipt["images"]["back"]
        project.write_json(receipt_path, receipt)
        with self.assertRaisesRegex(ValueError, "Quatre vues"):
            project.record(self.root, review)

    def test_pass_without_actual_inspection_fields_is_rejected(self):
        for field in ("method", "observations", "inspected_images"):
            with self.subTest(field=field):
                review = self.review()
                review["inspection"].pop(field)
                with self.assertRaises(ValueError):
                    project.record(self.root, review)

    def test_pass_with_unresolved_major_defect_is_rejected(self):
        review = self.review()
        review["defects"] = [{"category": "silhouette", "severity": "major", "resolved": False, "description": "Synthetic major defect."}]
        with self.assertRaisesRegex(ValueError, "défaut majeur"):
            project.record(self.root, review)

    def test_geometry_before_blockout_pass_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "blockout doit être PASS"):
            project.record(self.root, self.review(stage="geometry"))

    def test_initial_plus_three_corrections_preserves_best_and_stops(self):
        best = None
        original_best = None
        for attempt in range(4):
            review = self.review(attempt=attempt, status="FAIL")
            best = self.root / review["best_checkpoint"]
            if original_best is None:
                original_best = best.read_bytes()
            project.record(self.root, review)
        self.assertEqual(len(project.attempts(self.root, "blockout")), 4)
        self.assertEqual(self.manifest()["status"], "BLOCKED")
        self.assertEqual(best.read_bytes(), original_best)
        with self.assertRaisesRegex(ValueError, "Limite de corrections"):
            project.record(self.root, self.review(attempt=4, status="FAIL"))
        with self.assertRaisesRegex(ValueError, "blockout doit être PASS"):
            project.record(self.root, self.review(stage="geometry"))
        self.assertEqual(best.read_bytes(), original_best)
        project.validate(self.root)

    def test_fail_without_best_checkpoint_is_rejected(self):
        review = self.review(status="FAIL")
        del review["best_checkpoint"]
        with self.assertRaisesRegex(ValueError, "checkpoint"):
            project.record(self.root, review)

    def test_record_cannot_overwrite_prior_attempt(self):
        review = self.review(status="FAIL")
        report = project.record(self.root, review)
        original = report.read_bytes()
        replacement = copy.deepcopy(review)
        replacement["justification"] = "Synthetic attempted overwrite."
        with self.assertRaises(ValueError):
            project.record(self.root, replacement)
        self.assertEqual(report.read_bytes(), original)

    def test_altered_capture_is_rejected(self):
        project.record(self.root, self.review())
        (self.root / "previews/blockout/attempt-00/front.png").write_bytes(b"SYNTHETIC ALTERED CAPTURE")
        with self.assertRaisesRegex(ValueError, "Capture modifiée"):
            project.validate(self.root)

    def test_stale_blend_is_rejected_before_recording_review(self):
        review = self.review()
        self.master().write_bytes(SYNTHETIC_BLEND + b"modified after capture\n")
        with self.assertRaisesRegex(ValueError, "changé depuis les captures"):
            project.record(self.root, review)

    def test_complete_refuses_incomplete_project_through_cli(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "validate", str(self.root), "--complete"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Jalon non", result.stderr)

    def test_synthetic_complete_lifecycle_and_final_blend_integrity(self):
        for stage in project.STAGES:
            project.record(self.root, self.review(stage=stage))
        result = project.validate(self.root, complete=True)
        self.assertEqual(result["status"], "COMPLETE")
        self.assertIn("non effectuée", result["visual_validation"])
        self.master().write_bytes(SYNTHETIC_BLEND + b"changed after finalization\n")
        with self.assertRaisesRegex(ValueError, "modèle final a changé"):
            project.validate(self.root, complete=True)

    def test_progression_refuses_corrupted_prior_gate_evidence(self):
        project.record(self.root, self.review())
        (self.root / "previews/blockout/attempt-00/front.png").write_bytes(b"SYNTHETIC ALTERED CAPTURE")
        with self.assertRaisesRegex(ValueError, "Capture modifiée"):
            project.record(self.root, self.review(stage="geometry"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
