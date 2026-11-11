"""Tests SYNTHETIC des invariants ; aucun Blender ni examen visuel réel."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import derived_workflow as flow
from _fixtures import cube, stl, png, write_json


class DerivedWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "project.yaml").write_text("synthetic: true\n", encoding="utf-8")
        (self.root / "blender").mkdir()
        (self.root / "blender/model.blend").write_bytes(b"SYNTHETIC source, not a real blend")
        self.base = patch.object(flow, "validate_base")
        self.base.start()
        self.addCleanup(self.base.stop)

    def rel(self, path):
        return flow.relative(self.root, path)

    def new(self, kind="rig", label="principal", mode="rigid", source="blender/model.blend", upstream=None):
        return Path(flow.new_run(self.root, kind, label, mode, source,
                                "SYNTHETIC request, no real modelling", upstream)["manifest"])

    def data(self, path):
        return flow.read(path)

    def review(self, manifest, status="PASS", attempt=0):
        data = self.data(manifest)
        master = self.root / data["master"]["path"]
        master.write_bytes(b"SYNTHETIC derivative, not a real blend")
        result = {"status": status, "attempt": attempt,
                  "justification": "SYNTHETIC fixture used only to test the manifest contract."}
        if status == "PASS":
            images = []
            for name in ["front", "side", "back", "three-quarter"]:
                path = self.root / data["previews"] / (name + ".png")
                png(path)
                images.append(self.rel(path))
            reopened = manifest.parent / "reopen.json"
            write_json(reopened, {"isError": False, "content": [
                {"type": "text", "text": "SYNTHETIC reopening response, no Blender used."}]})
            result.update(inspection={
                "method": "SYNTHETIC fixture, no real visual inspection.",
                "images": images, "observations": ["SYNTHETIC observation for contract only."]},
                checks={key: "SYNTHETIC check for automated contract testing only."
                        for key in flow.CHECKS[data["kind"]]},
                reopen_evidence=self.rel(reopened), remaining_issues=[])
        if status == "FAIL":
            checkpoint = manifest.parent / ("best-" + str(attempt) + ".blend")
            checkpoint.write_bytes(b"SYNTHETIC best checkpoint")
            result["best_checkpoint"] = self.rel(checkpoint)
        return result

    def save_review(self, manifest, review):
        path = manifest.parent / "review-input.json"
        write_json(path, review)
        return flow.record(manifest, path)

    def passed_rig(self):
        manifest = self.new()
        self.save_review(manifest, self.review(manifest))
        return manifest

    def fdm(self):
        manifest = self.new(kind="fdm", mode="static")
        data = self.data(manifest)
        review = self.review(manifest)
        export = self.root / data["exports"] / "piece.stl"
        stl(export)
        reimport = manifest.parent / "reimport.json"
        write_json(reimport, {"content": [
            {"type": "text", "text": "SYNTHETIC reimport response, no Blender used."}]})
        review.update(
            readiness="GEOMETRY_PREPARED",
            print_profile={"machine": "Bambu Lab A1 mini",
                           "nominal_volume_mm": [180,180,180], "usable_volume_mm": [170,170,175],
                           "nozzle_mm": .4, "filament": "PLA"},
            dimensions_mm={"figure": [1,2,3], "with_base": [1,2,3]},
            exports=[{"path": self.rel(export), "dimensions_mm": [1,2,3],
                      "reimport_evidence": self.rel(reimport)}])
        return manifest, review

    def test_new_run_reserves_paths_without_creating_a_fake_model(self):
        source = self.root / "blender/model.blend"
        original = source.read_bytes()
        manifest = self.new()
        self.assertFalse((self.root / self.data(manifest)["master"]["path"]).exists())
        self.assertEqual(source.read_bytes(), original)
        self.assertEqual(self.data(manifest)["status"], "DRAFT")

    def test_path_escape_and_invalid_slug_are_rejected(self):
        with self.assertRaises(ValueError):
            self.new(label="../escape")
        with self.assertRaises(ValueError):
            self.new(source="../outside.blend")

    def test_static_object_does_not_require_a_rig(self):
        manifest = self.new(kind="pose", mode="static")
        self.save_review(manifest, self.review(manifest))
        self.assertEqual(flow.verify(manifest)["status"], "PASS")
        with self.assertRaises(ValueError):
            self.new(kind="rig", label="static", mode="static")

    def test_articulated_pose_requires_an_approved_rig(self):
        with self.assertRaises(ValueError):
            self.new(kind="pose", mode="rigid")

    def test_rig_pose_fdm_provenance_chain(self):
        rig = self.passed_rig()
        pose = self.new(kind="pose", source=self.data(rig)["master"]["path"], upstream=self.rel(rig))
        self.save_review(pose, self.review(pose))
        fdm = self.new(kind="fdm", source=self.data(pose)["master"]["path"], upstream=self.rel(pose))
        self.assertEqual(self.data(fdm)["upstream"]["sha256"], flow.sha(pose))
        self.assertEqual(flow.verify(pose)["mode"], "rigid")

    def test_incompatible_upstream_is_rejected(self):
        rig = self.passed_rig()
        with self.assertRaises(ValueError):
            self.new(kind="fdm", source=self.data(rig)["master"]["path"], upstream=self.rel(rig))

    def test_upstream_and_source_hashes_are_checked(self):
        rig = self.passed_rig()
        pose = self.new(kind="pose", source=self.data(rig)["master"]["path"], upstream=self.rel(rig))
        (self.root / self.data(rig)["master"]["path"]).write_bytes(b"changed")
        with self.assertRaises(ValueError):
            flow.verify(pose, require_pass=False)

    def test_upstream_manifest_changes_invalidate_descendant(self):
        rig = self.passed_rig()
        pose = self.new(kind="pose", source=self.data(rig)["master"]["path"], upstream=self.rel(rig))
        rig.write_text(rig.read_text(encoding="utf-8") + " ", encoding="utf-8")
        with self.assertRaises(ValueError):
            flow.verify(pose, require_pass=False)

    def test_source_change_invalidates_run(self):
        manifest = self.new()
        (self.root / "blender/model.blend").write_bytes(b"changed")
        with self.assertRaises(ValueError):
            flow.verify(manifest, require_pass=False)

    def test_pass_seals_review_and_evidence(self):
        manifest = self.new()
        review = self.review(manifest)
        self.save_review(manifest, review)
        sealed = manifest.parent / "attempt-00.json"
        self.assertTrue(sealed.is_file())
        self.assertIn("non effectuée", self.data(sealed)["validation_scope"])
        with self.assertRaises(ValueError):
            self.save_review(manifest, review)
        (self.root / review["inspection"]["images"][0]).write_bytes(b"changed")
        with self.assertRaises(ValueError):
            flow.verify(manifest)

    def test_pass_requires_four_views_and_all_checks(self):
        manifest = self.new()
        review = self.review(manifest)
        review["inspection"]["images"] = review["inspection"]["images"][:3]
        with self.assertRaises(ValueError):
            self.save_review(manifest, review)
        review = self.review(manifest)
        review["checks"]["bindings"] = "OK"
        with self.assertRaises(ValueError):
            self.save_review(manifest, review)

    def test_pass_rejects_unresolved_major_defect(self):
        manifest = self.new()
        review = self.review(manifest)
        review["defects"] = [{"severity": "major", "resolved": False}]
        with self.assertRaises(ValueError):
            self.save_review(manifest, review)

    def test_mcp_content_error_is_not_a_successful_reopen(self):
        manifest = self.new()
        review = self.review(manifest)
        write_json(self.root / review["reopen_evidence"],
                   {"isError": False, "content": [{"type": "text", "text": "Could not connect to Blender"}]})
        with self.assertRaises(ValueError):
            self.save_review(manifest, review)

    def test_blocked_preserves_correction_budget(self):
        manifest = self.new()
        self.save_review(manifest, self.review(manifest, "BLOCKED"))
        self.assertEqual(self.data(manifest)["next_attempt"], 0)
        self.save_review(manifest, self.review(manifest))
        self.assertEqual(flow.verify(manifest)["status"], "PASS")

    def test_empty_or_malformed_mcp_response_is_not_evidence(self):
        for response in [{}, {"isError": False}, {"structuredContent": None, "content": []}]:
            with self.subTest(response=response):
                self.assertTrue(flow.mcp_failed(response))
        manifest = self.new()
        review = self.review(manifest)
        write_json(self.root / review["reopen_evidence"], {})
        with self.assertRaises(ValueError):
            self.save_review(manifest, review)

    def test_four_failures_end_run_and_cannot_reset_budget(self):
        manifest = self.new()
        for attempt in range(4):
            self.save_review(manifest, self.review(manifest, "FAIL", attempt))
        self.assertEqual(self.data(manifest)["status"], "FAIL_FINAL")
        with self.assertRaises(ValueError):
            self.save_review(manifest, self.review(manifest, "FAIL", 4))
        with self.assertRaises(ValueError):
            self.new()

    def test_fail_requires_separate_best_checkpoint(self):
        manifest = self.new()
        review = self.review(manifest, "FAIL")
        review["best_checkpoint"] = self.data(manifest)["master"]["path"]
        with self.assertRaises(ValueError):
            self.save_review(manifest, review)

    def test_finished_pass_creates_a_new_revision(self):
        manifest = self.passed_rig()
        following = self.new()
        self.assertEqual(self.data(following)["revision"], "r002")
        self.assertTrue(manifest.is_file())

    def test_fdm_prepared_geometry_does_not_claim_slicing(self):
        manifest, review = self.fdm()
        self.save_review(manifest, review)
        self.assertEqual(flow.verify(manifest)["readiness"], "GEOMETRY_PREPARED")
        audits = self.data(manifest.parent / "attempt-00.json")["stl_audits"]
        self.assertEqual(audits[0]["dimensions_mm"], [1,2,3])

    def test_slicer_verified_requires_saved_preview_evidence(self):
        manifest, review = self.fdm()
        review["readiness"] = "SLICER_VERIFIED"
        with self.assertRaises((ValueError, KeyError)):
            self.save_review(manifest, review)
        report = manifest.parent / "slicer.txt"
        report.write_text("SYNTHETIC slicer evidence, no slicing performed", encoding="utf-8")
        image = manifest.parent / "slicer.png"
        png(image)
        review.update(slicer_evidence=self.rel(report), slicer_images=[self.rel(image)])
        self.save_review(manifest, review)
        self.assertEqual(flow.verify(manifest)["readiness"], "SLICER_VERIFIED")

    def test_wrong_units_or_oversized_parts_are_rejected(self):
        manifest, review = self.fdm()
        wrong = deepcopy(review)
        wrong["exports"][0]["dimensions_mm"] = [1000,2000,3000]
        with self.assertRaises(ValueError):
            self.save_review(manifest, wrong)
        review["print_profile"]["usable_volume_mm"] = [.5,.5,.5]
        with self.assertRaises(ValueError):
            self.save_review(manifest, review)

    def test_a1_mini_nominal_size_cannot_be_invented(self):
        manifest, review = self.fdm()
        review["print_profile"]["nominal_volume_mm"] = [256,256,256]
        with self.assertRaises(ValueError):
            self.save_review(manifest, review)

    def test_unlisted_stl_and_open_surface_are_rejected(self):
        manifest, review = self.fdm()
        export = self.root / self.data(manifest)["exports"]
        extra = stl(export / "extra.stl")
        with self.assertRaises(ValueError):
            self.save_review(manifest, review)
        extra.unlink()
        stl(self.root / review["exports"][0]["path"], cube()[:-1])
        with self.assertRaises(ValueError):
            self.save_review(manifest, review)

    def test_failed_reimport_is_rejected(self):
        manifest, review = self.fdm()
        write_json(self.root / review["exports"][0]["reimport_evidence"], {"isError": True})
        with self.assertRaises(ValueError):
            self.save_review(manifest, review)

    def test_multiple_surface_exception_requires_reason(self):
        manifest, review = self.fdm()
        stl(self.root / review["exports"][0]["path"],
            cube() + cube(offset=(5,0,0)))
        part = review["exports"][0]
        part["dimensions_mm"] = [6,2,3]
        part["allow_multiple_shells"] = True
        with self.assertRaises(ValueError):
            self.save_review(manifest, review)
        part["shells_justification"] = "SYNTHETIC exception only; no physical connection is attested by this test."
        self.save_review(manifest, review)
        self.assertEqual(flow.verify(manifest)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
