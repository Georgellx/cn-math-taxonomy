"""广州适配的可观察数据契约；不把目录核对等同于题库教师审核。"""
import hashlib
import json
import math
from decimal import Decimal, ROUND_HALF_UP
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

    def test_each_primary_volume_has_a_separate_evidence_boundary(self):
        profile = json.loads((ROOT / 'data/guangzhou-primary-review.json').read_text(encoding='utf-8'))
        volumes = profile.get('volume_reviews', [])
        self.assertEqual({(v['grade'], v['semester']) for v in volumes},
                         {(g, s) for g in range(1, 7) for s in ('上', '下')})
        for v in volumes:
            self.assertTrue(v['note'])
            self.assertTrue(v['sources'])
            if v['grade'] >= 4 and v['semester'] == '下':
                self.assertEqual(v['directory_status'], 'pending')
        self.assertIn('pep-2l', profile['sources'])

    def test_comparison_nodes_do_not_start_with_subtraction(self):
        for tid, answer in [('cnm_p009', '9＞6'), ('cnm_p029', '47＜74'),
                            ('cnm_p054', '3200＞2800'), ('cnm_p119', '3.5＞2.8')]:
            q = self.questions[tid + '_q1']
            self.assertEqual(q['type'], 'choice', tid)
            self.assertEqual(next(c['text'] for c in q['choices'] if c['key'] == q['answer']), answer)

    def test_grade_one_ordinal_and_grade_two_remainder_application(self):
        self.assertIn('从左', self.questions['cnm_p003_q1']['prompt'])
        self.assertIn('第几', self.questions['cnm_p003_q1']['prompt'])
        self.assertIn('至少', self.questions['cnm_p052_q1']['prompt'])
        self.assertEqual(self.questions['cnm_p052_q1']['answer'], '5')
        self.assertNotIn('毫米', self.questions['cnm_p040_q2']['prompt'])
        self.assertIn('减法', self.questions['cnm_p072_q1']['prompt'])

    def test_fractions_and_decimals_assess_the_named_concept(self):
        self.assertEqual(self.questions['cnm_p079_q2']['answer'], '1/2')
        self.assertEqual(self.questions['cnm_p079_q3']['answer'], '1/4')
        self.assertNotIn('小数作答', self.questions['cnm_p079_q2']['prompt'])
        self.assertIn('角', self.questions['cnm_p093_q1']['prompt'])
        self.assertIn('最大公因数', self.questions['cnm_p158_q1']['prompt'])
        self.assertEqual(self.questions['cnm_p158_q1']['answer'], '6')
        self.assertIn('保留一位小数', self.questions['cnm_p121_q3']['prompt'])
        self.assertEqual(self.questions['cnm_p121_q3']['answer'], '2.5')

    def test_geometry_statistics_and_routes_have_required_visuals(self):
        for tid in ('cnm_p024', 'cnm_p085', 'cnm_p100', 'cnm_p108',
                    'cnm_p130', 'cnm_p150', 'cnm_p180', 'cnm_p181',
                    'cnm_p193', 'cnm_p221', 'cnm_p222', 'cnm_p237'):
            for n in range(1, 5):
                self.assertIn('<svg', self.questions[f'{tid}_q{n}'].get('figure', ''), f'{tid}_q{n}')

    def test_spatial_and_repair_limits_remain_visible(self):
        # 修题不会把未核册次、实践能力或官方教材归属顺带标为已核。
        for tid in ('cnm_p085', 'cnm_p237', 'cnm_p241', 'cnm_p242'):
            self.assertEqual(self.topics[tid]['curriculum_review']['status'], 'pending')
        profile = json.loads((ROOT / 'data/guangzhou-primary-review.json').read_text(encoding='utf-8'))
        fixed = [self.questions[qid] for qid in profile['question_fixes']]
        self.assertEqual({self.topics[q['topicId']]['grade'] for q in fixed}, set(range(1, 7)))
        for grade in range(1, 7):
            batch = {q['id']: q for q in json.loads((ROOT / f'data/_qbatches/primary_g{grade}.json').read_text(encoding='utf-8'))}
            for q in fixed:
                if self.topics[q['topicId']]['grade'] == grade:
                    self.assertEqual(batch.get(q['id']), q)

    def test_other_subjects_secondary_math_and_dependencies_are_unchanged(self):
        expected = {
            'topics.json': 'b2b804a031f412c345dca3b5fc1aba88984328b45d2e45b9dbda2c066eac15b1',
            'questions.json': '2106f4400c6bec02aafc404bbd26fca0aafa71452f4b72afd62f5142c305cd34',
            'dependencies.json': 'b55ee6b1e259abf9c71effe231c8244b29b6c2fb29e068b5bd200ed304946f38',
            'cn-curriculum-standards.json': '5393764f8c01188c8d09cff443792864cfe3534d80d2639d7d5103850cc80bb8',
        }
        for name, digest in expected.items():
            value = json.loads((ROOT / 'data' / name).read_text(encoding='utf-8'))
            if name == 'topics.json':
                value = [t for t in value if not t['id'].startswith('cnm_p')]
            elif name == 'questions.json':
                value = [q for q in value if not q['topicId'].startswith('cnm_p')]
            actual = hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            self.assertEqual(actual, digest, name)

    def test_protractor_rays_and_net_answers_match_independent_geometry(self):
        ns = '{http://www.w3.org/2000/svg}'
        for n in range(1, 5):
            q = self.questions[f'cnm_p100_q{n}']
            root = ET.fromstring(q['figure'])
            ray = next(e for e in root.findall(ns + 'path') if e.get('stroke') == '#a94b21')
            endpoint = ray.get('d').split('L')[-1].split()
            x, y = map(float, endpoint)
            angle = math.degrees(math.atan2(165 - y, x - 140))
            self.assertAlmostEqual(angle, float(q['answer']), delta=.01)
        for n, opposite in [(2, '3'), (3, '6'), (4, '4')]:
            self.assertEqual(self.questions[f'cnm_p222_q{n}']['answer'], opposite)

    def test_rounding_and_container_counts_use_the_complete_result(self):
        for qid, exact, places in [('cnm_p121_q3', '2.46', '0.1'),
                                    ('cnm_p135_q1', '3.84', '0.1'),
                                    ('cnm_p135_q2', '0.64', '0.1'),
                                    ('cnm_p135_q4', '2.832', '0.01')]:
            rounded = Decimal(exact).quantize(Decimal(places), rounding=ROUND_HALF_UP)
            self.assertEqual(Decimal(self.questions[qid]['answer']), rounded)
        for qid, count, capacity in [('cnm_p052_q1', 23, 5), ('cnm_p052_q3', 28, 6)]:
            self.assertEqual(int(self.questions[qid]['answer']), math.ceil(count / capacity))
        # 最简形式不能交给只比较数值的 numeric 判题器，否则6/8也会被当成3/4。
        for n in range(1, 5):
            self.assertEqual(self.questions[f'cnm_p168_q{n}']['type'], 'choice')

    def test_percentage_and_application_questions_require_quantity_relations(self):
        q = self.questions['cnm_p197_q1']
        self.assertIn('合格', q['prompt'])
        self.assertEqual(next(c['text'] for c in q['choices'] if c['key'] == q['answer']), '25%')
        self.assertIn('40%', self.questions['cnm_p198_q1']['prompt'])
        for tid in ('cnm_p059', 'cnm_p084', 'cnm_p087', 'cnm_p126', 'cnm_p134',
                    'cnm_p139', 'cnm_p179', 'cnm_p184', 'cnm_p187', 'cnm_p215'):
            for n in range(1, 5):
                prompt = self.questions[f'{tid}_q{n}']['prompt']
                self.assertFalse(prompt.startswith('计算：'), tid)
                self.assertNotIn('计算：', prompt, tid)
        self.assertIn('最小公倍数', self.questions['cnm_p159_q2']['prompt'])
        self.assertIn('容积', self.questions['cnm_p164_q1']['prompt'])


if __name__ == '__main__':
    unittest.main()
