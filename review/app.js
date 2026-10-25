(function () {
  'use strict';
  var C = window.CnmCurriculum;
  function el(tag, text) {
    var node = document.createElement(tag);
    if (text) node.textContent = text;
    return node;
  }
  function link(text, href) {
    var a = el('a', text);
    a.href = href;
    return a;
  }
  function section(title, nodes) {
    var s = el('section');
    s.append(el('h2', title));
    var list = el('ul');
    nodes.forEach(function (node) { list.append(node); });
    s.append(list);
    return s;
  }
  function topicRow(t) {
    var li = el('li');
    li.append(link(t.name, '../explore/#' + encodeURIComponent(t.id)), ' ', el('code', t.id));
    var note = el('span', t.chapter + '。' + C.note(t));
    note.className = 'review-reason';
    li.append(note);
    return li;
  }
  Promise.all(['../data/topics.json', '../data/guangzhou-primary-review.json'].map(function (url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
  })).then(function (data) {
    var topics = data[0].filter(function (t) { return /^cnm_p\d+$/.test(t.id); });
    var profile = data[1];
    var counts = C.summary(topics);
    document.getElementById('review-summary').textContent = '核对日期：' + profile.reviewed_at + '。小学共 ' + counts.total + ' 个知识点；可测 ' + counts.eligible + '，待核 ' + counts.pending + '，拓展 ' + counts.supplementary + '。';
    var box = document.getElementById('review-content');
    ['pending', 'supplementary'].forEach(function (status) {
      var list = topics.filter(function (t) { var r = C.reviewOf(t); return r && r.status === status; });
      box.append(section((status === 'pending' ? '待核知识点' : '拓展内容') + '（' + list.length + '）', list.map(topicRow)));
    });
    box.append(section('尚未建点或覆盖不足的内容', profile.coverage_issues.map(function (issue) {
      var li = el('li');
      li.append(el('strong', issue.title + ' · 待核'), el('p', issue.note));
      return li;
    })));
    var corrected = topics.filter(function (t) { var r = profile.topic_reviews[t.id]; return r && (r.chapter || r.status === 'corrected'); });
    box.append(section('本轮目录与题目修正', corrected.map(topicRow)));
    box.append(section('核对依据及适用范围', Object.keys(profile.sources).map(function (key) {
      var source = profile.sources[key];
      var li = el('li');
      li.append(link(source.label, source.url), el('p', source.scope));
      return li;
    })));
  }).catch(function (error) {
    document.getElementById('review-summary').textContent = '核对记录加载失败：' + error.message + '。请联网重试。';
  });
})();
