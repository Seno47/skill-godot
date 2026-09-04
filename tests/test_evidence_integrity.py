"""Adversarial admissibility tests, not visual-quality forward evaluations."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from evidence_integrity import sha256, decode_media, validate_gate_integrity
from forward_eval_audit import audit
from tests.test_auditors import write_mjpeg_avi, load_eval_evidence, bind_synthetic_fixture


class EvidenceIntegrityTests(unittest.TestCase):
    def setUp(self):
        from PIL import Image
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.candidate = self.root / 'candidate.json'
        self.candidate.write_text('{"test":"candidate-A"}', encoding='utf-8')
        self.image = self.root / 'screen.png'
        Image.new('RGB', (100, 60), (50, 100, 80)).save(self.image)
        self.metadata = {'builder_context':'builder-1', 'candidate':{'build_id':'A','path':str(self.candidate),'sha256':sha256(self.candidate)}}
        self.gate_id = 'cross_surface_production_craft_review'
        self.gate = {'build_id':'A','candidate_sha256':sha256(self.candidate),
                     'reviewer':{'role':'independent','context':'reviewer-2'},
                     'artifacts':[{'path':str(self.image),'kind':'image','sha256':sha256(self.image),'states':['main_menu']}]}
        self.receipt = {'schema_version':1,'build_id':'A','candidate_sha256':sha256(self.candidate),
                        'reviewer_context':'reviewer-2','source_context':'reviewer-2','source_message':'test-response-7',
                        'gates':{self.gate_id:{'verdict':'pass','blockers':[],
                         'observations':['Synthetic admission case; not an aesthetic claim.'],
                         'first_read_before_intent':True,'first_read_observations':['Synthetic first read.'],
                         'artifacts':{sha256(self.image):['main_menu']}}}}
        self.save_receipt()

    def save_receipt(self):
        path = self.root / 'receipt.json'
        path.write_text(json.dumps(self.receipt), encoding='utf-8')
        self.gate['reviewer']['receipt'] = {'path':str(path),'sha256':sha256(path)}

    def errors(self):
        return validate_gate_integrity(self.gate_id,self.gate,'independent',self.metadata,self.root)

    def test_bound_decoded_media_and_matching_receipt_pass(self):
        self.assertEqual(self.errors(), [])

    def test_text_with_png_extension_fails_even_with_current_hash(self):
        self.image.write_text('not an image', encoding='utf-8')
        self.gate['artifacts'][0]['sha256'] = sha256(self.image)
        self.assertTrue(any('invalid artifact' in e for e in self.errors()))

    def test_stale_capture_fails(self):
        self.image.write_bytes(self.image.read_bytes()+b'changed')
        self.assertTrue(any('SHA-256 mismatch' in e for e in self.errors()))

    def test_stale_candidate_dependency_manifest_fails(self):
        self.candidate.write_text('{"test":"nested-resource-changed"}', encoding='utf-8')
        self.assertTrue(any('SHA-256 mismatch' in e for e in self.errors()))

    def test_rebinding_candidate_does_not_renew_old_review(self):
        self.candidate.write_text('{"test":"candidate-B"}', encoding='utf-8')
        self.metadata['candidate']['sha256'] = sha256(self.candidate)
        self.gate['candidate_sha256'] = sha256(self.candidate)
        self.assertTrue(any('another candidate' in e for e in self.errors()))

    def test_role_string_alone_cannot_pass(self):
        del self.gate['reviewer']['receipt']
        self.assertTrue(self.errors())

    def test_builder_cannot_review_itself(self):
        self.metadata['builder_context'] = 'reviewer-2'
        self.assertTrue(any('distinct' in e for e in self.errors()))

    def test_report_pass_cannot_overwrite_receipt_fail(self):
        self.receipt['gates'][self.gate_id]['verdict'] = 'fail'
        self.save_receipt()
        self.assertTrue(any('does not award PASS' in e for e in self.errors()))

    def test_state_relabel_requires_review(self):
        self.gate['artifacts'][0]['states'].append('pause')
        self.assertTrue(any('all cited' in e for e in self.errors()))

    def test_blind_observations_cannot_be_omitted(self):
        self.receipt['gates'][self.gate_id]['first_read_observations'] = []
        self.save_receipt()
        self.assertTrue(any('first-read' in e for e in self.errors()))

    def test_duplicate_media_does_not_manufacture_coverage(self):
        clone = self.root / 'another.png'
        clone.write_bytes(self.image.read_bytes())
        self.gate['artifacts'].append({**self.gate['artifacts'][0], 'path':str(clone)})
        self.assertTrue(any('identical media' in e for e in self.errors()))

    def test_mjpeg_decode_and_segment_bounds(self):
        video = self.root / 'motion.avi'
        write_mjpeg_avi(video)
        self.assertEqual(decode_media(video,'video')['frames'], 6)
        item = {'path':str(video),'kind':'video','sha256':sha256(video),'states':['cycle'],'segments':{'cycle':[0,3]}}
        self.gate['artifacts'] = [item]
        self.assertEqual(validate_gate_integrity('motion',self.gate,'builder',self.metadata,self.root), [])
        item['segments']['cycle'] = [0,300]
        self.assertTrue(any('timed segment' in e for e in validate_gate_integrity('motion',self.gate,'builder',self.metadata,self.root)))

    def test_text_with_avi_extension_is_rejected(self):
        video = self.root / 'fake.avi'
        video.write_text('video placeholder',encoding='utf-8')
        with self.assertRaises(ValueError):
            decode_media(video,'video')

    def test_watchback_requires_actual_finite_full_duration_observations(self):
        video = self.root / 'motion.avi'
        write_mjpeg_avi(video)
        digest = sha256(video)
        self.gate['artifacts'] = [{'path':str(video), 'kind':'video', 'sha256':digest,
                                  'states':['cycle'], 'segments':{'cycle':[0, 3]}}]
        gate_id = 'production_motion_quality_evidence'
        def errors():
            return validate_gate_integrity(gate_id,self.gate,'builder',self.metadata,self.root)
        self.assertTrue(errors())
        valid = {'playback_speed':1,'start_seconds':0,'end_seconds':3,
                 'observations':['Synthetic timing-contract observation, not aesthetic approval.']}
        self.gate['watchback'] = {digest:copy.deepcopy(valid)}
        self.assertEqual(errors(), [])
        for field, value in [('playback_speed',True),('playback_speed',0.5),('end_seconds',float('nan')),
                             ('end_seconds',1),('observations',True),('observations',['TODO'])]:
            with self.subTest(field=field,value=value):
                self.gate['watchback'][digest] = {**valid,field:value}
                self.assertTrue(errors())

    def test_blind_receipt_boolean_is_not_an_observation(self):
        self.receipt['gates'][self.gate_id]['first_read_observations'] = True
        self.save_receipt()
        self.assertTrue(any('first-read' in e for e in self.errors()))

    def test_binder_preserves_verdicts_and_does_not_renew_receipt(self):
        source = self.root/'source.json'
        output = self.root/'bound.json'
        self.gate['status'] = 'not_tested'
        source.write_text(json.dumps({'run_metadata':self.metadata,'gates':{self.gate_id:self.gate}}),encoding='utf-8')
        before = self.gate['reviewer']['receipt']['sha256']
        command = [sys.executable,'-B',str(ROOT/'scripts/evidence_bind.py'),'--evidence',str(source),
                   '--candidate',str(self.candidate),'--build-id','B','--output',str(output)]
        result = subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        bound = json.loads(output.read_text())
        gate = bound['gates'][self.gate_id]
        self.assertEqual(gate['status'],'not_tested')
        self.assertEqual(gate['reviewer']['receipt']['sha256'],before)
        self.assertTrue(validate_gate_integrity(self.gate_id,gate,'independent',bound['run_metadata'],self.root))
        self.assertEqual(subprocess.run(command,capture_output=True,text=True).returncode,2)

    def test_truncated_video_is_rejected(self):
        video = self.root / 'broken.avi'
        write_mjpeg_avi(video)
        video.write_bytes(video.read_bytes()[:-30])
        with self.assertRaises(ValueError):
            decode_media(video,'video')

    def test_scorecard_rejects_fake_png_end_to_end(self):
        source = load_eval_evidence()
        source['case_id'] = 'new-2-5d-complete'
        for key in ['audio_direction_quality','asset_pipeline']:
            source['scores'][key] = {'score':3,'evidence':['synthetic unit evidence']}
        source = bind_synthetic_fixture(source)
        evidence = self.root/'evidence.json'
        report = self.root/'scorecard.json'
        def run():
            evidence.write_text(json.dumps(source),encoding='utf-8')
            return subprocess.run([sys.executable,'-B',str(ROOT/'scripts/eval_scorecard.py'),'--rubric',str(ROOT/'evals/rubric.json'),'--evidence',str(evidence),'--case',source['case_id'],'--json-output',str(report),'--summary'],capture_output=True,text=True)
        self.assertEqual(run().returncode, 0)
        fake = self.root/'fake.png'
        fake.write_text('not an image',encoding='utf-8')
        gate = source['gates']['art_direction_selection_evidence']
        gate['artifacts'][1]['path'] = str(fake)
        gate['artifacts'][1]['sha256'] = sha256(fake)
        self.assertEqual(run().returncode, 1)
        result = json.loads(report.read_text())
        self.assertEqual(result['responsibility_status'],'builder_work_remaining')


class ForwardExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'brief.md').write_text('Synthetic test brief',encoding='utf-8')
        (self.root/'result.log').write_text('Synthetic observed result',encoding='utf-8')
        revision = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        self.data = {'schema_version':2,'scope':'focused','skill_commit':revision,'required_contracts':['ui'],'scenarios':[]}
        for positive in [True,False]:
            verdict = 'pass' if positive else 'fail'
            identity = 'good' if positive else 'bad'
            hashes = {'result.log':sha256(self.root/'result.log')}
            receipt = {'skill_commit':revision,'scenario_id':identity,'observed_verdict':verdict,
                       'builder_context':'builder','reviewer_context':'reviewer','source_message':'test-response',
                       'observations':['Synthetic validator exercise only.'],'artifact_sha256':hashes}
            path = self.root/(identity+'.json')
            path.write_text(json.dumps(receipt),encoding='utf-8')
            self.data['scenarios'].append({'id':identity,'brief_path':'brief.md','brief_sha256':sha256(self.root/'brief.md'),
                 'godot_version':'4.x','composite_case':'example','contracts':['ui'],'builder_context':'builder','reviewer_context':'reviewer',
                 'first_pass_verdict':verdict,'expected_verdict':verdict,'positive_fixture':positive,'negative_fixture':not positive,
                 'user_found_defects':[],'expected_gate_for_each_defect':{},'false_positive_burden':'Synthetic control input.',
                 'token_cost':0,'elapsed_minutes':0,'result_artifacts':['result.log'],'artifact_sha256':hashes,
                 'execution_receipt':{'path':path.name,'sha256':sha256(path)}})

    def test_consistent_bound_execution_record(self):
        self.assertEqual(audit(self.data,'execution',self.root)[0], [])

    def test_missing_raw_files_fail_execution(self):
        (self.root/'result.log').unlink()
        self.assertTrue(audit(self.data,'execution',self.root)[0])

    def test_negative_case_marked_pass_fails(self):
        self.data['scenarios'][1]['first_pass_verdict'] = 'pass'
        self.assertTrue(audit(self.data,'execution',self.root)[0])

    def test_fictional_revision_fails(self):
        self.data['skill_commit'] = 'post-fix-description'
        self.assertTrue(audit(self.data,'execution',self.root)[0])

    def test_legacy_declarations_are_not_execution(self):
        self.data['schema_version'] = 1
        self.assertTrue(audit(self.data,'execution',self.root)[0])
        errors,warnings,_ = audit(self.data,'coverage',self.root)
        self.assertEqual(errors, [])
        self.assertTrue(any('Declaration coverage only' in w for w in warnings))


if __name__ == '__main__':
    unittest.main()
