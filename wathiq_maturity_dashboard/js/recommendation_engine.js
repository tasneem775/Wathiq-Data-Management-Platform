/**
 * Recommendation Engine — pure text formatting over existing MQ maturity
 * results. Computes nothing: no new maturity level, no score, no
 * percentage, no compliance verdict. Its only inputs are exactly the three
 * fields named in the task spec:
 *   - current maturity level (mq.current_level)
 *   - missing evidence       (mq.next_level_gaps)
 *   - maturity requirement   (evidence_name / level_name, already produced
 *                              upstream by the Maturity Assessment layer)
 *
 * This module never reads coverage_percentage, compliance_percentage, or
 * any domain-level score, and never will — it only reformats fields that
 * already exist on the mq result object into a human-readable
 * recommendation.
 */

(function () {
  "use strict";

  /**
   * @param {object} mq - one entry from mock_data.js mq_results (or the
   *   real engine's equivalent shape).
   * @returns {{ status: 'complete'|'pending', title: string, body: string, actions: string[] }}
   */
  function generateRecommendation(mq) {
    const gaps = mq.next_level_gaps || [];

    // current_level/level_name/next_level/next_level_name/gaps مُضافة هنا
    // كحقول إخراج صريحة -- كلها مدخلات موجودة أصلاً لهذه الدالة (mq.*)، لا
    // حساب جديد ولا بيانات مخترعة. الهدف: تمكين طبقة العرض (app.js) من رسم
    // العلاقة Current → Missing → Next كصفوف منفصلة بدل طمرها داخل جملة
    // نصية واحدة فقط.
    if (gaps.length === 0) {
      return {
        status: "complete",
        title: `${mq.mq_id} — لا توجد فجوات معلّقة حالياً`,
        body: `بحسب آخر تقييم للأدلة، ${mq.mq_id} في أعلى مستوى نضج مدعوم حالياً بالأدلة المتوفرة (المستوى ${mq.current_level} — ${mq.level_name}).`,
        actions: [],
        current_level: mq.current_level,
        level_name: mq.level_name,
        next_level: mq.next_level,
        next_level_name: mq.next_level_name,
        gaps: gaps,
      };
    }

    const gapsList = gaps.join("، ");
    const nextLevelLabel = mq.next_level_name
      ? `المستوى ${mq.next_level} — ${mq.next_level_name}`
      : "المستوى التالي";

    return {
      status: "pending",
      title: "التوصية",
      body: `استكمال متطلبات ${gapsList} للانتقال إلى مستوى النضج التالي (${nextLevelLabel}).`,
      actions: ["مراجعة المتطلب.", "استكمال الدليل المطلوب.", "تحديث مستندات التصنيف."],
      current_level: mq.current_level,
      level_name: mq.level_name,
      next_level: mq.next_level,
      next_level_name: mq.next_level_name,
      gaps: gaps,
    };
  }

  /**
   * @param {object[]} mqResults
   * @returns {object[]} one recommendation per mq, same order as input.
   */
  function generateRecommendations(mqResults) {
    return (mqResults || []).map(function (mq) {
      return Object.assign({ mq_id: mq.mq_id }, generateRecommendation(mq));
    });
  }

  window.WathiqRecommendationEngine = {
    generateRecommendation: generateRecommendation,
    generateRecommendations: generateRecommendations,
  };
})();
