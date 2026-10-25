"""广州适配的可观察数据契约；不把目录核对等同于题库教师审核。"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class GuangzhouDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.topics = {t['id']: t for t in json.loads((ROOT / 'data/topics.json').read_text(encoding='utf-8'))}
        cls.questions = {q['id']: q for q in json.loads((ROOT / 'data/questions.json').read_text(encoding='utf-8'))}

    def test_fraction_preparation_is_in_unit_four(self):
        for tid in ('cnm_p158', 'cnm_p159', 'cnm_p172'):
            self.assertEqual(self.topics[tid]['chapter'], '五年级下册 第4单元 分数的意义和性质')

    def test_enrichment_is_separate_from_grade_five_assessment(self):
        for tid in ('cnm_p143', 'cnm_p145', 'cnm_p146'):
            self.assertEqual(self.topics[tid].get('curriculum_review', {}).get('status'), 'supplementary')

    def test_unnumbered_activities_keep_their_volume(self):
        self.assertEqual(self.topics['cnm_p095']['chapter'], '三年级上册 数学广角 搭配问题')
        self.assertEqual(self.topics['cnm_p131']['chapter'], '四年级上册 数学广角 鸡兔同笼')
        self.assertEqual(self.topics['cnm_p236']['chapter'], '四年级上册 综合与实践 1亿有多大')
        self.assertEqual(self.topics['cnm_p015']['chapter'], '一年级上册 数学游戏 开篇活动')

    def test_comparison_assesses_comparison(self):
        expected = ['4＞2', '5＝5', '5＞3', '2＜4']
        for i, answer in enumerate(expected, 1):
            q = self.questions[f'cnm_p002_q{i}']
            self.assertEqual(q['type'], 'choice')
            self.assertEqual(next(c['text'] for c in q['choices'] if c['key'] == q['answer']), answer)

    def test_spatial_questions_supply_actual_figures(self):
        for tid in ('cnm_p113', 'cnm_p238'):
            for i in range(1, 5):
                q = self.questions[f'{tid}_q{i}']
                self.assertIn('<svg', q.get('figure', ''))
                self.assertTrue(all('<svg' in c.get('figure', '') for c in q['choices']))
                self.assertTrue(q.get('hideChoiceText'))

    def test_unconfirmed_spring_volumes_are_not_marked_aligned(self):
        for t in self.topics.values():
            if t['id'].startswith('cnm_p') and t['grade'] in (4, 5, 6) and t['semester'] == '下':
                self.assertEqual(t.get('curriculum_review', {}).get('status'), 'pending', t['id'])

    def test_spatial_answers_match_hand_checked_projections(self):
        q = self.questions['cnm_p113_q3']
        fig = next(c['figure'] for c in q['choices'] if c['key'] == q['answer'])
        rects = ET.fromstring(fig).findall('{http://www.w3.org/2000/svg}rect')
        self.assertEqual({(r.get('x'), r.get('y')) for r in rects},
                         {('62', '112'), ('94', '112'), ('62', '80'), ('94', '80')})
        q = self.questions['cnm_p238_q2']
        fig = next(c['figure'] for c in q['choices'] if c['key'] == q['answer'])
        polygon = ET.fromstring(fig).find('{http://www.w3.org/2000/svg}polygon')
        self.assertEqual(polygon.get('points'), '100,95 100,135 120,95')

    def test_reapply_is_idempotent_and_check_is_read_only(self):
        files = [ROOT / 'data/topics.json', ROOT / 'data/questions.json']
        before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in files]
        result = subprocess.run([sys.executable, '-X', 'utf8', 'scripts/align_guangzhou_primary.py', '--check'],
                                cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(before, [hashlib.sha256(p.read_bytes()).hexdigest() for p in files])


if __name__ == '__main__':
    unittest.main()
