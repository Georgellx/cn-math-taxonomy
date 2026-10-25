#!/usr/bin/env python3
"""将广州 2026 秋小学数学的已确认修正及待核状态应用到现有数据。

保留稳定 id、先修边和其他学科。--check 只比较，不写文件。
旧 build_primary.py 未完整保存上游 2026-10-22 的手工修订，不能用来重建本分支。
"""
import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATE = '2026-10-25'
PROFILE_ID = 'guangzhou-pep-primary-2026-autumn'
SOURCES = {
    'gz-2026': {'label': '广州日报：2026秋换版说明（简易方程调整到初中）',
                'url': 'https://news.dayoo.com/guangzhou/202608/31/139995_54998235.htm',
                'scope': '广州换版背景与方程调整；不是十二册逐页核验'},
    'pep-1u': {'label': '人教社一年级上册', 'url': 'https://book.pep.com.cn/1221001101241/', 'scope': '目录页：数学游戏及六个编号单元'},
    'pep-3u': {'label': '人教社三年级上册', 'url': 'https://book.pep.com.cn/1221001301251/', 'scope': '目录页止于第7单元，不把数学广角编为第8单元'},
    'pep-4u': {'label': '人教社四年级上册', 'url': 'https://book.pep.com.cn/1221001401261/', 'scope': '目录页；1亿有多大为单列实践活动；无第8单元'},
    'pep-5u': {'label': '人教社五年级上册', 'url': 'https://book.pep.com.cn/1221001501261/', 'scope': '目录及观察简单组合体示例；后续正文预览受访问验证限制'},
    'moe-fractions': {'label': '教育部基础教育精品课目录',
                      'url': 'https://www.moe.gov.cn/jyb_xxgk/s5743/s5744/A06/202404/W020240402490580211463.pdf',
                      'scope': '现行旧版五下第4单元约分/通分及最大公因数、最小公倍数；不证明2027春新版目录'},
    'upstream': {'label': '上游小学册次来源与待核说明',
                 'url': 'https://github.com/xiaoyang111222/cn-math-taxonomy/blob/5ca171dbbb1a85d73c14f35f7e915655bf8e5b1f/README.md',
                 'scope': '继承的目录、临时迁移与尚未核实的小节说明'},
}


def entry(status, note, sources, **changes):
    return dict(status=status, note=note, sources=sources, **changes)


REVIEWS = {
    'cnm_p002': entry('corrected', '已将减法计算题替换为大小比较题；题库尚未经教师审核。', ['pep-1u']),
    'cnm_p015': entry('pending', '已用官方开篇「数学游戏」替换自定义「我的教室」栏目；相对位置内容与活动的具体对应仍待核。', ['pep-1u'], chapter='一年级上册 数学游戏 开篇活动'),
    'cnm_p022': entry('pending', '已归并到官方开篇「数学游戏」；原「数学游戏分享」是课标主题名，具体内容对应仍待核。', ['pep-1u'], chapter='一年级上册 数学游戏 开篇活动'),
    'cnm_p095': entry('corrected', '去掉项目自编的第8单元号，保留同册非编号数学广角；不是新增必学单元。', ['pep-3u'], chapter='三年级上册 数学广角 搭配问题'),
    'cnm_p131': entry('corrected', '去掉项目自编的第8单元号，保留同册非编号数学广角；不是新增必学单元。', ['pep-4u'], chapter='四年级上册 数学广角 鸡兔同笼'),
    'cnm_p236': entry('corrected', '按官方目录单列综合与实践；题目只能辅助检查量感，不能替代实际估测。', ['pep-4u'], chapter='四年级上册 综合与实践 1亿有多大', domain='综合与实践'),
    'cnm_p158': entry('pending', '已修正现行旧版归属：第4单元「分数的意义和性质」；2027春新版册次仍待核。', ['moe-fractions', 'upstream'], chapter='五年级下册 第4单元 分数的意义和性质'),
    'cnm_p159': entry('pending', '已修正现行旧版归属：第4单元「分数的意义和性质」；2027春新版册次仍待核。', ['moe-fractions', 'upstream'], chapter='五年级下册 第4单元 分数的意义和性质'),
    'cnm_p172': entry('pending', '已修正现行旧版归属：第4单元「分数的意义和性质」；2027春新版册次仍待核。', ['moe-fractions', 'upstream'], chapter='五年级下册 第4单元 分数的意义和性质'),
    'cnm_p113': entry('pending', '已用实际视图选择题替换无关加减计算；2027春四下目录及本点册次仍待核。', ['upstream']),
    'cnm_p238': entry('corrected', '已补充平移、旋转和轴对称的图示辨认题；选择题不能替代实际作图检查。', ['pep-5u']),
    'cnm_p237': entry('pending', '当前题目对三视图还原、拼搭及最少/最多小正方体的覆盖不足，待补充核验。', ['pep-5u']),
    'cnm_p241': entry('pending', '当前主要是体育情境计算，不能完整评价教材要求的问题选择、数据收集与交流。', ['upstream']),
    'cnm_p242': entry('pending', '当前主要是用水量计算，不能完整评价真实调查、节水方案及交流展示。', ['upstream']),
    'cnm_p216': entry('pending', '去掉自编第7单元号；同册数学广角的具体位置和选学范围待核。', ['upstream'], chapter='六年级上册 数学广角 鸽巢问题'),
}
for tid in ('cnm_p143', 'cnm_p145', 'cnm_p146'):
    REVIEWS[tid] = entry('supplementary', '新版把简易方程调整到初中；保留旧知识点与先修引用供查阅，不纳入广州小学自动测评。', ['gz-2026', 'upstream'])
for tid, reason in {
    'cnm_p060': '简单变化规律暂挂二下复习，具体小节归属未核。',
    'cnm_p061': '时、分、秒由三上迁入二下实践活动，具体范围待核。',
    'cnm_p062': '时、分、秒的进率在二下活动中的范围待核。',
    'cnm_p063': '经过时间在二下活动中的要求待核。',
    'cnm_p073': '倍的认识暂挂三上复习，新版具体归属待核。',
    'cnm_p081': '集合图里的重叠暂挂三上复习，新版具体归属待核。',
    'cnm_p082': '八个方向暂挂三下复习，新版具体归属待核。',
    'cnm_p085': '新版单元为数据的收集与整理，原复式统计表节点的覆盖范围待核。',
    'cnm_p098': '公顷和平方千米移入五上多边形面积，具体小节待核。',
    'cnm_p109': '简单优化暂挂四上复习，新版具体归属待核。',
    'cnm_p135': '积的近似数暂挂五上复习；是否仍属于小数乘法正文及其要求待核，不能认定已删除。',
    'cnm_p144': '节点含利用等式性质分离未知数的要求，与新版用字母表示数量关系的边界待核。',
    'cnm_p151': '植树问题暂挂五上复习，新版选学位置与要求待核。',
    'cnm_p203': '百分数单元合并后，折扣是否仍为本册必学内容待核。',
    'cnm_p204': '百分数单元合并后，利率是否仍为本册必学内容待核。',
    'cnm_p205': '百分数单元合并后，沿用的应用题范围待逐页核验。',
}.items():
    REVIEWS[tid] = entry('pending', reason, ['upstream'])

BOOK_REVIEWS = [
    {'grade': grade, 'semester': '下', 'status': 'pending',
     'note': '本分支以2026秋为基准。此册含现行旧版和临时迁移内容，尚未对齐2027春正式教材，整体标为待核。',
     'sources': ['upstream']}
    for grade in (4, 5, 6)
]
COVERAGE_ISSUES = [
    {'id': 'decimal-coverage', 'title': '五上：循环小数、商的近似数',
     'status': 'pending', 'note': '尚无专门节点与诊断题。配套教学资料提示可能漏项，需用正式教材确认范围后补点；本轮不据此编造章节、页码或题目。'},
    {'id': 'practice-coverage', 'title': '数学连环画、营养午餐等实践活动',
     'status': 'pending', 'note': '尚无独立知识点，不表示活动已被教材删除；实践成果、真实调查和作图需要线下检查。'},
]


def svg(body, title='题目图示', width=260, height=175):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{title}"><title>{title}</title>{body}</svg>'


def plane(cells):
    return svg(''.join(f'<rect x="{62 + x * 32}" y="{112 - y * 32}" width="32" height="32" fill="#d5edf4" stroke="#254f64" stroke-width="2"/>' for x, y in cells), '候选视图', 220, 170)


def cubes(points):
    def p(x, y, z):
        return f'{120 + 26 * (x - y)},{92 + 13 * (x + y) - 26 * z}'
    body = ''
    for x, y, z in sorted(points, key=lambda a: (sum(a), a[2], a[0])):
        for color, corners in (
            ('#80b8ce', [(x+1,y,z), (x+1,y+1,z), (x+1,y+1,z+1), (x+1,y,z+1)]),
            ('#acd4e3', [(x,y+1,z), (x+1,y+1,z), (x+1,y+1,z+1), (x,y+1,z+1)]),
            ('#deeff5', [(x,y,z+1), (x+1,y,z+1), (x+1,y+1,z+1), (x,y+1,z+1)])):
            body += f'<polygon points="{" ".join(p(*c) for c in corners)}" fill="{color}" stroke="#254f64" stroke-width="1.5"/>'
    body += '<path d="M92 154 L110 128 M110 128 L100 132 M110 128 L109 139" stroke="#173c50" stroke-width="2" fill="none"/><text x="50" y="162" font-size="16" fill="#173c50">前面</text>'
    return svg(body, '小正方体组合体，箭头标示前面')


def triangle(points, axis=False):
    body = ''.join(f'<path d="M{20+i*20} 15V155 M20 {15+i*20}H180" stroke="#d2dce0"/>' for i in range(8))
    if axis:
        body += '<path d="M100 15V155" stroke="#b74d22" stroke-dasharray="5 4" stroke-width="2"/>'
    body += '<circle cx="100" cy="95" r="3" fill="#173c50"/><text x="104" y="109" font-size="13">O</text>'
    coords = ' '.join(f'{100+x*20},{95-y*20}' for x, y in points)
    body += f'<polygon points="{coords}" fill="#bfdeec" stroke="#254f64" stroke-width="2"/>'
    return svg(body, '方格中的三角形，每小格边长相同', 210, 175)


def choice(tid, n, prompt, answers, correct, explanation, figure=None, figures=None):
    q = {'id': f'{tid}_q{n}', 'topicId': tid, 'difficulty': 'basic' if n <= 2 else 'standard',
         'type': 'choice', 'prompt': prompt,
         'choices': [{'key': 'ABCD'[i], 'text': text} for i, text in enumerate(answers)],
         'answer': 'ABCD'[correct], 'explanation': explanation, 'verify': repr(answers[correct]),
         'fixed_from_source': '广州适配：修正题目与知识点的对应，不表示教师审核或盲解核验。'}
    if figure:
        q['figure'] = figure
    if figures:
        q['hideChoiceText'] = True
        for c, fig in zip(q['choices'], figures):
            c['figure'] = fig
    return q


def replacements():
    out = []
    for n, prompt, answers, correct in [
        (1, '比较4和2的大小，哪种写法正确？', ['4＞2', '4＜2', '4＝2'], 0),
        (2, '比较5和5的大小，哪种写法正确？', ['5＞5', '5＝5', '5＜5'], 1),
        (3, '小明有5颗珠子，小红有3颗。比较两人珠子的数量，哪种写法正确？', ['5＜3', '5＝3', '5＞3'], 2),
        (4, '比较2和4的大小，哪种写法正确？', ['2＝4', '2＜4', '2＞4'], 1)]:
        out.append(choice('cnm_p002', n, prompt, answers, correct, '从1到5依次增大；数量相同用＝，多用＞，少用＜。'))
    shape = [(0,0,0), (1,0,0), (0,0,1)]
    row2, row3, col2, ell = [(0,0),(1,0)], [(0,0),(1,0),(2,0)], [(0,0),(0,1)], [(0,0),(1,0),(0,1)]
    for n, direction, obj, options, correct, explanation in [
        (1, '前面', shape, [ell, row3, row2], 0, '前面能看到两列，左列高2格、右列高1格。'),
        (2, '上面', shape, [ell, row2, col2], 1, '上面的投影只占两个并排的位置，叠高不会增加占地格数。'),
        (3, '上面', [(0,0,0),(1,0,0),(0,1,0),(1,1,0)], [row3, col2, [(0,0),(1,0),(0,1),(1,1)]], 2, '四个小正方体占地组成2行2列的正方形。'),
        (4, '左面', shape, [row2, col2, ell], 1, '从左面观察，能看到一列高2格。')]:
        out.append(choice('cnm_p113', n, f'观察图中的组合体。从{direction}看到的图形是哪一个？',
                          ['图一', '图二', '图三'], correct, explanation, cubes(obj), [plane(c) for c in options]))
    original = [(0,0),(2,0),(0,1)]
    cases = [
        ('把三角形向右平移2格，结果是哪一个？', [[(2,0),(4,0),(2,1)], [(0,2),(2,2),(0,3)], [(-2,0),(0,0),(-2,1)]], 0, False, '每个顶点都向右移动2格，形状和方向不变。'),
        ('绕O点顺时针旋转90°，结果是哪一个？', [[(0,0),(0,2),(-1,0)], [(0,0),(0,-2),(1,0)], [(0,0),(-2,0),(0,-1)]], 1, False, '向右的边转到下方，向上的边转到右方。'),
        ('以竖直虚线为对称轴，轴对称后的图形是哪一个？', [[(0,0),(0,-2),(1,0)], [(0,0),(-2,0),(0,-1)], [(0,0),(-2,0),(0,1)]], 2, True, '对应顶点在对称轴两侧，到轴的距离相等。'),
        ('把三角形向上平移2格，结果是哪一个？', [[(0,-2),(2,-2),(0,-1)], [(0,2),(2,2),(0,3)], [(2,0),(4,0),(2,1)]], 1, False, '每个顶点向上移动2格，边的方向不变。'),
    ]
    for n, (prompt, options, correct, axis, explanation) in enumerate(cases, 1):
        out.append(choice('cnm_p238', n, prompt, ['图一','图二','图三'], correct, explanation,
                          triangle(original, axis), [triangle(points, axis) for points in options]))
    return out


def adapt(topics, questions):
    topics, questions = copy.deepcopy(topics), copy.deepcopy(questions)
    by_id = {t['id']: t for t in topics}
    missing = set(REVIEWS) - set(by_id)
    if missing:
        raise ValueError(f'核对记录指向不存在的知识点：{sorted(missing)}；不能用旧生成器覆盖新版数据')
    changes = replacements()
    by_qid = {q['id']: q for q in questions}
    if any(q['id'] not in by_qid for q in changes):
        raise ValueError('待修正题目缺失，停止覆盖')
    for t in topics:
        if not t['id'].startswith('cnm_p'):
            continue
        t.pop('curriculum_review', None)
        review = next((dict(b) for b in BOOK_REVIEWS if t['grade'] == b['grade'] and t['semester'] == b['semester']), None)
        explicit = REVIEWS.get(t['id'])
        if explicit:
            review = dict(explicit)
            for field in ('chapter', 'domain'):
                if field in review:
                    t[field] = review.pop(field)
        if review:
            review.pop('grade', None)
            review.pop('semester', None)
            review.update(profile=PROFILE_ID, reviewed_at=DATE)
            t['curriculum_review'] = review
    replacements_by_id = {q['id']: q for q in changes}
    questions = [replacements_by_id.get(q['id'], q) for q in questions]
    for q in changes:
        if q['id'].endswith('_q1'):
            correct = next(c['text'] for c in q['choices'] if c['key'] == q['answer'])
            by_id[q['topicId']]['diagnostic_question'] = {'question': q['prompt'], 'answer': correct}
    profile = {'id': PROFILE_ID, 'label': '广州现用人教版小学数学 · 2026秋', 'reviewed_at': DATE,
               'scope': '一至六年级上册按2026秋目录整理；四至六年级下册的2027春正式安排待核。未标记内容沿用上游，不代表逐页或教师审核。',
               'sources': SOURCES, 'book_reviews': BOOK_REVIEWS, 'topic_reviews': REVIEWS,
               'coverage_issues': COVERAGE_ISSUES,
               'question_fixes': [q['id'] for q in changes]}
    return topics, questions, profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='只读检查是否已应用全部修正')
    args = parser.parse_args()
    data = ROOT / 'data'
    load = lambda name: json.loads((data / name).read_text(encoding='utf-8'))
    topics, questions, profile = adapt(load('topics.json'), load('questions.json'))
    outputs = {'topics.json': (topics, 2), 'questions.json': (questions, 2), 'guangzhou-primary-review.json': (profile, 2)}
    fixed_ids = set(profile['question_fixes'])
    qbyid = {q['id']: q for q in questions if q['id'] in fixed_ids}
    grades = {t['id']: t['grade'] for t in topics}
    for grade in (1, 4, 5):
        name = f'_qbatches/primary_g{grade}.json'
        batch = load(name)
        existing = {q['id'] for q in batch}
        batch = [qbyid.get(q['id'], q) for q in batch]
        batch.extend(q for q in qbyid.values() if q['id'] not in existing and grades[q['topicId']] == grade)
        outputs[name] = (batch, 1)
    stale = []
    for name, (value, indent) in outputs.items():
        path = data / name
        encoded = json.dumps(value, ensure_ascii=False, indent=indent) + '\n'
        if not path.exists() or path.read_text(encoding='utf-8') != encoded:
            stale.append(name)
            if not args.check:
                path.write_text(encoded, encoding='utf-8', newline='\n')
    if args.check and stale:
        print('广州适配尚未应用：' + ', '.join(stale))
        return 1
    print(('检查通过' if args.check else '已应用广州适配') + f'：{len(REVIEWS)}条核对记录，{len(profile["question_fixes"])}道题目修正；待核内容保持显式标记。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
