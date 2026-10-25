'use strict';
const assert = require('node:assert/strict');
const { test } = require('node:test');
const E = require('../diagnose/engine.js');
const fs = require('node:fs');
const path = require('node:path');

function topic(id, status, chapter = '五年级上册 第8单元 复习与关联') {
  const t = { id, name: id, grade: 5, semester: '上', chapter, external: false,
    diagnostic_question: { question: '比较4和2的大小', answer: '4＞2' } };
  if (status) t.curriculum_review = { status, note: '教材归属待核' };
  return t;
}
const topics = [topic('cnm_p001'), topic('cnm_p002', 'pending'),
  topic('cnm_p003', 'supplementary'), topic('cnm_p004', 'corrected')];
const deps = [{ topicId: 'cnm_p004', prerequisiteId: 'cnm_p002', strength: 'hard' }];
const graph = E.buildGraph(topics, deps);

test('整册只选可测内容，单独返回待核和拓展的编号', () => {
  const range = E.gradeTargets(graph, '五上');
  assert.deepEqual(range.ids, ['cnm_p001', 'cnm_p004']);
  assert.deepEqual(range.excludedIds, ['cnm_p002', 'cnm_p003']);
});
test('直接指定待核或拓展目标，也不能绕过测评范围', () => {
  for (const id of ['cnm_p002', 'cnm_p003']) {
    assert.throws(() => E.createSession(graph, [id]), /待核|拓展|自动测评/);
    assert.equal(E.isTestable(graph, id), false);
  }
  const s = E.createSession(graph, ['cnm_p002', 'cnm_p004']);
  assert.deepEqual(s.targets, ['cnm_p004']);
});
test('答错已修正目标时，不会回溯出待核题目', () => {
  let s = E.createSession(graph, ['cnm_p004']);
  s = E.applyAnswer(graph, s, 'cnm_p004', 'wrong');
  assert.equal(E.nextQuestion(graph, s), null);
});
test('答对目标，不把待核先修推断成已掌握', () => {
  let s = E.createSession(graph, ['cnm_p004']);
  s = E.applyAnswer(graph, s, 'cnm_p004', 'correct');
  assert.equal(E.statusOf(s, 'cnm_p002'), 'unknown');
  assert.ok(!E.summarize(graph, s).mastered.includes('cnm_p002'));
});
test('旧存档中的待核作答不能恢复为有效测评记录', () => {
  const s = E.createSession(graph, ['cnm_p004']);
  assert.throws(() => E.applyAnswer(graph, s, 'cnm_p002', 'correct'), /待核|拓展/);
});
test('待核先修单列，不混同为可测但未测或无题外部节点', () => {
  let s = E.createSession(graph, ['cnm_p004']);
  s = E.applyAnswer(graph, s, 'cnm_p004', 'wrong');
  const sum = E.summarize(graph, s);
  assert.deepEqual(sum.reviewExcluded, ['cnm_p002']);
  assert.ok(!sum.untested.includes('cnm_p002'));
  assert.deepEqual(sum.roots[0].reviewPrereqs, ['cnm_p002']);
  assert.deepEqual(sum.roots[0].externalPrereqs, []);
});
test('整册全部待核时保留范围说明，避免误报为无效册次', () => {
  const g = E.buildGraph([topic('cnm_p002', 'pending')], []);
  const range = E.gradeTargets(g, '五上');
  assert.deepEqual(range.ids, []);
  assert.deepEqual(range.excludedIds, ['cnm_p002']);
});
test('非编号活动保持所属册次，不伪造第8或第7单元', () => {
  assert.deepEqual(E.parseChapter('三年级上册 数学广角 搭配问题'),
    { volume: '三上', chapterNo: '数学广角', chapterName: '搭配问题', section: '' });
  assert.equal(E.parseChapter('一年级上册 数学游戏 开篇活动').volume, '一上');
});
test('中学与其他学科的诊断范围保持可用', () => {
  const junior = { ...topic('cnm_001'), grade: 7, chapter: '七上 第一章 有理数 1.1' };
  const g = E.buildGraph([junior], []);
  assert.deepEqual(E.gradeTargets(g, '七上').ids, ['cnm_001']);
});

const readData = name => JSON.parse(fs.readFileSync(path.join(__dirname, '../data', name), 'utf8'));
const productionTopics = readData('topics.json');
const productionGraph = E.buildGraph(productionTopics, readData('dependencies.json'), readData('questions.json'));
test('实际五上保留小数乘法，排除旧方程及待核内容；全年筛查也不能绕过', () => {
  for (const scope of ['五上', '五年级']) {
    const range = E.gradeTargets(productionGraph, scope);
    assert.ok(range.ids.includes('cnm_p132'));
    for (const id of ['cnm_p143', 'cnm_p145', 'cnm_p146', 'cnm_p135', 'cnm_p237']) {
      assert.ok(!range.ids.includes(id));
      assert.ok(range.excludedIds.includes(id));
    }
  }
});
test('实际2027春四至六下只能查阅待核内容，不能开始整册测评', () => {
  for (const scope of ['四下', '五下', '六下']) {
    const range = E.gradeTargets(productionGraph, scope);
    assert.deepEqual(range.ids, []);
    assert.ok(range.excludedIds.length > 10);
    assert.throws(() => E.createSession(productionGraph, range.excludedIds, { mode: 'screen' }), /待核|拓展/);
  }
});
test('实际初中回溯及整册模拟均不出被标记排除的题', () => {
  const excluded = new Set(productionTopics.filter(t => t.curriculum_review &&
    ['pending', 'supplementary'].includes(t.curriculum_review.status)).map(t => t.id));
  for (const targets of [['cnm_221'], E.gradeTargets(productionGraph, '四上').ids, E.gradeTargets(productionGraph, '五上').ids]) {
    let s = E.createSession(productionGraph, targets, { limit: 1000, seed: 'guangzhou-integration' });
    for (let count = 0; count < 1000; count++) {
      const item = E.nextItem(productionGraph, s);
      if (!item) break;
      assert.ok(!excluded.has(item.topicId), item.topicId);
      s = E.applyAnswer(productionGraph, s, item.topicId, 'wrong');
    }
    assert.equal(E.nextQuestion(productionGraph, s), null);
    const sum = E.summarize(productionGraph, s);
    assert.ok(sum.path.every(p => !excluded.has(p.id)));
    assert.ok(sum.mastered.every(id => !excluded.has(id)));
  }
});
