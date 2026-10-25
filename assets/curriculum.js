/* 广州小学数学的核对状态。状态用于限制测评范围，不表示教师已审核题库。 */
(function (root, factory) {
  if (typeof module !== 'undefined' && module.exports) module.exports = factory();
  else root.CnmCurriculum = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  function reviewOf(topic) {
    return topic && /^cnm_p\d+$/.test(topic.id) ? topic.curriculum_review || null : null;
  }
  function canAssess(topic) {
    var review = reviewOf(topic);
    return !review || review.status === 'corrected';
  }
  function label(topic) {
    var review = reviewOf(topic);
    if (!review) return '';
    return { corrected: '已修正', pending: '待核', supplementary: '拓展内容' }[review.status] || '待核';
  }
  function note(topic) {
    var review = reviewOf(topic);
    return review ? review.note || '' : '';
  }
  function summary(topics) {
    var out = { total: 0, eligible: 0, pending: 0, supplementary: 0 };
    topics.forEach(function (topic) {
      if (!/^cnm_p\d+$/.test(topic.id)) return;
      out.total++;
      if (canAssess(topic)) out.eligible++;
      else if (reviewOf(topic).status === 'supplementary') out.supplementary++;
      else out.pending++;
    });
    return out;
  }
  return { reviewOf: reviewOf, canAssess: canAssess, label: label, note: note, summary: summary };
});
