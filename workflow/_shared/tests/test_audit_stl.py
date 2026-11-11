import math
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_stl import audit_stl
from _fixtures import cube, stl


class StlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "synthetic.stl"

    def test_binary_dimensions_and_closed_volume(self):
        data = audit_stl(stl(self.path), [1,2,3])
        self.assertEqual(data["status"], "PASS")
        self.assertAlmostEqual(data["signed_volume_mm3"], 6)
        self.assertEqual(data["surface_components"], 1)

    def test_ascii(self):
        self.assertEqual(audit_stl(stl(self.path, ascii=True))["status"], "PASS")

    def test_open_surface(self):
        data = audit_stl(stl(self.path, cube()[:-1]))
        self.assertEqual(data["status"], "FAIL")
        self.assertGreater(data["boundary_edges"], 0)

    def test_reversed_volume(self):
        data = audit_stl(stl(self.path, cube(reverse=True)))
        self.assertEqual(data["status"], "FAIL")
        self.assertLess(data["signed_volume_mm3"], 0)

    def test_inconsistent_orientation(self):
        triangles = cube();triangles[0] = tuple(reversed(triangles[0]))
        self.assertGreater(audit_stl(stl(self.path, triangles))["orientation_errors"], 0)

    def test_duplicate_and_degenerate_faces(self):
        triangles = cube();triangles += [triangles[0], ((0,0,0),)*3]
        data = audit_stl(stl(self.path, triangles))
        self.assertGreater(data["duplicate_triangles"], 0)
        self.assertGreater(data["degenerate_triangles"], 0)

    def test_wrong_scale_is_rejected(self):
        data = audit_stl(stl(self.path), [1000,2000,3000])
        self.assertEqual(data["status"], "FAIL")

    def test_nan_is_rejected(self):
        triangles = cube();triangles[0] = ((math.nan,0,0),triangles[0][1],triangles[0][2])
        with self.assertRaises(ValueError):
            audit_stl(stl(self.path, triangles))

    def test_truncated_binary(self):
        stl(self.path);self.path.write_bytes(self.path.read_bytes()[:-3])
        with self.assertRaises(ValueError):
            audit_stl(self.path)

    def test_empty_stl(self):
        with self.assertRaises(ValueError):
            audit_stl(stl(self.path, []))

    def test_multiple_surfaces_require_explicit_examination(self):
        stl(self.path, cube() + cube(offset=(10,0,0)))
        self.assertEqual(audit_stl(self.path)["status"], "FAIL")
        self.assertEqual(audit_stl(self.path, allow_multiple_shells=True)["surface_components"], 2)

    def test_closed_internal_cavity_can_be_documented(self):
        triangles = cube((4,4,4)) + cube((1,1,1), offset=(1,1,1), reverse=True)
        data = audit_stl(stl(self.path, triangles), allow_multiple_shells=True)
        self.assertEqual(data["status"], "PASS")
        self.assertAlmostEqual(data["signed_volume_mm3"], 63)


if __name__ == "__main__":
    unittest.main()
