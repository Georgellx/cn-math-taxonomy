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
  function volumeTable(topics, profile) {
    var s = el('section');
    s.append(el('h2', '一至六年级各册核对进度'));
    s.append(el('p', '目录已核仅指所列目录页；知识点归属、题目覆盖和教师审定分别记录。可测数量表示当前允许选题。'));
    s.append(el('p', '手机上可横向滑动表格，查看完整说明。'));
    if (!profile.volume_reviews || !profile.volume_reviews.length) {
      s.append(el('p', '逐册核对记录正在更新，请联网刷新页面后查看。'));
      return s;
    }
    var wrap = el('div');
    wrap.className = 'review-table-wrap';
    var table = el('table');
    table.id = 'volume-review-table';
    table.append(el('caption', '小学十二册目录核对范围与测评状态'));
    var head = el('thead');
    var tr = el('tr');
    ['册次', '目录核对', '可测 / 待核 / 拓展', '范围与说明'].forEach(function (title) {
      var th = el('th', title); th.scope = 'col'; tr.append(th);
    });
    head.append(tr); table.append(head);
    var body = el('tbody');
    (profile.volume_reviews || []).forEach(function (v) {
      var row = el('tr');
      var label = '一二三四五六'[v.grade - 1] + v.semester;
      var th = el('th', label); th.scope = 'row'; row.append(th);
      var status = { official_directory_checked: '目录页已核', inherited_directory: '沿用前轮目录', pending: '待核' }[v.directory_status] || '待核';
      row.append(el('td', status));
      var counts = C.summary(topics.filter(function (t) { return t.grade === v.grade && t.semester === v.semester; }));
      row.append(el('td', counts.eligible + ' / ' + counts.pending + ' / ' + counts.supplementary));
      var note = el('td');
      note.append(el('p', v.note));
      v.sources.forEach(function (key) {
        var source = profile.sources[key];
        if (source) note.append(link(source.label, source.url), ' ');
      });
      row.append(note); body.append(row);
    });
    table.append(body); wrap.append(table); s.append(wrap);
    return s;
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
    box.append(volumeTable(topics, profile));
    ['pending', 'supplementary'].forEach(function (status) {
      var list = topics.filter(function (t) { var r = C.reviewOf(t); return r && r.status === status; });
      box.append(section((status === 'pending' ? '待核知识点' : '拓展内容') + '（' + list.length + '）', list.map(topicRow)));
    });
    box.append(section('尚未建点或覆盖不足的内容', profile.coverage_issues.map(function (issue) {
      var li = el('li');
      li.append(el('strong', issue.title + ' · 待核'), el('p', issue.note));
      return li;
    })));
    var fixedTopics = new Set(profile.question_fixes.map(function (id) { return id.replace(/_q\d+$/, ''); }));
    var corrected = topics.filter(function (t) { var r = profile.topic_reviews[t.id]; return r && (r.chapter || r.status === 'corrected' || fixedTopics.has(t.id)); });
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
