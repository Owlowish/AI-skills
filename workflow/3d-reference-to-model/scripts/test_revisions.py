#!/usr/bin/env python3
"""Revision contracts using isolated synthetic fixtures; no real visual validation."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest
from unittest import mock
import zlib

import project
import blender_previews as previews
import test_project as fixtures

SYNTHETIC_BLEND = fixtures.SYNTHETIC_BLEND


def synthetic_png(size=128):
    def chunk(kind, payload):
        return struct.pack('!I', len(payload)) + kind + payload + struct.pack('!I', zlib.crc32(kind + payload) & 0xffffffff)
    raw = (b'\x00' + b'\x80\x90\xa0' * size) * size
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', size, size, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')


class TargetedRevisionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ProjectContractTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        for stage in project.STAGES:
            project.record(self.root, self.fixture.review(stage=stage))
        project.write_json(self.root / 'previews/camera-rig.json', {
            'version': 1, 'target': [0, 0, 1.5], 'diameter': 3.5,
            'ortho_scale': 4.4, 'front_axis': '-Y', 'up_axis': '+Z',
        })
        self.original_manifest = (self.root / 'project.yaml').read_bytes()
        self.original_master = (self.root / 'blender/model.blend').read_bytes()

    def data(self):
        return project.read_json(self.root / 'project.yaml')

    def start(self, stage='geometry'):
        return project.revise(self.root, stage, 'SYNTHETIC: improve profile only', ['head'], ['colors', 'marks'], (-1, -0.18, 0.05))

    def capture(self, stage=None, attempt=0, before=False):
        arguments = previews.prepare(self.root, stage, attempt, resolution=128, before=before)
        data = self.data()
        stage = data['revision']['from_stage'] if before else stage
        folder = self.root / project.stage_path('previews', stage, data['revision']['id']) / ('before' if before else f'attempt-{attempt:02d}')
        prepared = project.read_json(folder / 'prepared.json')
        for view in project.capture_views(data['revision']['id']):
            (folder / f'{view}.png').write_bytes(synthetic_png())
        capture = {
            'stage': stage, 'attempt': 0 if before else attempt,
            'rendered': list(project.capture_views(data['revision']['id'])),
            'rig': prepared['rig'], 'resolution': 128, 'engine': 'BLENDER_WORKBENCH',
            'purpose': prepared['purpose'], 'revision_id': prepared['revision_id'],
            'view_specs': prepared['views'], 'neutral_settings': {'fixture': 'same neutral setup'},
            'producer': 'SYNTHETIC ONLY; no Blender render or visual inspection',
        }
        response = arguments.with_name(arguments.stem + '.synthetic-result.json')
        project.write_json(response, {'status': 'PASS', 'content': [{'type': 'text', 'text': 'REFERENCE_TO_3D_CAPTURE=' + json.dumps(capture)}]})
        return previews.finish(self.root, stage, 0 if before else attempt, response, before)

    def review(self, stage='geometry', attempt=0, status='PASS'):
        receipt_path = self.capture(stage, attempt)
        receipt = project.read_json(receipt_path)
        info, before = project.baseline_evidence(self.root, self.data())
        review = {
            'stage': stage, 'attempt': attempt, 'status': status,
            'justification': 'SYNTHETIC revision contract only; no actual quality decision.',
            'inspection': {'method': 'SYNTHETIC; no actual visual inspection',
                           'observations': ['Fixture only'],
                           'inspected_images': [s['path'] for s in self.data()['sources']] + [e['path'] for e in receipt['images'].values()] + [e['path'] for e in before['images'].values()]},
            'corrections': [] if attempt == 0 else ['Synthetic correction'],
            'defects': [], 'remaining_issues': [],
            'comparison': {'outcome': 'improved', 'observations': ['Synthetic before/after observation'],
                           'changes': ['Synthetic profile change'],
                           'preservation_checks': {value: 'Synthetic preserved check' for value in info['preserve']}},
        }
        if stage in {'geometry', 'finalization'}:
            review['geometry_checks'] = {key: 'Synthetic only' for key in project.CHECKS}
        if stage == 'finalization':
            review['scene_check'] = 'Synthetic only; no Blender opened'
            review['export_checks'] = []
        if status == 'FAIL':
            relative = f'blender/checkpoints/{info["id"]}/{stage}-best.blend'
            checkpoint = self.root / relative
            checkpoint.parent.mkdir(parents=True, exist_ok=True)
            checkpoint.write_bytes(SYNTHETIC_BLEND)
            review['best_checkpoint'] = relative
            review['remaining_issues'] = ['Synthetic unresolved issue']
        return review

    def ready(self):
        self.start()
        self.capture(before=True)
        (self.root / 'blender/model.blend').write_bytes(SYNTHETIC_BLEND + b'retouched\n')

    def test_revision_preserves_previous_version_and_reopens_only_suffix(self):
        result = self.start()
        self.assertEqual(result['revision'], 'r001')
        self.assertEqual(result['revalidate'], ['geometry', 'refinement', 'finalization'])
        self.assertEqual(set(self.data()['stages']), {'blockout'})
        self.assertEqual((self.root / result['previous_model']).read_bytes(), self.original_master)
        self.assertEqual((self.root / 'blender/model.blend').read_bytes(), self.original_master)
        self.assertEqual((self.root / 'revisions/r001/project-before.json').read_bytes(), self.original_manifest)
        self.assertTrue((self.root / 'previews/geometry/attempt-00/front.png').is_file())
        self.assertEqual(project.attempts(self.root, 'geometry'), [])
        self.assertEqual(len(project.attempts(self.root, 'blockout')), 1)
        self.assertEqual(project.validate(self.root)['status'], 'IN_PROGRESS')
        with self.assertRaisesRegex(ValueError, 'Jalon non validé'):
            project.validate(self.root, complete=True)

    def test_revision_cannot_reset_an_unfinished_revision_counter(self):
        self.start()
        with self.assertRaisesRegex(ValueError, 'reprendre le cycle actif'):
            self.start()

    def test_before_capture_required_and_must_precede_edits(self):
        self.start()
        with self.assertRaises((ValueError, OSError)):
            previews.prepare(self.root, 'geometry', 0, resolution=128)
        (self.root / 'blender/model.blend').write_bytes(b'SYNTHETIC changed too soon')
        with self.assertRaisesRegex(ValueError, 'avant doit précéder'):
            previews.prepare(self.root, before=True, resolution=128)

    def test_before_capture_sealed_and_cannot_be_overwritten(self):
        self.start()
        path = self.capture(before=True)
        before = path.read_bytes()
        with self.assertRaises(FileExistsError):
            previews.prepare(self.root, before=True, resolution=128)
        self.assertEqual(path.read_bytes(), before)

    def test_unvalidated_current_master_cannot_become_previous_delivery(self):
        (self.root / 'blender/model.blend').write_bytes(SYNTHETIC_BLEND + b'changed after delivery')
        with self.assertRaisesRegex(ValueError, 'modèle final a changé'):
            self.start()
        self.assertFalse((self.root / 'revisions').exists())

    def test_before_focus_image_tampering_is_detected(self):
        self.start()
        path = self.capture(before=True)
        receipt = project.read_json(path)
        (self.root / receipt['images']['focus']['path']).write_bytes(b'altered synthetic focus')
        with self.assertRaisesRegex(ValueError, 'Capture avant modifiée'):
            project.validate(self.root)

    def test_five_views_generated_including_same_focus_direction(self):
        self.start()
        receipt = project.read_json(self.capture(before=True))
        self.assertEqual(set(receipt['images']), {*project.VIEWS, 'focus'})
        self.assertEqual(receipt['view_specs'][-1], ['focus', [-1.0, -0.18, 0.05]])
        project.validate(self.root)

    def test_resolution_and_collection_must_match_before(self):
        self.ready()
        with self.assertRaisesRegex(ValueError, 'même résolution'):
            previews.prepare(self.root, 'geometry', 0, resolution=256)
        with self.assertRaisesRegex(ValueError, 'même résolution'):
            previews.prepare(self.root, 'geometry', 0, resolution=128, collection='OTHER')

    def test_comparison_observations_and_preservation_checks_required(self):
        self.ready()
        review = self.review()
        missing = copy.deepcopy(review)
        missing.pop('comparison')
        with self.assertRaisesRegex(ValueError, 'avant/après'):
            project.record(self.root, missing)
        missing = copy.deepcopy(review)
        del missing['comparison']['preservation_checks']['marks']
        with self.assertRaisesRegex(ValueError, 'préservation'):
            project.record(self.root, missing)

    def test_regression_forbids_pass(self):
        self.ready()
        review = self.review()
        review['comparison']['outcome'] = 'regressed'
        with self.assertRaisesRegex(ValueError, 'régression'):
            project.record(self.root, review)

    def test_before_images_must_be_inspected(self):
        self.ready()
        review = self.review()
        review['inspection']['inspected_images'] = [p for p in review['inspection']['inspected_images'] if '/before/' not in p]
        with self.assertRaisesRegex(ValueError, 'avant doivent'):
            project.record(self.root, review)

    def test_camera_or_lighting_change_refuses_comparison(self):
        self.ready()
        review = self.review()
        path = self.root / 'previews/geometry/r001/attempt-00/capture.json'
        receipt = project.read_json(path)
        receipt['neutral_settings'] = {'fixture': 'different lighting'}
        project.write_json(path, receipt)
        with self.assertRaisesRegex(ValueError, 'Avant/après incompatible'):
            project.record(self.root, review)

    def test_previous_capture_cannot_be_reused_as_after(self):
        self.ready()
        review = self.review()
        path = self.root / 'previews/geometry/r001/attempt-00/capture.json'
        receipt = project.read_json(path)
        receipt['images']['side']['path'] = 'previews/geometry/attempt-00/side.png'
        project.write_json(path, receipt)
        with self.assertRaisesRegex(ValueError, 'chemin incohérent'):
            project.record(self.root, review)

    def test_old_artifacts_and_previous_master_are_protected(self):
        result = self.start()
        target = self.root / 'reports/finalization/attempt-00.json'
        original = target.read_bytes()
        target.write_bytes(b'changed old report')
        with self.assertRaisesRegex(ValueError, 'Historique protégé'):
            project.validate(self.root)
        target.write_bytes(original)
        (self.root / result['previous_model']).write_bytes(b'changed previous model')
        with self.assertRaisesRegex(ValueError, 'Version précédente'):
            project.validate(self.root)

    def test_unchanged_prior_exports_cannot_count_as_new_revision_exports(self):
        self.ready()
        for stage in ('geometry', 'refinement'):
            project.record(self.root, self.review(stage))
        manifest = self.data()
        manifest['requested_exports'] = ['glb']
        project.write_json(self.root / 'project.yaml', manifest)
        old = self.root / 'exports/old.glb'
        old.parent.mkdir()
        old.write_bytes(b'SYNTHETIC export')
        review = self.review('finalization')
        review['export_checks'] = [{'path': 'exports/old.glb', 'method': 'Synthetic', 'status': 'PASS'}]
        with self.assertRaises(ValueError):
            project.record(self.root, review)

    def test_three_corrections_still_limit_current_revision(self):
        self.ready()
        for attempt in range(4):
            project.record(self.root, self.review(attempt=attempt, status='FAIL'))
        self.assertEqual(self.data()['status'], 'BLOCKED')
        with self.assertRaisesRegex(ValueError, 'corrections'):
            project.record(self.root, self.review(attempt=4, status='FAIL'))
        with self.assertRaisesRegex(ValueError, 'cycle actif'):
            self.start()

    def test_complete_revision_and_second_revision_keep_mixed_stage_history(self):
        self.ready()
        for stage in ('geometry', 'refinement', 'finalization'):
            report = project.record(self.root, self.review(stage))
            markdown = report.with_suffix('.md').read_text(encoding='utf-8')
            self.assertIn('![Avant]', markdown)
            self.assertIn('![Après]', markdown)
            self.assertIn('/r001/before/focus.png', markdown)
        self.assertEqual(project.validate(self.root, complete=True)['status'], 'COMPLETE')
        first_version = (self.root / 'blender/model.blend').read_bytes()
        result = self.start('refinement')
        self.assertEqual(result['revision'], 'r002')
        self.assertEqual(self.data()['stages']['geometry']['revision_id'], 'r001')
        self.assertNotIn('revision_id', self.data()['stages']['blockout'])
        self.assertEqual((self.root / result['previous_model']).read_bytes(), first_version)
        self.assertEqual(len(self.data()['revision_history']), 1)
        self.assertEqual(project.validate(self.root)['status'], 'IN_PROGRESS')

    def test_start_failure_leaves_current_delivery_untouched(self):
        real_write = project.write_json
        def fail_manifest(path, data):
            if Path(path) == self.root / 'project.yaml':
                raise OSError('Synthetic commit failure')
            return real_write(path, data)
        with mock.patch.object(project, 'write_json', side_effect=fail_manifest):
            with self.assertRaises(OSError):
                self.start()
        self.assertEqual((self.root / 'project.yaml').read_bytes(), self.original_manifest)
        self.assertEqual((self.root / 'blender/model.blend').read_bytes(), self.original_master)
        self.assertFalse((self.root / 'blender/model-before-r001.blend').exists())
        project.validate(self.root, complete=True)

    def test_invalid_direction_refused_without_creating_revision(self):
        for direction in ((0,0,0),(float('nan'),0,0),(float('inf'),1,0)):
            with self.assertRaises(ValueError):
                project.revise(self.root, 'geometry', 'Synthetic', view_direction=direction)
        self.assertFalse((self.root / 'revisions').exists())

    def test_cli_revision_preserves_master(self):
        result = subprocess.run([sys.executable, str(Path(project.__file__)), 'revise', str(self.root), '--from-stage', 'finalization', '--request', 'SYNTHETIC lighting change'], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['revalidate'], ['finalization'])
        self.assertEqual((self.root / 'blender/model.blend').read_bytes(), self.original_master)

    def test_old_initial_capture_payload_remains_finishable(self):
        folder = self.root / 'previews/refinement/attempt-01'
        folder.mkdir()
        rig = project.read_json(self.root / 'previews/camera-rig.json')
        prepared = {'stage': 'refinement', 'attempt': 1, 'blend_sha256': project.sha256(self.root / 'blender/model.blend'),
                    'collection': 'MODEL', 'resolution': 128, 'rig': rig}
        project.write_json(folder / 'prepared.json', prepared)
        for view in project.VIEWS:
            (folder / f'{view}.png').write_bytes(synthetic_png())
        old_payload = {'stage': 'refinement', 'attempt': 1, 'rendered': list(project.VIEWS),
                       'rig': rig, 'resolution': 128, 'engine': 'BLENDER_WORKBENCH'}
        result = folder / 'synthetic-old-result.json'
        project.write_json(result, {'content': [{'type': 'text', 'text': 'REFERENCE_TO_3D_CAPTURE='+json.dumps(old_payload)}]})
        receipt = previews.finish(self.root, 'refinement', 1, result)
        self.assertEqual(set(project.read_json(receipt)['images']), set(project.VIEWS))
        self.assertEqual((self.root / 'blender/model.blend').read_bytes(), self.original_master)


if __name__ == '__main__':
    unittest.main(verbosity=2)
