/**
 * Wathiq — Maturity Dashboard (DC) — rendering & interaction.
 *
 * Architecture note: every DOM-building function below reads only the
 * fields already present on the maturity report shape (mq_id,
 * current_level, level_name, next_level_gaps, evaluated_evidence...). None
 * of them compute a new value — they format what loadMaturityData()
 * returns. Swapping the data source (see loadMaturityData) is the only
 * change needed to connect this UI to the real
 * src/maturity_assessment/maturity_report_generator.py output later.
 */

(function () {
  "use strict";

  /* ---------------------------------------------------------------- */
  /* Data loading — the one function to change when wiring real data   */
  /* ---------------------------------------------------------------- */

  // Single source of truth for where the report comes from. Every other
  // function in this file (and recommendation_engine.js) receives its data
  // as a plain object passed down from loadMaturityData()'s resolved
  // promise -- nothing else reads this URL or performs its own fetch/parse.
  const MATURITY_DATA_URL = "data/sample_maturity_report.json";

  function loadMaturityData() {
    // Phase 1.5: fetches the static sample JSON below.
    // Phase 2 (real backend): swap MATURITY_DATA_URL for a REST endpoint
    // (e.g. '/api/maturity/DC') -- the fetch/json() call shape is already
    // what a real API call looks like, so nothing else in this file changes.
    return fetch(MATURITY_DATA_URL).then(function (response) {
      if (!response.ok) {
        throw new Error(
          "loadMaturityData(): failed to load " + MATURITY_DATA_URL + " (HTTP " + response.status + ")"
        );
      }
      return response.json();
    });
  }

  /* ---------------------------------------------------------------- */
  /* Small helpers                                                      */
  /* ---------------------------------------------------------------- */

  function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value == null ? "" : String(value);
    return div.innerHTML;
  }

  // نص evidence_name الخام لسجلَّين فقط في sample_maturity_report.json
  // (DC.C.3.1 وDC.M.12) ينتهي بقوس إنجليزي يكرر حرفياً ما قيل بالعربي
  // مباشرة قبله -- عرض فقط، بلا أي تعديل على الملف نفسه (Arabic Terminology
  // Audit). مطابقة حرفية دقيقة فقط (لا Regex عام) حتى لا يتأثر أي نص آخر
  // لم يُتحقَّق منه صراحة.
  var EVIDENCE_NAME_DISPLAY_OVERRIDES = {
    "تقرير جرد المجموعات التي تم تحديدها من البيانات والسجلات (Identified Datasets & Artifacts)":
      "تقرير جرد المجموعات التي تم تحديدها من البيانات والسجلات",
    "تقرير مراقبة آلية مراجعة تصنيف البيانات عبر مؤشرات الأداء الرئيسية (KPIs) المحددة مسبقاً":
      "تقرير مراقبة آلية مراجعة تصنيف البيانات عبر مؤشرات الأداء الرئيسية المحددة مسبقاً",
  };
  function evidenceNameDisplay(name) {
    return (name && EVIDENCE_NAME_DISPLAY_OVERRIDES[name]) || name;
  }

  function statusBadgeAttr(status) {
    if (status === "PASS") return "pass";
    if (status === "PARTIAL_PASS") return "partial";
    return "fail";
  }

  function statusLabelAr(status) {
    if (status === "PASS") return "مستوفى";
    if (status === "PARTIAL_PASS") return "مستوفى جزئياً";
    if (status === "FAIL") return "غير مستوفى";
    if (status === "NOT_PROVIDED") return "غير مُقدَّم";
    return status;
  }

  function findEvidence(mq, code) {
    return (mq.evaluated_evidence || []).find(function (e) {
      return e.evidence_code === code;
    });
  }

  // Display-only Arabic substitution for the small number of known English
  // fragments the JSON's own free-text fields (architectural_note,
  // maturity_assessment_status.reason) still contain. This never touches
  // data/sample_maturity_report.json itself -- it only rewrites what is
  // shown on screen, so the underlying data stays byte-for-byte unchanged.
  function arabizeDisplayText(text) {
    return String(text)
      .replace(/\bDomain Maturity\b/g, "نضج المجال")
      .replace(/\bNo official aggregation rule between MQs found\b/, "لا توجد قاعدة تجميع رسمية بين المتطلبات")
      .replace(/\bMQs\b/g, "المتطلبات")
      .replace(/\bMQ\b/g, "متطلب")
      // إصلاح لغوي عرضي فقط (لا يلمس sample_maturity_report.json): بعد
      // الاستبدال أعلاه يصبح النص "...ولا تمثل نضج المجال نهائية..." --
      // عدم تطابق نحوي (نهائية مؤنث لا يطابق "نضج المجال"). يُستبدَل هنا
      // بصياغة سليمة نحوياً بنفس المعنى تماماً.
      .replace(/نضج المجال نهائية/, "مستوى نضج المجال النهائي");
  }

  /* ---------------------------------------------------------------- */
  /* Overview                                                            */
  /* ---------------------------------------------------------------- */

  function renderOverview(data) {
    document.getElementById("wq-domain-name").textContent = data.domain_name;
    document.getElementById("wq-header-domain").textContent =
      data.domain_name + " (" + data.domain + ")";
    document.getElementById("wq-domain-context").textContent =
      data.domain_name + " (" + data.domain + ")";

    document.getElementById("wq-stat-evaluated").textContent =
      data.assessment_overview.evaluated_mqs + " / " + data.assessment_overview.total_mqs;
    document.getElementById("wq-stat-completion").textContent =
      data.assessment_overview.completion_status;
    document.getElementById("wq-stat-domain-status").textContent =
      data.maturity_assessment_status.domain_level_calculation === "NOT_AVAILABLE"
        ? "غير متاح"
        : data.maturity_assessment_status.domain_level_calculation;
    document.getElementById("wq-stat-domain-status-sub").textContent =
      arabizeDisplayText(data.maturity_assessment_status.reason);

    document.getElementById("wq-architectural-note").textContent =
      arabizeDisplayText(data.architectural_note);
  }

  /* ---------------------------------------------------------------- */
  /* MQ Maturity Cards                                                    */
  /* ---------------------------------------------------------------- */

  function levelTrackHtml(currentLevel, nextLevel) {
    let html = "";
    for (let level = 0; level <= 5; level += 1) {
      const achieved = level > 0 && level <= currentLevel;
      const isTarget = level === nextLevel;
      html +=
        '<div class="wq-level-track__seg" data-achieved="' +
        achieved +
        '" data-target="' +
        isTarget +
        '" title="مستوى ' +
        level +
        '"></div>';
    }
    return html;
  }

  // أيقونتان زخرفيتان فقط (aria-hidden)، بلا لون حرفي -- ترثان اللون من
  // currentColor عبر tokens الحالية (نفس أسلوب ختم وثيق في index.html).
  function folderIconSvg() {
    return (
      '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      '<path d="M3 7a1 1 0 0 1 1-1h4.5l1.5 2H20a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V7Z"/>' +
      "</svg>"
    );
  }

  function fileIconSvg() {
    return (
      '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      '<path d="M7 2h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1Z"/><path d="M14 2v5h5"/></svg>'
    );
  }

  // يقرأ فقط الحقل الموجود أصلاً evaluated_evidence[].satisfied (محسوب مسبقاً
  // من طبقة التقييم الحقيقية) -- لا يُنشئ أي قاعدة اجتياز/رسوب جديدة، فقط
  // يُجمِّع (count) ما هو موجود، تماماً كما تُحسب next_level_gaps.length في
  // بقية هذا الملف. هذا ليس "نسبة تقدّم نحو النضج" -- فقط نسبة استيفاء
  // ضمن الأدلة التي جرى تقييمها فعلاً (Evidence Coverage)، ويُعرض تحت هذا
  // الاسم صراحة لتفادي الخلط مع مستوى النضج (current_level).
  function evidenceSatisfactionStats(mq) {
    const list = mq.evaluated_evidence || [];
    const satisfied = list.filter(function (e) {
      return !!e.satisfied;
    }).length;
    const total = list.length;
    const pct = total > 0 ? Math.round((satisfied / total) * 100) : 0;
    return { satisfied: satisfied, total: total, pct: pct };
  }

  function evidencePreviewHtml(mq) {
    const list = mq.evaluated_evidence || [];
    const shown = list.slice(0, 3);
    const rest = list.length - shown.length;
    // data-satisfied يعرض فقط الحقل الموجود أصلاً (satisfied) كـ Attribute
    // قابل للاستعلام من CSS -- علامة ✓/✕ نفسها تُرسَم بالكامل عبر
    // components.css (::before content)، لا نص جديد هنا.
    let html = shown
      .map(function (e) {
        return (
          '<li data-satisfied="' +
          !!e.satisfied +
          '">' +
          fileIconSvg() +
          "<span>" +
          escapeHtml(e.evidence_code) +
          "</span></li>"
        );
      })
      .join("");
    if (rest > 0) {
      html += '<li class="wq-mq-card__evidence-more">+' + rest + "</li>";
    }
    return html;
  }

  // تصنيف نوع الدليل من بادئة evidence_code فقط -- عرض بحت، لا يُنشئ أي
  // قاعدة تقييم جديدة ولا يمس evaluated_evidence[].status أو satisfied.
  // القاعدة كما وردت حرفياً: DC.M = دليل نضج، DC.C = دليل امتثال. بلا أي
  // نوع ثالث.
  function evidenceTypeKind(evidenceCode) {
    const code = String(evidenceCode || "");
    if (code.indexOf("DC.M") === 0) return "maturity";
    if (code.indexOf("DC.C") === 0) return "compliance";
    return null;
  }

  function evidenceTypeLabel(evidenceCode) {
    const kind = evidenceTypeKind(evidenceCode);
    if (kind === "maturity") return "دليل مرتبط بالنضج";
    if (kind === "compliance") return "دليل مرتبط بالامتثال";
    return null;
  }

  function evidenceListHtml(mq) {
    return (mq.evaluated_evidence || [])
      .map(function (e) {
        const typeLabel = evidenceTypeLabel(e.evidence_code);
        return (
          '<li class="wq-evidence-item" data-evidence-code="' +
          escapeHtml(e.evidence_code) +
          '" data-mq-id="' +
          escapeHtml(mq.mq_id) +
          '">' +
          '<div class="wq-evidence-item__head">' +
          '<span class="wq-evidence-code">' +
          escapeHtml(e.evidence_code) +
          "</span>" +
          '<span class="wq-evidence-name">' +
          escapeHtml(evidenceNameDisplay(e.evidence_name)) +
          "</span>" +
          "</div>" +
          '<div class="wq-evidence-item__meta">' +
          (typeLabel
            ? '<span class="wq-evidence-item__type">' +
              '<span class="wq-evidence-item__type-label">النوع</span>' +
              '<span class="wq-evidence-item__type-value">' +
              escapeHtml(typeLabel) +
              "</span>" +
              "</span>"
            : "") +
          '<span class="wq-evidence-item__status">' +
          '<span class="wq-evidence-item__status-label">الحالة</span>' +
          '<span class="wq-status-badge" data-status="' +
          statusBadgeAttr(e.status) +
          '"><span class="wq-status-badge__dot"></span>' +
          escapeHtml(statusLabelAr(e.status)) +
          "</span>" +
          "</span>" +
          "</div>" +
          "</li>"
        );
      })
      .join("");
  }

  // "File Card" -- كل متطلب نضج يُعرض كملف/Evidence Asset بدل بطاقة KPI
  // تقليدية (طلب صريح). status الإكمال هنا مُستدعى من نفس الدالة الحقيقية
  // في recommendation_engine.js (generateRecommendation(mq).status) بدل
  // تكرار صيغة gaps.length===0 يدوياً -- مصدر واحد للحقيقة.
  function mqCardHtml(mq, domainName) {
    const gapsPreview =
      mq.next_level_gaps.length > 0
        ? mq.next_level_gaps.slice(0, 3).join("، ") +
          (mq.next_level_gaps.length > 3 ? " +" + (mq.next_level_gaps.length - 3) : "")
        : "لا توجد فجوات معلّقة";

    const recoStatus = window.WathiqRecommendationEngine.generateRecommendation(mq).status;
    const stats = evidenceSatisfactionStats(mq);

    return (
      '<article class="wq-mq-card" tabindex="0" role="button" aria-expanded="false" data-mq-id="' +
      escapeHtml(mq.mq_id) +
      '">' +
      '<div class="wq-mq-card__header">' +
      '<span class="wq-mq-card__id">' +
      escapeHtml(mq.mq_id) +
      "</span>" +
      '<span class="wq-mq-card__domain-badge">' +
      escapeHtml(domainName) +
      "</span>" +
      '<span class="wq-mq-card__status-pill" data-complete="' +
      (recoStatus === "complete") +
      '">' +
      (recoStatus === "complete" ? "مكتمل" : "قيد الاستكمال") +
      "</span>" +
      "</div>" +
      '<div class="wq-mq-card__file">' +
      '<span class="wq-mq-card__file-icon" aria-hidden="true">' +
      folderIconSvg() +
      "</span>" +
      '<p class="wq-mq-card__question">' +
      escapeHtml(mq.question) +
      "</p>" +
      "</div>" +
      '<div class="wq-mq-card__level">' +
      '<div class="wq-mq-card__level-head">' +
      '<span class="wq-mq-card__level-label">مستوى النضج</span>' +
      '<span class="wq-level-badge"><span class="wq-level-badge__num">' +
      mq.current_level +
      '</span><span class="wq-level-badge__name">' +
      escapeHtml(mq.level_name) +
      "</span></span>" +
      "</div>" +
      '<div class="wq-level-track" aria-hidden="true">' +
      levelTrackHtml(mq.current_level, mq.next_level) +
      "</div>" +
      "</div>" +
      '<div class="wq-mq-card__evidence">' +
      '<div class="wq-mq-card__evidence-label">الأدلة المرتبطة بالتقييم</div>' +
      '<ul class="wq-mq-card__evidence-preview">' +
      evidencePreviewHtml(mq) +
      "</ul>" +
      "</div>" +
      '<div class="wq-mq-card__satisfaction">' +
      '<div class="wq-mq-card__satisfaction-head">' +
      "<span>اكتمال الأدلة المرتبطة بالتقييم</span>" +
      "<span>" +
      stats.satisfied +
      " من " +
      stats.total +
      "</span>" +
      "</div>" +
      '<div class="wq-mq-card__satisfaction-track"><div class="wq-mq-card__satisfaction-fill" style="width:' +
      stats.pct +
      '%"></div></div>' +
      "</div>" +
      '<div class="wq-mq-card__row"><span>الفجوات القادمة</span><strong>' +
      mq.next_level_gaps.length +
      "</strong></div>" +
      '<div class="wq-mq-card__gaps"><strong>القادم:</strong> ' +
      escapeHtml(gapsPreview) +
      "</div>" +
      // Discoverability fix: زر "إرفاق دليل" أصبح على وجه البطاقة (داخل
      // wq-mq-card__footer)، بجانب "عرض التفاصيل" -- نسخة واحدة فقط في كل
      // البطاقة (أُزيلت النسخة التي كانت داخل Detail View). نفس data-mq-id،
      // نفس الكلاس wq-attach-evidence-btn، نفس معالج الحدث المُفوَّض في
      // renderMqCards() -- بلا أي منطق رفع جديد.
      '<div class="wq-mq-card__footer">' +
      '<button type="button" class="wq-attach-evidence-btn" data-mq-id="' +
      escapeHtml(mq.mq_id) +
      '">+ إرفاق دليل</button>' +
      '<div class="wq-mq-card__expand-hint">' +
      "<span>عرض التفاصيل →</span>" +
      '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
      '<path d="M6 9l6 6 6-6"/></svg>' +
      "</div>" +
      "</div>" +
      '<div class="wq-mq-card__detail"><div class="wq-mq-card__detail-inner">' +
      '<div class="wq-mq-card__detail-content">' +
      '<div class="wq-detail-block"><div class="wq-detail-block__label">وصف المستوى الحالي</div>' +
      '<div class="wq-detail-block__body">' +
      escapeHtml(mq.level_description) +
      "</div></div>" +
      '<div class="wq-detail-block"><div class="wq-detail-block__label">الأدلة التي تم تقييمها</div>' +
      '<ul class="wq-evidence-list">' +
      evidenceListHtml(mq) +
      "</ul></div>" +
      evidenceRepositoryBlockHtml(mq.mq_id) +
      pendingEvidenceBlockHtml(mq.mq_id) +
      "</div></div></div>" +
      "</article>"
    );
  }

  function renderMqCards(data) {
    const container = document.getElementById("wq-mq-grid");
    container.innerHTML = data.mq_results
      .map(function (mq) {
        return mqCardHtml(mq, data.domain_name);
      })
      .join("");

    container.querySelectorAll(".wq-mq-card").forEach(function (card) {
      function toggle() {
        const expanded = card.getAttribute("aria-expanded") === "true";
        card.setAttribute("aria-expanded", String(!expanded));
      }
      card.addEventListener("click", function (event) {
        if (event.target.closest("li[data-evidence-code]")) return; // handled separately
        if (event.target.closest(".wq-attach-evidence-btn")) return; // handled separately
        if (event.target.closest(".wq-evidence-open-btn")) return; // handled separately
        if (event.target.closest(".wq-evidence-export-btn")) return; // handled separately
        if (event.target.closest(".wq-export-mq-btn")) return; // handled separately
        toggle();
      });
      card.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          toggle();
        }
      });
    });

    container.querySelectorAll("li[data-evidence-code]").forEach(function (li) {
      li.addEventListener("click", function (event) {
        event.stopPropagation();
        const code = li.getAttribute("data-evidence-code");
        const mqId = li.getAttribute("data-mq-id");
        const mq = data.mq_results.find(function (m) {
          return m.mq_id === mqId;
        });
        const evidence = findEvidence(mq, code);
        openEvidenceModal(mq, evidence);
      });
    });

    container.querySelectorAll(".wq-attach-evidence-btn").forEach(function (btn) {
      btn.addEventListener("click", function (event) {
        event.stopPropagation();
        openUploadModal(btn.getAttribute("data-mq-id"));
      });
    });

    container.querySelectorAll(".wq-evidence-open-btn").forEach(function (btn) {
      btn.addEventListener("click", function (event) {
        event.stopPropagation();
        openEvidenceFile(btn.getAttribute("data-mq-id"), btn.getAttribute("data-path"));
      });
    });

    container.querySelectorAll(".wq-evidence-export-btn").forEach(function (btn) {
      btn.addEventListener("click", function (event) {
        event.stopPropagation();
        exportEvidenceFile(
          btn.getAttribute("data-mq-id"),
          btn.getAttribute("data-path"),
          btn.getAttribute("data-filename")
        );
      });
    });

    container.querySelectorAll(".wq-export-mq-btn").forEach(function (btn) {
      btn.addEventListener("click", function (event) {
        event.stopPropagation();
        exportMqEvidenceZip(btn.getAttribute("data-mq-id"));
      });
    });
  }

  /* ---------------------------------------------------------------- */
  /* Gap Identification                                                   */
  /* ---------------------------------------------------------------- */

  let activeGapFilter = "ALL";

  function allGaps(data) {
    const gaps = [];
    data.mq_results.forEach(function (mq) {
      mq.next_level_gaps.forEach(function (code) {
        const evidence = findEvidence(mq, code);
        gaps.push({
          code: code,
          mq_id: mq.mq_id,
          mq_name: mq.question,
          evidence_name: evidence ? evidence.evidence_name : null,
          // level_number موجود أصلاً على كائن evidence (evaluated_evidence[]
          // في JSON) -- يُمرَّر هنا فقط لأجل الترتيب، بلا حساب جديد.
          level_number: evidence ? evidence.level_number : null,
          next_level: mq.next_level,
          next_level_name: mq.next_level_name,
        });
      });
    });
    // ترتيب: MQ أولاً، ثم مستوى الدليل، ثم رمز الدليل -- بيانات موجودة
    // أصلاً في كل عنصر، لا قيمة مُخترَعة.
    gaps.sort(function (a, b) {
      if (a.mq_id !== b.mq_id) return a.mq_id < b.mq_id ? -1 : 1;
      if (a.level_number !== b.level_number) return (a.level_number || 0) - (b.level_number || 0);
      return a.code < b.code ? -1 : a.code > b.code ? 1 : 0;
    });
    return gaps;
  }

  function renderGapFilters(data) {
    const bar = document.getElementById("wq-gap-toolbar");
    const mqIds = data.mq_results.map(function (mq) {
      return mq.mq_id;
    });

    const buttons = ["ALL"].concat(mqIds);
    bar.innerHTML = buttons
      .map(function (id) {
        const label = id === "ALL" ? "كل المجالات الفرعية" : id;
        return (
          '<button type="button" class="wq-filter-btn" data-filter="' +
          escapeHtml(id) +
          '" aria-pressed="' +
          (id === activeGapFilter) +
          '">' +
          escapeHtml(label) +
          "</button>"
        );
      })
      .join("");

    bar.querySelectorAll(".wq-filter-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        activeGapFilter = btn.getAttribute("data-filter");
        bar.querySelectorAll(".wq-filter-btn").forEach(function (b) {
          b.setAttribute("aria-pressed", String(b === btn));
        });
        renderGapList(data);
      });
    });
  }

  function renderGapList(data) {
    const list = document.getElementById("wq-gap-list");
    const gaps = allGaps(data).filter(function (gap) {
      return activeGapFilter === "ALL" || gap.mq_id === activeGapFilter;
    });

    if (gaps.length === 0) {
      list.innerHTML = '<div class="wq-empty-state">لا توجد فجوات ضمن هذا الفلتر.</div>';
      return;
    }

    list.innerHTML = gaps
      .map(function (gap, index) {
        return (
          '<div class="wq-gap-card" style="animation-delay:' +
          index * 30 +
          'ms" data-code="' +
          escapeHtml(gap.code) +
          '" data-mq-id="' +
          escapeHtml(gap.mq_id) +
          '">' +
          '<div class="wq-gap-card__code">' +
          escapeHtml(gap.code) +
          "</div>" +
          '<div class="wq-gap-card__req">' +
          escapeHtml(evidenceNameDisplay(gap.evidence_name) || "بدون وصف متاح") +
          "</div>" +
          '<div class="wq-gap-card__mq">' +
          '<span class="wq-gap-card__mq-label">مرتبط بالمتطلب</span>' +
          '<span class="wq-gap-card__mq-value">' +
          escapeHtml(gap.mq_id) +
          "</span></div>" +
          '<div class="wq-gap-card__next">' +
          '<span class="wq-gap-card__next-label">الانتقال إلى</span>' +
          '<span class="wq-gap-card__next-value">المستوى ' +
          gap.next_level +
          " — " +
          escapeHtml(gap.next_level_name || "المستوى التالي") +
          "</span>" +
          "</div>" +
          "</div>"
        );
      })
      .join("");

    list.querySelectorAll(".wq-gap-card").forEach(function (card) {
      card.addEventListener("click", function () {
        const code = card.getAttribute("data-code");
        const mqId = card.getAttribute("data-mq-id");
        const mq = data.mq_results.find(function (m) {
          return m.mq_id === mqId;
        });
        openEvidenceModal(mq, findEvidence(mq, code), true);
      });
    });
  }

  /* ---------------------------------------------------------------- */
  /* Recommendation Engine (rendering)                                    */
  /* ---------------------------------------------------------------- */

  function renderRecommendations(data) {
    const grid = document.getElementById("wq-reco-grid");
    const recos = window.WathiqRecommendationEngine.generateRecommendations(data.mq_results);

    grid.innerHTML = recos
      .map(function (reco) {
        const cardClass = reco.status === "complete" ? "wq-reco-card--complete" : "wq-reco-card--pending";
        // "!" كانت رمزاً لكل توصية معلَّقة (Arabic Cleanup Pass) -- استُبدلت
        // بـ"…" (نفس رمز حالة "قيد الانتظار" المستخدَم أصلاً في نظام
        // wq-status-badge بالضبط، اتساقاً بدل رمز جديد) -- ما زال يميّز
        // مرئياً بين "مكتمل"(✓) و"معلّق"، بلا الاعتماد على علامة تعجب.
        const icon = reco.status === "complete" ? "✓" : "…";
        const actionsHtml =
          reco.actions.length > 0
            ? '<ul class="wq-reco-actions">' +
              reco.actions.map(function (a) {
                return "<li>" + escapeHtml(a) + "</li>";
              }).join("") +
              "</ul>"
            : "";

        // صفوف Current → Missing → Next -- كلها من حقول reco المُضافة في
        // recommendation_engine.js (current_level/level_name/next_level/
        // next_level_name/gaps)، وكلها مأخوذة أصلاً من mq.* بلا حساب جديد.
        // تُعرض فقط عندما توجد فجوة فعلية (pending) -- حالة complete ليس
        // لها "المطلوب/التالي" لتُعرض أصلاً.
        const levelsHtml =
          reco.status === "pending"
            ? '<div class="wq-reco-card__levels">' +
              '<div class="wq-reco-card__level-row">' +
              '<span class="wq-reco-card__level-label">المستوى الحالي</span>' +
              '<span class="wq-reco-card__level-value">' +
              reco.current_level +
              " — " +
              escapeHtml(reco.level_name) +
              "</span></div>" +
              '<div class="wq-reco-card__level-row wq-reco-card__level-row--next">' +
              '<span class="wq-reco-card__level-label">للوصول إلى</span>' +
              '<span class="wq-reco-card__level-value">' +
              reco.next_level +
              " — " +
              escapeHtml(reco.next_level_name || "المستوى التالي") +
              "</span></div>" +
              "</div>" +
              '<div class="wq-reco-card__missing">' +
              '<span class="wq-reco-card__missing-label">المطلوب</span>' +
              '<span class="wq-reco-card__missing-value">استكمال ' +
              escapeHtml(reco.gaps.join("، ")) +
              "</span></div>"
            : "";

        // ترتيب العرض: العنوان (What) -> "لماذا" مُعنوَنة صراحة (Why، كانت
        // فقرة بلا تسمية) -> المستوى الحالي/التالي + المطلوب (Missing) ->
        // الإجراءات (Action) -- يطابق التسلسل المطلوب What->Why->Missing->
        // Action بدل الترتيب السابق (المستويات قبل العنوان). لا تغيير على
        // reco.title/body/gaps نفسها -- إعادة ترتيب العرض فقط.
        return (
          '<div class="wq-reco-card ' +
          cardClass +
          '">' +
          '<div class="wq-reco-card__head"><span class="wq-reco-card__icon">' +
          icon +
          '</span><span class="wq-reco-card__mq">' +
          escapeHtml(reco.mq_id) +
          "</span></div>" +
          '<h3 class="wq-reco-card__title">' +
          escapeHtml(reco.title) +
          "</h3>" +
          (reco.status === "pending" ? '<div class="wq-reco-card__why-label">لماذا؟</div>' : "") +
          '<p class="wq-reco-card__body">' +
          escapeHtml(reco.body) +
          "</p>" +
          levelsHtml +
          actionsHtml +
          "</div>"
        );
      })
      .join("");
  }

  /* ---------------------------------------------------------------- */
  /* Compliance (قياس الامتثال) -- طبقة عرض مستقلة تماماً عن Maturity      */
  /* ---------------------------------------------------------------- */

  // مصدر منفصل تماماً عن MATURITY_DATA_URL أعلاه: لا يُقرأ من sample_
  // maturity_report.json ولا يُغذّي current_level/next_level_gaps بأي شكل.
  // كل مواصفة هنا 100% (ممتثل) أو 0% (غير ممتثل) فقط -- وفق صفحة 14 من
  // المحتوى التدريبي لمؤشر نضيء (نص حرفي: "0% غير ممتثل للمواصفات التي
  // طبقت بشكل جزئي أو لم تطبق على الإطلاق / 100% ممتثل للمواصفات المطبقة
  // بشكل كامل"). لا وزن، لا Final Score، لا علاقة بمستوى النضج.
  const COMPLIANCE_DATA_URL = "data/compliance_models/DC_compliance.json";

  function loadComplianceData() {
    return fetch(COMPLIANCE_DATA_URL)
      .then(function (response) {
        return response.ok ? response.json() : null;
      })
      .catch(function () {
        return null;
      });
  }

  // Compliance % = (sum of specification scores) / (number of specifications)
  // -- بالضبط كما ورد، بلا أي وزن مُضاف. يقرأ فقط compliance_score الموجود
  // أصلاً على كل مواصفة في DC_compliance.json؛ لا يحسب درجة مواصفة جديدة.
  function complianceStats(complianceData) {
    const specs = (complianceData && complianceData.specifications) || [];
    const total = specs.length;
    const compliant = specs.filter(function (s) {
      return s.compliance_status === "COMPLIANT";
    }).length;
    const scoreSum = specs.reduce(function (sum, s) {
      return sum + (typeof s.compliance_score === "number" ? s.compliance_score : 0);
    }, 0);
    return {
      total: total,
      compliant: compliant,
      nonCompliant: total - compliant,
      pct: total > 0 ? Math.round(scoreSum / total) : 0,
    };
  }

  // عرض فقط -- بلا تعديل على DC_compliance.json. عندما لا يتوفر اسم وصفي
  // حقيقي للمواصفة في المصدر (الحالة الوحيدة الحالية: specification_name
  // مطابق حرفياً لـ specification_code، مثل DC.C.4.1)، يُستبدَل بنص واضح
  // بدل تكرار الرمز نفسه كاسم. الحالة/الارتباط/النتيجة (compliance_status/
  // linked_mq/compliance_score) تُقرأ كما هي بلا أي تغيير.
  function complianceSpecDisplayName(spec) {
    return spec.specification_name === spec.specification_code
      ? "اسم المواصفة غير متوفر في المصدر الحالي"
      : evidenceNameDisplay(spec.specification_name);
  }

  function complianceItemHtml(spec) {
    const isCompliant = spec.compliance_status === "COMPLIANT";
    return (
      '<li class="wq-compliance-item">' +
      '<div class="wq-compliance-item__main">' +
      '<span class="wq-compliance-item__code">' +
      escapeHtml(spec.specification_code) +
      "</span>" +
      '<span class="wq-compliance-item__name">' +
      escapeHtml(complianceSpecDisplayName(spec)) +
      "</span>" +
      "</div>" +
      '<div class="wq-compliance-item__meta">' +
      '<span class="wq-compliance-item__mq">مرتبط: ' +
      escapeHtml(spec.linked_mq) +
      "</span>" +
      '<span class="wq-status-badge" data-status="' +
      (isCompliant ? "pass" : "fail") +
      '"><span class="wq-status-badge__dot"></span>' +
      (isCompliant ? "ممتثل" : "غير ممتثل") +
      "</span>" +
      "</div>" +
      "</li>"
    );
  }

  function renderCompliance(complianceData) {
    const specs = (complianceData && complianceData.specifications) || [];
    const stats = complianceStats(complianceData);

    document.getElementById("wq-compliance-total").textContent = stats.total;
    document.getElementById("wq-compliance-compliant").textContent = stats.compliant;
    document.getElementById("wq-compliance-noncompliant").textContent = stats.nonCompliant;
    document.getElementById("wq-compliance-score").textContent =
      stats.total > 0 ? stats.pct + "%" : "—";

    const list = document.getElementById("wq-compliance-list");
    if (specs.length === 0) {
      list.innerHTML = '<div class="wq-empty-state">تعذّر تحميل بيانات الامتثال.</div>';
      return;
    }
    list.innerHTML = specs.map(complianceItemHtml).join("");
  }

  /* ---------------------------------------------------------------- */
  /* Operational Excellence -- Simulation فقط (بيانات تجريبية)             */
  /* ---------------------------------------------------------------- */

  // مصدر منفصل تماماً عن sample_maturity_report.json وDC_compliance.json
  // وevidence_repository_catalog.json -- لا يقرأ من أي منها ولا يكتب إليها.
  // كل الدوال أدناه (opexStats/renderOperationalExcellence) تقرأ فقط شكل
  // indicators[] (id/name/value/level) -- بلا افتراض أنه ملف JSON ساكن.
  const OPERATIONAL_EXCELLENCE_DATA_URL = "data/operational_excellence_simulation.json";

  // Future sources:
  // API
  // SQL
  // Data Platform
  // SharePoint
  const OPERATIONAL_EXCELLENCE_SOURCE = "SIMULATION";

  // Data Provider abstraction -- نقطة الاستدعاء الوحيدة لبيانات Operational
  // Excellence من بقية الملف (renderOperationalExcellence() وboot أدناه).
  // استبدال المصدر مستقبلاً (أي من القيم في تعليق OPERATIONAL_EXCELLENCE_
  // SOURCE أعلاه) يعني تغيير *جسم* هذه الدالة فقط -- بلا أي تعديل على
  // renderOperationalExcellence() أو نقطة الاستدعاء في boot، طالما البيانات
  // المُعادة تحافظ على نفس الشكل (indicators[] بالحقول id/name/value/level
  // + data_type/data_source_label/connection_status).
  function getOperationalExcellenceData() {
    // التنفيذ الحالي (OPERATIONAL_EXCELLENCE_SOURCE = "SIMULATION"): قراءة
    // من ملف JSON ساكن فقط -- بلا أي تغيير عن السلوك السابق.
    return fetch(OPERATIONAL_EXCELLENCE_DATA_URL)
      .then(function (response) {
        return response.ok ? response.json() : null;
      })
      .catch(function () {
        return null;
      });
  }

  // Operational Excellence Score = متوسط قيمة (value) كل المؤشرات ضمن
  // indicators[] -- على مستوى هذا القسم فقط. بلا وزن، بلا صيغة 70/20/10،
  // وبلا أي دمج مع Maturity أو Compliance أو Final/Overall Score لمنصة نضيء
  // ككل.
  function opexStats(opexData) {
    const indicators = (opexData && opexData.indicators) || [];
    const sum = indicators.reduce(function (total, i) {
      return total + (typeof i.value === "number" ? i.value : 0);
    }, 0);
    return {
      count: indicators.length,
      score: indicators.length > 0 ? Math.round(sum / indicators.length) : null,
    };
  }

  // كانت القيمة والمستوى على نفس السطر متلاصقين بلا تراتبية (Arabic
  // Cleanup Pass) -- أصبحت الآن: اسم المؤشر (Label) -> الرقم (العنصر
  // الأكبر) -> "المستوى: X" (Secondary، شارة صغيرة أسفل الرقم). لا تغيير
  // على أي قيمة بيانات.
  function opexIndicatorItemHtml(indicator) {
    return (
      '<li class="wq-opex-item">' +
      '<span class="wq-opex-item__name">' +
      escapeHtml(indicator.name) +
      "</span>" +
      '<span class="wq-opex-item__value">' +
      escapeHtml(String(indicator.value) + "%") +
      "</span>" +
      '<span class="wq-opex-item__level">' +
      escapeHtml("المستوى: " + indicator.level) +
      "</span>" +
      "</li>"
    );
  }

  function renderOperationalExcellence(opexData) {
    const indicators = (opexData && opexData.indicators) || [];
    const stats = opexStats(opexData);

    const scoreEl = document.getElementById("wq-opex-score");
    const countEl = document.getElementById("wq-opex-count");
    const statusEl = document.getElementById("wq-opex-status");
    const dataSourceEl = document.getElementById("wq-opex-data-source");
    const connectionStatusEl = document.getElementById("wq-opex-connection-status");
    const disclaimerEl = document.getElementById("wq-opex-disclaimer");
    const listEl = document.getElementById("wq-opex-list");

    if (indicators.length === 0) {
      scoreEl.textContent = "—";
      countEl.textContent = "—";
      statusEl.textContent = "غير متاح";
      dataSourceEl.textContent = "—";
      connectionStatusEl.textContent = "—";
      disclaimerEl.textContent = "";
      listEl.innerHTML = '<div class="wq-empty-state">تعذّر تحميل بيانات محاكاة التميز التشغيلي.</div>';
      return;
    }

    scoreEl.textContent = stats.score !== null ? stats.score + "%" : "—";
    countEl.textContent = String(stats.count);
    statusEl.textContent = opexData.data_type === "SIMULATION" ? "محاكاة نشطة" : "متاح";
    // نفس أسلوب disclaimerEl أدناه بالضبط (Arabic Cleanup Pass): الحقل
    // الخام opexData.data_source_label بالإنجليزية حرفياً في المصدر
    // ("Simulation Data (Prototype)") -- المصدر ممنوع لمسه، فتُرجَم القيمة
    // المعروضة في طبقة الواجهة فقط لقيمة SIMULATION المعروفة تحديداً؛ أي
    // قيمة أخرى مستقبلية تُعرض كما هي (بلا اختراع ترجمة لشيء غير معروف).
    dataSourceEl.textContent =
      opexData.data_source_label === "Simulation Data (Prototype)"
        ? "بيانات محاكاة — نموذج أولي"
        : opexData.data_source_label || "—";
    connectionStatusEl.textContent = opexData.connection_status || "—";
    // نص العرض ثابت في JS عمداً (وليس opexData.disclaimer) -- تعديل نص
    // التنبيه هذه الجولة ممنوع أن يمرّ عبر تعديل operational_excellence_
    // simulation.json (مصادر البيانات JSON ممنوع لمسها)، فبقي الحقل كما هو
    // في الملف وانتقل نص العرض إلى طبقة الواجهة فقط، بنفس أسلوب Badge/
    // العنوان/الوصف أعلاه (نصوص واجهة ثابتة، لا تُقرأ من الملف).
    disclaimerEl.textContent =
      "هذه بيانات محاكاة لغرض عرض النموذج الأولي فقط، وليست بيانات تشغيلية فعلية أو مرتبطة بأي جهة خارجية.";
    listEl.innerHTML = indicators.map(opexIndicatorItemHtml).join("");
  }

  /* ---------------------------------------------------------------- */
  /* Compliance -- قسم مستقل بالكامل (حقن بلا لمس index.html)             */
  /* ---------------------------------------------------------------- */

  // إعادة ترتيب (User Journey Restructuring Pass) ثم إعادة تنظيم كـView
  // مستقلة (Sidebar Navigation Pass): كانت تُدرَج قبل "بطاقات نضج
  // المتطلبات" مباشرة وبعد Overview، فتقاطع الرحلة الأساسية بقسمين
  // منفصلين تماماً عن حساب النضج (Compliance/Operational Excellence
  // كلاهما "قيد الإعداد" ومصرَّح عنهما في تعليقاتهما الخاصة كطبقتين
  // مستقلتين). موضع الإدراج (afterend #recommendations) لم يعد يحدّد
  // الترتيب البصري بما أن showView() في js/app.js يعرض View واحدة فقط في
  // كل مرة -- لكنه ما زال يحدّد ترتيب DOM اللازم لتسلسل الاعتماد
  // (injectOperationalExcellenceSection() يعتمد على وجود #compliance).
  // wq-tier-divider (الفاصل البصري بين الرحلة الأساسية ومعلومات إضافية،
  // من الجولة السابقة) أُزيل من هنا لأنه أصبح بلا معنى ضمن View مستقلة
  // بمفردها -- تجميع "معلومات إضافية" أصبح مسؤولية Sidebar (مجموعة
  // Navigation منفصلة) لا مسؤولية عنصر داخل الصفحة. لا تغيير على
  // renderCompliance() أو البيانات.
  function injectComplianceSection() {
    const anchor = document.getElementById("recommendations");
    const html =
      '<section class="wq-section wq-section--supplementary" id="compliance" aria-labelledby="compliance-title">' +
      '<div class="wq-section__head">' +
      "<div>" +
      '<h2 class="wq-section__title" id="compliance-title">قياس الامتثال</h2>' +
      '<p class="wq-section__hint">التزام الجهة بمواصفات إدارة البيانات الوطنية — كل مواصفة 100% ممتثل أو 0% غير ممتثل، بمعزل تام عن مستوى النضج.</p>' +
      "</div>" +
      "</div>" +
      // شبكة 2×2 صريحة (Arabic Cleanup Pass) بدل wq-overview-grid المرنة
      // -- كانت تنتج أحياناً 3 بطاقات في صف + بطاقة منفردة في الصف التالي.
      '<div class="wq-kpi-grid--2x2">' +
      '<div class="wq-stat"><div class="wq-stat__label">إجمالي المواصفات</div><div class="wq-stat__value" id="wq-compliance-total">—</div></div>' +
      '<div class="wq-stat wq-stat--compliance"><div class="wq-stat__label">نسبة الامتثال</div><div class="wq-stat__value" id="wq-compliance-score">—</div></div>' +
      '<div class="wq-stat"><div class="wq-stat__label">ممتثل</div><div class="wq-stat__value" id="wq-compliance-compliant">—</div></div>' +
      '<div class="wq-stat"><div class="wq-stat__label">غير ممتثل</div><div class="wq-stat__value" id="wq-compliance-noncompliant">—</div></div>' +
      "</div>" +
      '<ul class="wq-compliance-list" id="wq-compliance-list"></ul>' +
      "</section>";
    anchor.insertAdjacentHTML("afterend", html);
  }

  /* ---------------------------------------------------------------- */
  /* Operational Excellence -- قسم مستقل بالكامل، عنوان وحاوية منفصلان تماماً
     عن Compliance (لا مشاركة أي عنصر/حاوية). يعرض بيانات Simulation من
     OPERATIONAL_EXCELLENCE_DATA_URL حصراً -- بمعزل تام عن حساب الامتثال
     وبطاقات النضج والتوصيات. renderOperationalExcellence() (أعلاه) يملأ
     العناصر التي تبنيها هذه الدالة بعد التحميل، عبر معرّفاتها فقط.        */
  /* ---------------------------------------------------------------- */
  // إعادة ترتيب (User Journey Restructuring Pass): تُدرَج الآن بعد Compliance
  // مباشرة (نفس مجموعة "معلومات إضافية" -- بلا فاصل ثانٍ) بدل قبل MQ Cards.
  // انظر تعليق injectComplianceSection() أعلاه للسبب الكامل.
  function injectOperationalExcellenceSection() {
    const anchor = document.getElementById("compliance");
    const html =
      '<section class="wq-section wq-section--supplementary" id="operational-excellence" aria-labelledby="opex-title">' +
      '<div class="wq-section__head">' +
      "<div>" +
      '<h2 class="wq-section__title" id="opex-title">قياس التميز التشغيلي</h2>' +
      '<p class="wq-section__hint">يقيس مؤشرات الأداء التشغيلي المرتبطة بإدارة البيانات اعتماداً على مصادر البيانات التشغيلية المتاحة.</p>' +
      "</div>" +
      "</div>" +
      '<div class="wq-opex-card">' +
      '<div class="wq-opex-badge-row">' +
      '<span class="wq-opex-badge">بيانات محاكاة</span>' +
      "</div>" +
      // 3 أعمدة صريحة (Arabic Cleanup Pass) بدل wq-overview-grid المرنة.
      '<div class="wq-kpi-grid--3">' +
      '<div class="wq-stat wq-stat--compliance"><div class="wq-stat__label">مؤشر التميز التشغيلي</div><div class="wq-stat__value" id="wq-opex-score">—</div></div>' +
      '<div class="wq-stat"><div class="wq-stat__label">عدد المؤشرات</div><div class="wq-stat__value" id="wq-opex-count">—</div></div>' +
      '<div class="wq-stat"><div class="wq-stat__label">حالة المؤشرات</div><div class="wq-stat__value" id="wq-opex-status">—</div></div>' +
      "</div>" +
      '<div class="wq-opex-meta">' +
      '<div class="wq-opex-meta__row">' +
      '<span class="wq-opex-meta__label">مصدر البيانات</span>' +
      '<span class="wq-opex-meta__value" id="wq-opex-data-source">—</span>' +
      "</div>" +
      '<div class="wq-opex-meta__row">' +
      '<span class="wq-opex-meta__label">حالة الربط</span>' +
      '<span class="wq-opex-meta__value" id="wq-opex-connection-status">—</span>' +
      "</div>" +
      "</div>" +
      '<p class="wq-opex-disclaimer" id="wq-opex-disclaimer"></p>' +
      '<ul class="wq-opex-list" id="wq-opex-list"></ul>' +
      "</div>" +
      "</section>";
    anchor.insertAdjacentHTML("afterend", html);
  }

  /* ---------------------------------------------------------------- */
  /* Evidence Repository -- عرض ومتابعة فقط، بلا أي محرك تقييم جديد        */
  /* ---------------------------------------------------------------- */

  // يبني قائمة أدلة موحّدة بدمج قراءة فقط (بلا أي كتابة) من ثلاثة مصادر
  // محمَّلة أصلاً في هذا الملف:
  //  1) evidence_repository_catalog.json (evidenceCatalogState) -- القائمة
  //     الأساس: كل ملف دليل موجود فعلياً لمجال DC (23 عنصراً)، وترتيبها.
  //  2) sample_maturity_report.json (data.mq_results[].evaluated_evidence)
  //     -- يُغني كل عنصر مطابق الرمز باسمه ومستواه وحالته الحقيقية كما هي،
  //     بلا أي إعادة حساب.
  //  3) DC_compliance.json (عبر complianceState/findComplianceSpec أعلاه)
  //     -- لأدلة الامتثال (DC.C) فقط: يُفضَّل compliance_status الجاهز على
  //     حالة evaluated_evidence عند توفره، بنفس منطق evidenceDetailStatusLabel
  //     في نافذة تفاصيل الدليل تماماً -- بحث فقط، لا حساب جديد.
  // أي عنصر في الكتالوج بلا مطابقة في أي من المصدرين الآخرين (5 عناصر
  // حالياً: DC.M.3/M.4/M.9/M.13 وDC.C.4.1 قبل مطابقة الامتثال) يُعرض صراحة
  // "غير متوفر"/"غير مُقيّم في المصدر الحالي" بدل اختراع اسم أو حالة.
  function buildEvidenceRepositoryItems(data, catalog) {
    const evaluatedByCode = {};
    (data.mq_results || []).forEach(function (mq) {
      (mq.evaluated_evidence || []).forEach(function (e) {
        evaluatedByCode[e.evidence_code] = e;
      });
    });

    return (catalog || []).map(function (item) {
      const code = item.evidence_code;
      const kind = evidenceTypeKind(code);
      const evaluated = evaluatedByCode[code];
      const spec = kind === "compliance" ? findComplianceSpec(code) : null;

      let statusLabel;
      let statusBadge;
      if (spec) {
        statusLabel = spec.compliance_status === "COMPLIANT" ? "ممتثل" : "غير ممتثل";
        statusBadge = spec.compliance_status === "COMPLIANT" ? "pass" : "fail";
      } else if (evaluated) {
        statusLabel = statusLabelAr(evaluated.status);
        statusBadge = statusBadgeAttr(evaluated.status);
      } else {
        statusLabel = "غير مُقيّم في المصدر الحالي";
        statusBadge = "pending";
      }

      return {
        evidence_code: code,
        evidence_name: evaluated ? evaluated.evidence_name : null,
        mq_id: item.mq_id,
        // مستوى النضج المرتبط -- من evaluated_evidence.level_number فقط
        // (لأي نوع دليل، M أو C -- أدلة الامتثال تحمل level_number أيضاً في
        // sample_maturity_report.json). لا قيمة لهذا الحقل لعناصر الكتالوج
        // غير المُقيَّمة -- يُعرض "غير متوفر في المصدر الحالي" عندها بدل
        // اختراع مستوى.
        level_number: evaluated ? evaluated.level_number : null,
        type_label: evidenceTypeLabel(code),
        type_kind: kind,
        status_label: statusLabel,
        status_badge: statusBadge,
        // القيمة الخام (PASS/FAIL/…) كما وردت في evaluated_evidence.status،
        // أو null لعناصر الكتالوج غير المُقيَّمة -- تُمرَّر لاحقاً بلا تغيير
        // إلى نافذة تفاصيل الدليل عند الفتح من هذا القسم (انظر معالج
        // النقر في renderEvidenceRepository) بدل إعادة اشتقاق الحالة.
        raw_status: evaluated ? evaluated.status : null,
      };
    });
  }

  // إحصاءات عدّ بحتة (بلا أي نسبة أو Score) -- تُطابق تماماً ما يُعرض أصلاً
  // في قسم Compliance (6 ممتثل / 4 غير ممتثل) لأن المصدر نفسه.
  function evidenceRepositoryStats(items) {
    function countByLabel(label) {
      return items.filter(function (i) {
        return i.status_label === label;
      }).length;
    }
    return {
      total: items.length,
      maturityCount: items.filter(function (i) {
        return i.type_kind === "maturity";
      }).length,
      complianceCount: items.filter(function (i) {
        return i.type_kind === "compliance";
      }).length,
      satisfied: countByLabel("مستوفى"),
      notSatisfied: countByLabel("غير مستوفى"),
      compliant: countByLabel("ممتثل"),
      nonCompliant: countByLabel("غير ممتثل"),
    };
  }

  function evRepoStatusRowHtml(label, count) {
    return (
      '<div class="wq-evrepo-status-row">' +
      '<span class="wq-evrepo-status-row__label">' +
      escapeHtml(label) +
      "</span>" +
      '<span class="wq-evrepo-status-row__value">' +
      count +
      "</span>" +
      "</div>"
    );
  }

  // رسالة غياب الاسم تختلف حسب نوع الدليل -- "اسم المواصفة..." لأدلة
  // الامتثال (نفس المصطلح المستخدَم أصلاً في complianceSpecDisplayName()
  // لقسم Compliance)، و"اسم الدليل..." لأدلة النضج -- بدل مصطلح واحد عام.
  function evidenceRepositoryNameFallback(item) {
    return item.type_kind === "compliance"
      ? "اسم المواصفة غير متوفر في المصدر الحالي"
      : "اسم الدليل غير متوفر في المصدر الحالي";
  }

  // حقل "المتطلب المرتبط" حُذف من كل صف (Final Senior UX Audit): القائمة
  // المسطّحة (23 صفاً) أصبحت الآن مجمَّعة حسب المتطلب عبر
  // evidenceRepositoryGroupedHtml() أدناه، وعنوان المجموعة يذكر MQ ID مرة
  // واحدة بدل تكراره في كل صف تحته. لا تغيير على أي حقل بيانات آخر ولا
  // على منطق فتح الـModal (data-mq-id على <li> ما زال موجوداً كما هو).
  // إعادة تنظيم Hierarchy (Arabic Cleanup Pass): الكود والاسم كانا على نفس
  // السطر (baseline)، وحقول Label/Value الثلاثة (النوع/المستوى/الحالة)
  // متلاصقة أفقياً بفارق 5px فقط -- تُقرأ كنص متصل واحد. أصبح الآن: الكود
  // على سطره الخاص، الاسم تحته على سطر مستقل، ثم صف حقول Label أعلى/Value
  // أسفل (Stacked) لكل حقل بما فيها الحالة (بدل خلطها بين الحقول). لا
  // تغيير على أي بيانات -- عرض فقط.
  function evidenceRepositoryItemHtml(item) {
    const levelDisplay =
      typeof item.level_number === "number" ? "مستوى " + item.level_number : "غير متوفر في المصدر الحالي";
    return (
      '<li class="wq-evrepo-item" data-evidence-code="' +
      escapeHtml(item.evidence_code) +
      '" data-mq-id="' +
      escapeHtml(item.mq_id) +
      '" tabindex="0" role="button">' +
      '<div class="wq-evrepo-item__main">' +
      '<span class="wq-evrepo-item__code">' +
      escapeHtml(item.evidence_code) +
      "</span>" +
      '<span class="wq-evrepo-item__name">' +
      escapeHtml(evidenceNameDisplay(item.evidence_name) || evidenceRepositoryNameFallback(item)) +
      "</span>" +
      "</div>" +
      '<div class="wq-evrepo-item__meta">' +
      (item.type_label
        ? '<span class="wq-evrepo-item__field"><span class="wq-evrepo-item__field-label">النوع</span>' +
          '<span class="wq-evrepo-item__field-value">' +
          escapeHtml(item.type_label) +
          "</span></span>"
        : "") +
      '<span class="wq-evrepo-item__field"><span class="wq-evrepo-item__field-label">مستوى النضج المرتبط</span>' +
      '<span class="wq-evrepo-item__field-value">' +
      escapeHtml(levelDisplay) +
      "</span></span>" +
      '<span class="wq-evrepo-item__field"><span class="wq-evrepo-item__field-label">الحالة</span>' +
      '<span class="wq-status-badge" data-status="' +
      item.status_badge +
      '"><span class="wq-status-badge__dot"></span>' +
      escapeHtml(item.status_label) +
      "</span></span>" +
      "</div>" +
      "</li>"
    );
  }

  // تجميع القائمة المسطّحة (23 عنصراً في هذا النموذج) حسب المتطلب (MQ)
  // -- كل عنصر يحمل mq_id أصلاً (نفس الحقل الذي كان يُعرض سابقاً كسطر
  // "المتطلب المرتبط" داخل كل صف على حدة، 23 مرة متكررة). هذا تجميع عرض
  // بحت لبيانات مُحمَّلة أصلاً عبر buildEvidenceRepositoryItems() -- بلا
  // حساب جديد وبلا حقل جديد وبلا تغيير على evidenceRepositoryItemHtml()
  // الفردية (Final Senior UX Audit، أولوية Reorder/Simplify قبل Add).
  // ترتيب المجموعات يتبع ترتيب data.mq_results (نفس ترتيب صفحة "متطلبات
  // النضج")، ثم أي mq_id إضافي غير موجود هناك (احتياط، لا يُفترض حدوثه).
  function evidenceRepositoryGroupedHtml(items, mqResults) {
    const groups = {};
    const groupOrder = [];
    items.forEach(function (item) {
      if (!groups[item.mq_id]) {
        groups[item.mq_id] = [];
        groupOrder.push(item.mq_id);
      }
      groups[item.mq_id].push(item);
    });
    const canonicalOrder = mqResults
      .map(function (mq) {
        return mq.mq_id;
      })
      .filter(function (id) {
        return groups[id];
      });
    const remaining = groupOrder.filter(function (id) {
      return canonicalOrder.indexOf(id) === -1;
    });
    const orderedIds = canonicalOrder.concat(remaining);

    return orderedIds
      .map(function (mqId) {
        const groupItems = groups[mqId];
        const mq = mqResults.find(function (m) {
          return m.mq_id === mqId;
        });
        return (
          '<li class="wq-evrepo-group-header">' +
          '<span class="wq-evrepo-group-header__id">' +
          escapeHtml(mqId) +
          "</span>" +
          (mq && mq.question
            ? '<span class="wq-evrepo-group-header__question">' + escapeHtml(mq.question) + "</span>"
            : "") +
          '<span class="wq-evrepo-group-header__count">' +
          groupItems.length +
          (groupItems.length === 1 ? " دليل" : " أدلة") +
          "</span>" +
          "</li>" +
          groupItems.map(evidenceRepositoryItemHtml).join("")
        );
      })
      .join("");
  }

  function renderEvidenceRepository(data) {
    const items = buildEvidenceRepositoryItems(data, evidenceCatalogState);
    const stats = evidenceRepositoryStats(items);

    document.getElementById("wq-evrepo-total").textContent = stats.total;
    document.getElementById("wq-evrepo-maturity-count").textContent = stats.maturityCount;
    document.getElementById("wq-evrepo-compliance-count").textContent = stats.complianceCount;

    document.getElementById("wq-evrepo-status-breakdown").innerHTML =
      evRepoStatusRowHtml("مستوفى", stats.satisfied) +
      evRepoStatusRowHtml("غير مستوفى", stats.notSatisfied) +
      evRepoStatusRowHtml("ممتثل", stats.compliant) +
      evRepoStatusRowHtml("غير ممتثل", stats.nonCompliant);

    const list = document.getElementById("wq-evrepo-list");
    if (items.length === 0) {
      list.innerHTML = '<div class="wq-empty-state">لا تتوفر بيانات أدلة لهذا المجال.</div>';
      return;
    }
    list.innerHTML = evidenceRepositoryGroupedHtml(items, data.mq_results || []);

    // فتح نفس Evidence Detail Modal المستخدَم أصلاً من بطاقات MQ (نفس
    // openEvidenceModal بلا أي تعديل على توقيعها) -- يبني كائن "evidence"
    // من حقول العنصر الموحَّد نفسها (evidence_name/level_number/raw_status)
    // بلا أي حساب جديد، ويبحث عن كائن الـ MQ المطابق من data.mq_results
    // للحصول على question المستخدَم في سطر "المتطلب المرتبط".
    list.querySelectorAll("li[data-evidence-code]").forEach(function (li) {
      function open() {
        const code = li.getAttribute("data-evidence-code");
        const mqId = li.getAttribute("data-mq-id");
        const item = items.find(function (i) {
          return i.evidence_code === code;
        });
        const mq =
          (data.mq_results || []).find(function (m) {
            return m.mq_id === mqId;
          }) || { mq_id: mqId, question: "" };
        const evidenceLike = {
          evidence_code: item.evidence_code,
          evidence_name: item.evidence_name,
          level_number: item.level_number,
          status: item.raw_status,
        };
        openEvidenceModal(mq, evidenceLike);
      }
      li.addEventListener("click", open);
      li.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          open();
        }
      });
    });
  }

  // نفس أسلوب حقن الأقسام أعلاه -- بلا لمس index.html.
  // إعادة ترتيب (User Journey Restructuring Pass): كانت تُدرَج قبل MQ Cards
  // (قبل معرفة نتيجة النضج). الرحلة المطلوبة الآن: Overview(الوضع الحالي)
  // -> MQ Cards(النضج ولماذا) -> Evidence Repository + Visual Evidence
  // Repository(الأدلة التي تثبت النتيجة) -> Gaps -> Recommendations؛
  // Compliance/Operational Excellence انتقلا لمجموعة "معلومات إضافية" بعد
  // نهاية الرحلة (انظر injectComplianceSection()). تُدرَج الآن بعد MQ Cards
  // مباشرة، بلا أي تغيير على renderEvidenceRepository() أو البيانات.
  function injectEvidenceRepositorySection() {
    const anchor = document.getElementById("mq-cards");
    const html =
      '<section class="wq-section" id="evidence-repository" aria-labelledby="evrepo-title">' +
      '<div class="wq-section__head">' +
      "<div>" +
      // مُميِّز عن "مستودع الأدلة المرئية" أدناه -- هذا القسم يعرض تحديداً
      // نتيجة evaluated_evidence الرسمية (PASS/FAIL) لا فهرس البيانات
      // الوصفية القابل للفلترة (ذلك في القسم المرئي). بلا أي تغيير على
      // البيانات نفسها -- توضيح نصي فقط.
      '<p class="wq-section__kicker">نتائج التقييم الرسمي</p>' +
      '<h2 class="wq-section__title" id="evrepo-title">مستودع الأدلة</h2>' +
      '<p class="wq-section__hint">عرض جميع الأدلة المرتبطة بمجال تصنيف البيانات مع حالة التقييم والمتطلب المرتبط بها.</p>' +
      "</div>" +
      "</div>" +
      '<div class="wq-overview-grid">' +
      '<div class="wq-stat"><div class="wq-stat__label">إجمالي الأدلة</div><div class="wq-stat__value" id="wq-evrepo-total">—</div></div>' +
      '<div class="wq-stat"><div class="wq-stat__label">أدلة النضج</div><div class="wq-stat__value" id="wq-evrepo-maturity-count">—</div></div>' +
      '<div class="wq-stat"><div class="wq-stat__label">أدلة الامتثال</div><div class="wq-stat__value" id="wq-evrepo-compliance-count">—</div></div>' +
      '<div class="wq-stat">' +
      '<div class="wq-stat__label">حالة الأدلة</div>' +
      '<div class="wq-evrepo-status-breakdown" id="wq-evrepo-status-breakdown"></div>' +
      "</div>" +
      "</div>" +
      '<ul class="wq-evrepo-list" id="wq-evrepo-list"></ul>' +
      "</section>";
    anchor.insertAdjacentHTML("afterend", html);
  }

  /* ---------------------------------------------------------------- */
  /* Evidence Upload (Prototype) -- منفصل تماماً عن تقييم النضج            */
  /* ---------------------------------------------------------------- */

  // ملاحظة معمارية إلزامية: هذه لوحة Static بلا Backend -- لا توجد أي وسيلة
  // من المتصفح لكتابة data/uploaded_evidence.json فعلياً على القرص. ذلك
  // الملف بذرة أولية فقط (مصفوفة فارغة ابتداءً). الحالة الفعلية أثناء
  // الاستخدام تُبنى في الذاكرة وتُحفَظ في localStorage (لنفس المتصفح/الجهاز
  // فقط) لتبقى بعد إعادة تحميل الصفحة -- وليست قاعدة بيانات مشتركة حقيقية.
  // لا يُخزَّن محتوى الملف نفسه (bytes) في أي مكان، فقط بيانات وصفية (Name/
  // Linked MQ/Date/Status) مطابقة تماماً للمخطط المطلوب. لا علاقة إطلاقاً
  // بـ evaluated_evidence أو current_level أو next_level_gaps -- المسار
  // الصحيح (Upload → Evidence Repository → Assessment → PASS/FAIL →
  // Maturity Calculation) يتوقف هنا عمداً عند "Evidence Repository".
  const UPLOADED_EVIDENCE_URL = "data/uploaded_evidence.json";
  const UPLOADED_EVIDENCE_STORAGE_KEY = "wathiq-uploaded-evidence";
  const ALLOWED_EVIDENCE_EXTENSIONS = ["pdf", "docx", "xlsx", "png", "jpg", "jpeg"];

  // Evidence Lifecycle Hardening -- الحالات الثلاث المسموحة فقط لسجل رفع.
  // لا يوجد أي مسار في هذا الملف يُغيّر حالة سجل إلى APPROVED/REJECTED
  // فعلياً بعد -- المراجعة الفعلية غير مُنفَّذة عمداً هذه الجولة. هذا
  // الثابت + دالتا العرض أدناه يُجهّزان العرض فقط ليعمل صحيحاً في اللحظة
  // التي تُضاف فيها آلية مراجعة حقيقية لاحقاً (خارج نطاق اليوم)، بلا حاجة
  // لتعديل طريقة العرض حينها.
  const EVIDENCE_STATUS = {
    PENDING_REVIEW: "PENDING_REVIEW",
    APPROVED: "APPROVED",
    REJECTED: "REJECTED",
  };

  function evidenceStatusLabelAr(status) {
    if (status === EVIDENCE_STATUS.APPROVED) return "معتمد";
    if (status === EVIDENCE_STATUS.REJECTED) return "مرفوض";
    return "قيد المراجعة"; // PENDING_REVIEW، والافتراضي الآمن لأي قيمة غير متوقَّعة
  }

  function evidenceStatusBadgeAttr(status) {
    if (status === EVIDENCE_STATUS.APPROVED) return "approved";
    if (status === EVIDENCE_STATUS.REJECTED) return "rejected";
    return "pending";
  }

  let uploadedEvidenceState = [];
  let uploadModalMqId = null;

  function loadUploadedEvidenceSeed() {
    return fetch(UPLOADED_EVIDENCE_URL)
      .then(function (response) {
        return response.ok ? response.json() : [];
      })
      .catch(function () {
        return [];
      });
  }

  function readUploadedEvidenceFromStorage() {
    try {
      const raw = localStorage.getItem(UPLOADED_EVIDENCE_STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function saveUploadedEvidenceToStorage() {
    try {
      localStorage.setItem(UPLOADED_EVIDENCE_STORAGE_KEY, JSON.stringify(uploadedEvidenceState));
    } catch (e) {
      // localStorage غير متاح (وضع خاص، تخزين معطَّل...) -- الرفع يعمل لهذه
      // الجلسة فقط، بلا ثبات بعد إعادة التحميل.
    }
  }

  function fileExtension(fileName) {
    const parts = String(fileName || "").split(".");
    return parts.length > 1 ? parts.pop().toLowerCase() : "";
  }

  // عرض مُلصَّق بوضوح (Name / Linked MQ / Date / Status) بدل سطر مضغوط
  // واحد -- Evidence Status Display المطلوب هذه الجولة. يقرأ status عبر
  // evidenceStatusLabelAr()/evidenceStatusBadgeAttr() فقط، فيعرض تلقائياً
  // "معتمد"/"مرفوض" الصحيحين لو ظهرت هذه القيم مستقبلاً من مراجعة فعلية
  // (غير مُنفَّذة اليوم) بلا أي تعديل إضافي هنا.
  function pendingEvidenceItemHtml(item) {
    return (
      '<li class="wq-pending-evidence-item">' +
      '<div class="wq-pending-evidence-item__main">' +
      '<span class="wq-evidence-code">📄 ' +
      escapeHtml(item.file_name) +
      "</span>" +
      '<span class="wq-status-badge" data-status="' +
      evidenceStatusBadgeAttr(item.status) +
      '"><span class="wq-status-badge__dot"></span>' +
      escapeHtml(evidenceStatusLabelAr(item.status)) +
      "</span>" +
      "</div>" +
      '<div class="wq-pending-evidence-item__meta">' +
      "<span>مرتبط: " +
      escapeHtml(item.linked_mq) +
      "</span>" +
      "<span>التاريخ: " +
      escapeHtml(item.upload_date) +
      "</span>" +
      "</div>" +
      "</li>"
    );
  }

  // يُبنى دائماً (حتى بلا عناصر) بمعرّف ثابت قابل للاستهداف لاحقاً من
  // refreshPendingEvidenceBlock() بلا إعادة رسم البطاقة كلها (يحافظ على
  // حالة aria-expanded الحالية للبطاقة).
  function pendingEvidenceBlockHtml(mqId) {
    const items = uploadedEvidenceState.filter(function (e) {
      return e.linked_mq === mqId;
    });
    return (
      '<div class="wq-detail-block" id="wq-pending-block-' +
      escapeHtml(mqId) +
      '"' +
      (items.length === 0 ? ' style="display:none"' : "") +
      '><div class="wq-detail-block__label">الأدلة المرفوعة (قيد المراجعة)</div>' +
      '<ul class="wq-evidence-list" id="wq-pending-list-' +
      escapeHtml(mqId) +
      '">' +
      items.map(pendingEvidenceItemHtml).join("") +
      "</ul></div>"
    );
  }

  function refreshPendingEvidenceBlock(mqId) {
    const block = document.getElementById("wq-pending-block-" + mqId);
    const list = document.getElementById("wq-pending-list-" + mqId);
    if (!block || !list) return;
    const items = uploadedEvidenceState.filter(function (e) {
      return e.linked_mq === mqId;
    });
    list.innerHTML = items.map(pendingEvidenceItemHtml).join("");
    block.style.display = items.length > 0 ? "" : "none";
  }

  // الـ Modal بالكامل مُولَّد من JS (بلا لمس index.html) -- نفس أسلوب بناء
  // البطاقات في هذا الملف، ويعيد استخدام كلاسات wq-modal* الموجودة أصلاً
  // بلا أي تكرار CSS.
  function injectUploadModal() {
    const html =
      '<div class="wq-modal-overlay" id="wq-upload-modal-overlay" data-open="false" role="dialog" aria-modal="true" aria-labelledby="wq-upload-modal-title">' +
      '<div class="wq-modal">' +
      '<div class="wq-modal__head">' +
      '<h3 class="wq-modal__title" id="wq-upload-modal-title">إرفاق دليل جديد</h3>' +
      '<button type="button" class="wq-modal__close" id="wq-upload-modal-close" aria-label="إغلاق">✕</button>' +
      "</div>" +
      '<div class="wq-modal__body">' +
      '<div class="wq-upload-field">' +
      '<span class="wq-upload-field__label">اختر متطلب النضج (MQ ID)</span>' +
      '<span class="wq-upload-field__value" id="wq-upload-mq-id">اختر المتطلب</span>' +
      "</div>" +
      '<label class="wq-upload-field" for="wq-upload-file-input">' +
      '<span class="wq-upload-field__label">اختيار ملف</span>' +
      '<input type="file" id="wq-upload-file-input" class="wq-upload-file-input" accept=".pdf,.docx,.xlsx,.png,.jpg,.jpeg" />' +
      "</label>" +
      '<p class="wq-upload-hint">الصيغ المدعومة: PDF, DOCX, XLSX, PNG, JPG</p>' +
      '<p class="wq-upload-error" id="wq-upload-error" hidden></p>' +
      '<button type="button" class="wq-upload-submit" id="wq-upload-submit-btn">رفع الملف</button>' +
      "</div></div></div>";
    document.body.insertAdjacentHTML("beforeend", html);
  }

  function openUploadModal(mqId) {
    uploadModalMqId = mqId;
    document.getElementById("wq-upload-mq-id").textContent = mqId;
    const fileInput = document.getElementById("wq-upload-file-input");
    const errorEl = document.getElementById("wq-upload-error");
    fileInput.value = "";
    errorEl.hidden = true;
    errorEl.textContent = "";
    document.getElementById("wq-upload-modal-overlay").setAttribute("data-open", "true");
  }

  function closeUploadModal() {
    document.getElementById("wq-upload-modal-overlay").setAttribute("data-open", "false");
  }

  function handleUploadSubmit() {
    const fileInput = document.getElementById("wq-upload-file-input");
    const errorEl = document.getElementById("wq-upload-error");
    const file = fileInput.files && fileInput.files[0];

    if (!file) {
      errorEl.textContent = "الرجاء اختيار ملف أولاً.";
      errorEl.hidden = false;
      return;
    }
    if (ALLOWED_EVIDENCE_EXTENSIONS.indexOf(fileExtension(file.name)) === -1) {
      errorEl.textContent = "صيغة الملف غير مدعومة. الصيغ المدعومة: PDF, DOCX, XLSX, PNG, JPG.";
      errorEl.hidden = false;
      return;
    }
    if (!uploadModalMqId) {
      errorEl.textContent = "تعذّر تحديد المتطلب المرتبط بهذا الرفع.";
      errorEl.hidden = false;
      return;
    }

    // سجل بيانات وصفية فقط (id/file_name/linked_mq/upload_date/status) --
    // بلا PASS/FAIL، بلا evidence_code رسمي مُخترَع، بلا أي أثر على
    // evaluated_evidence أو current_level أو next_level_gaps.
    uploadedEvidenceState.push({
      id: "UP-" + Date.now(),
      file_name: file.name,
      linked_mq: uploadModalMqId,
      upload_date: new Date().toISOString().slice(0, 10),
      status: EVIDENCE_STATUS.PENDING_REVIEW,
    });
    saveUploadedEvidenceToStorage();
    refreshPendingEvidenceBlock(uploadModalMqId);
    closeUploadModal();
  }

  function wireUploadModal() {
    const overlay = document.getElementById("wq-upload-modal-overlay");
    document.getElementById("wq-upload-modal-close").addEventListener("click", closeUploadModal);
    document.getElementById("wq-upload-submit-btn").addEventListener("click", handleUploadSubmit);
    overlay.addEventListener("click", function (event) {
      if (event.target === overlay) closeUploadModal();
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && overlay.getAttribute("data-open") === "true") closeUploadModal();
    });
  }

  /* ---------------------------------------------------------------- */
  /* Evidence Repository Integration + Export (Viewer فقط)                */
  /* ---------------------------------------------------------------- */

  // نظام مستقل تماماً عن Evidence Upload أعلاه: هذا يعرض/يصدّر ملفات
  // evidence_repository/ الحقيقية الموجودة على القرص مسبقاً (23 ملف DOCX
  // حقيقي)، بلا أي كتابة أو تعديل أو نسخ دائم -- Viewer للعرض فقط. صفر
  // علاقة بـ current_level/next_level_gaps/evaluated_evidence أو بمنطق
  // النضج بأي شكل.
  //
  // ملاحظة تشغيل إلزامية: evidence_repository/ يقع خارج مجلد
  // wathiq_maturity_dashboard/ (شقيق له، لا ابن) -- لذا يجب تشغيل خادم
  // HTTP المحلي من مجلد جذر المستودع (Wathiq-Data-Management-Platform) وليس
  // من داخل wathiq_maturity_dashboard/ كما في كل الجولات السابقة، وفتح الصفحة عبر
  // .../wathiq_maturity_dashboard/index.html. المسارات في الكتالوج مخزَّنة
  // نسبة لجذر المستودع (كما وردت في المواصفة حرفياً)؛ evidenceFileUrl()
  // أدناه هو موضع الترجمة الوحيد إلى مسار HTTP فعلي (يضيف "../" لأن صفحة
  // اللوحة نفسها مستوى واحد تحت الجذر) -- لا تُغيَّر القيمة المخزَّنة في
  // الكتالوج نفسه.
  const EVIDENCE_REPOSITORY_CATALOG_URL = "data/evidence_repository_catalog.json";
  const EVIDENCE_UNAVAILABLE_MESSAGE = "ملف الدليل غير متاح في نسخة العرض الحالية";

  let evidenceCatalogState = [];

  // نسخة في الذاكرة من specifications[] (نفس complianceData المحمَّل أصلاً
  // في boot لعرض قسم Compliance) -- تُستخدَم فقط للبحث عن حالة امتثال جاهزة
  // في Evidence Detail View (انظر evidenceDetailStatusLabel أدناه). قراءة/
  // بحث فقط، بلا أي إعادة حساب، وبلا أي جلب إضافي لـ DC_compliance.json
  // (نفس الاستدعاء الوحيد لـ loadComplianceData() في boot).
  let complianceState = [];

  function findComplianceSpec(evidenceCode) {
    return complianceState.find(function (spec) {
      return spec.specification_code === evidenceCode;
    });
  }

  /* ---------------------------------------------------------------- */
  /* Evidence Visual Management Layer -- Evidence Artifact Management فقط،  */
  /* بلا أي دخول في حساب نضج/امتثال/تغطية/Score من أي نوع.                */
  /* ---------------------------------------------------------------- */

  // مصدر مستقل تماماً عن sample_maturity_report.json/DC_compliance.json/
  // operational_excellence_simulation.json/evidence_repository_catalog.json
  // -- لا يقرأ من أي منها ولا يكتب إليها. مصفوفة مسطّحة (وليست كائناً
  // مفهرَساً) -- كل عنصر يحمل evidence_code الخاص به صراحة (شرط إلزامي: لا
  // Visual Evidence بلا evidence_code يشير لدليل DC.M.x/DC.C.x.x حقيقي).
  const EVIDENCE_VISUAL_CATALOG_URL = "data/evidence_visual_catalog.json";
  const VISUAL_EVIDENCE_FILE_BASE = "evidence_repository/data_classification/visual_evidence/";

  // الفئات الخمس المسموحة فقط (لا تُخترَع فئات أخرى).
  const VISUAL_EVIDENCE_CATEGORIES = ["Workshop", "Meeting", "Approval", "Report", "Screenshot"];

  // حالات دورة حياة الدليل الست المسموحة فقط (لا تُخترَع حالة إضافية).
  // الترتيب هنا هو ترتيب التقدّم الطبيعي المستخدَم لاحقاً في عرض "دورة حياة
  // الدليل" (Rejected/Archived حالتان طرفيتان خارج التسلسل التصاعدي).
  const EVIDENCE_LIFECYCLE_STATUSES = ["Draft", "Submitted", "Under Review", "Approved", "Rejected", "Archived"];
  const EVIDENCE_LIFECYCLE_PROGRESSION = ["Draft", "Submitted", "Under Review", "Approved"];

  let evidenceVisualCatalogState = [];

  // مرجع للقراءة فقط لتقرير النضج المحمَّل أصلاً في boot (data.mq_results)
  // -- يُستخدَم حصراً للبحث عن level_number الخاص بكود دليل أصلي (evidence_
  // code) عند بناء قسم "علاقة التقييم" في Evidence Package Viewer. لا
  // يُكتب إليه أبداً، ولا يُشتق منه أي حساب جديد -- بحث فقط.
  let loadedMaturityData = null;

  function findEvaluatedEvidenceLevel(evidenceCode) {
    if (!loadedMaturityData) return null;
    for (const mq of loadedMaturityData.mq_results || []) {
      for (const e of mq.evaluated_evidence || []) {
        if (e.evidence_code === evidenceCode && typeof e.level_number === "number") {
          return e.level_number;
        }
      }
    }
    return null;
  }

  /* ---------------------------------------------------------------- */
  /* Evidence Relationships Layer -- Metadata Relationship Mapping فقط،   */
  /* عرض وتنقّل بين حزم أدلة موجودة أصلاً -- بلا أي حساب أو إعادة تقييم.    */
  /* ---------------------------------------------------------------- */

  // اسم قابل للعرض لكود هدف علاقة (mq_id أو evidence_code) -- بحث فقط في
  // مصدرين موجودين أصلاً: sample_maturity_report.json (سؤال المتطلب أو
  // اسم الدليل المقيَّم) ثم data/evidence_visual_catalog.json (عنوان الدليل
  // المرئي) كخيار احتياطي. يعيد null إن تعذّر أي تطابق -- لا اسم مخترَع.
  function resolveRelationshipTargetName(code) {
    if (loadedMaturityData) {
      for (const mq of loadedMaturityData.mq_results || []) {
        if (mq.mq_id === code) return mq.question;
        for (const e of mq.evaluated_evidence || []) {
          if (e.evidence_code === code) return evidenceNameDisplay(e.evidence_name);
        }
      }
    }
    const visualMatch = evidenceVisualCatalogState.find(function (i) {
      return i.evidence_code === code;
    });
    return visualMatch ? visualMatch.title : null;
  }

  // يبحث عن أول دليل مرئي (Evidence Package) بنفس evidence_code -- هذا فقط
  // ما "يُفتَح" فعلياً (Evidence Package Viewer). mq_id (مثل DC.MQ.3) لا
  // يطابق أي evidence_code أبداً بحكم الصيغة، فلا يُفتَح -- وهذا هو السلوك
  // الصحيح المطلوب (بند 4: زر الفتح فقط عند وجود حزمة فعلية).
  function resolveRelationshipTarget(code) {
    return (
      evidenceVisualCatalogState.find(function (i) {
        return i.evidence_code === code;
      }) || null
    );
  }

  function evidenceRelationshipTotalCount(item) {
    const rel = item.relationships;
    if (!rel) return 0;
    return (
      ((rel.supports && rel.supports.length) || 0) +
      ((rel.related_evidence && rel.related_evidence.length) || 0) +
      ((rel.related_requirements && rel.related_requirements.length) || 0)
    );
  }

  function evidenceHasRelationships(item) {
    return evidenceRelationshipTotalCount(item) > 0;
  }

  // بطاقة علاقة واحدة -- الاسم يظهر فقط إن أمكن تحليله (بحث فقط)، وزر
  // الفتح يظهر فقط إن وُجدت حزمة دليل مرئي فعلية لهذا الكود (بند 4/8 حرفياً).
  function evidenceRelationshipCardHtml(typeLabel, code) {
    const name = resolveRelationshipTargetName(code);
    const target = resolveRelationshipTarget(code);
    return (
      '<div class="wq-evidence-relationship-card">' +
      '<span class="wq-evidence-relationship-type">' +
      escapeHtml(typeLabel) +
      "</span>" +
      '<span class="wq-evidence-related-item">' +
      escapeHtml(code) +
      (name ? " — " + escapeHtml(name) : "") +
      "</span>" +
      (target
        ? '<button type="button" class="wq-evidence-related-item__open" data-visual-evidence-id="' +
          escapeHtml(target.visual_evidence_id) +
          '">فتح الحزمة →</button>'
        : "") +
      "</div>"
    );
  }

  // القسم بالكامل -- غائب إن لم توجد أي علاقة إطلاقاً. كل مجموعة (Supports/
  // Related Evidence/Related Requirements) تُعرض فقط إن كانت مصفوفتها غير
  // فارغة -- عنصر واحد يُعرض وحده، عدة عناصر تُعرض كقائمة، بلا فرق في
  // المنطق (map عادي في الحالتين).
  function evidenceRelationshipsSectionHtml(item) {
    const rel = item.relationships;
    if (!rel || !evidenceHasRelationships(item)) return "";

    // تسميات المجموعات كانت إنجليزية بالكامل (Arabic Terminology Audit) --
    // نص عرض فقط؛ مفاتيح rel.* نفسها (supports/related_evidence/
    // related_requirements) لم تتغيّر.
    const groups = [
      ["يدعم", rel.supports],
      ["أدلة مرتبطة", rel.related_evidence],
      ["متطلبات مرتبطة", rel.related_requirements],
    ];

    const groupsHtml = groups
      .filter(function (g) {
        return g[1] && g[1].length > 0;
      })
      .map(function (g) {
        return g[1]
          .map(function (code) {
            return evidenceRelationshipCardHtml(g[0], code);
          })
          .join("");
      })
      .join("");

    return (
      '<div class="wq-evidence-relationships">' +
      '<h4 class="wq-evidence-relationships__title">ارتباطات الدليل</h4>' +
      groupsHtml +
      "</div>"
    );
  }

  function evidenceStatusSlug(status) {
    return String(status || "")
      .toLowerCase()
      .replace(/\s+/g, "-");
  }

  // خرائط عرض عربية فقط (Arabic Cleanup Pass) -- القيمة الأصلية (حقل
  // status/category الخام في evidence_visual_catalog.json، أو قيمة
  // منطقية داخلية مثل "Healthy"/"Validated" غير مأخوذة من أي حقل نصي)
  // تبقى تماماً كما هي لأغراض المطابقة/الفلترة/الـslug؛ هذه الخرائط
  // تُستخدَم فقط لتحديد النص الظاهر للمستخدم -- بلا أي تغيير على بيانات
  // أو data contract أو منطق فلترة.
  var VISUAL_EVIDENCE_STATUS_AR = {
    Draft: "مسودة",
    Submitted: "مُقدَّم",
    "Under Review": "قيد المراجعة",
    Approved: "معتمد",
    Rejected: "مرفوض",
    Archived: "مؤرشف",
  };
  var VISUAL_EVIDENCE_CATEGORY_AR = {
    Workshop: "ورشة عمل",
    Meeting: "اجتماع",
    Approval: "اعتماد",
    Report: "تقرير",
    Screenshot: "لقطة شاشة",
  };
  var VISUAL_EVIDENCE_HEALTH_AR = {
    Healthy: "سليم",
    "Attention Required": "يتطلب مراجعة",
    Incomplete: "غير مكتمل",
  };
  var VISUAL_EVIDENCE_VALIDATION_AR = {
    Validated: "تم التحقق",
    "Not Validated": "لم يتم التحقق",
  };
  var VISUAL_EVIDENCE_RELATIONSHIP_AR = {
    "Has Relationships": "مرتبط",
    "No Relationships": "غير مرتبط",
  };
  // إجراءات سجل التدقيق (item.audit_trail[].action) -- مفردات أفعال منفصلة
  // عن حالات دورة الحياة أعلاه (Created/Reviewed غير موجودتين هناك أصلاً).
  var VISUAL_EVIDENCE_AUDIT_ACTION_AR = {
    Created: "تم الإنشاء",
    Submitted: "تم التقديم",
    Reviewed: "تمت المراجعة",
    Approved: "تم الاعتماد",
  };
  function arDisplay(map, value) {
    return (map && map[value]) || value;
  }

  // شارة حالة دورة الحياة -- مكوّن جديد بالكامل (wq-evidence-status-badge)،
  // بلا أي تعديل على wq-status-badge الموجودة أصلاً. الألوان الست كلها من
  // توكنات دلالية/محايدة موجودة أصلاً (status-info/warning/success/error +
  // درجتا رمادي من text-faint/text-primary) -- بلا أي لون جديد.
  function evidenceStatusBadgeHtml(status) {
    if (!status) return "";
    return (
      '<span class="wq-evidence-status-badge" data-status="' +
      evidenceStatusSlug(status) +
      '">' +
      escapeHtml(arDisplay(VISUAL_EVIDENCE_STATUS_AR, status)) +
      "</span>"
    );
  }

  /* ---------------------------------------------------------------- */
  /* Evidence Health Dashboard -- Metadata Analytics بحتة (بلا أي قراءة من
     sample_maturity_report.json/DC_compliance.json/operational_excellence_
     simulation.json). كل حساب هنا عدّ بسيط على حقول data/evidence_visual_
     catalog.json الموجودة أصلاً -- بلا أي وزن أو Score أو منطق تجميع.     */
  /* ---------------------------------------------------------------- */

  // "Validated" هنا يعني تحديداً وجود verified_by (نفس تعريف Validated
  // Count في البند 3) -- مفهوم مختلف عمداً عن validation_status النصي
  // (مراجع/غير مراجع/قيد المراجعة) المستخدَم في قسم "التحقق من الدليل"
  // داخل Evidence Package Viewer؛ لا تُستخدَم الحقول القديمة بالخطأ هنا.
  function evidenceHasLifecycle(item) {
    return !!(item.lifecycle_history && Object.keys(item.lifecycle_history).length > 0);
  }
  function evidenceHasVersion(item) {
    return !!item.version;
  }
  function evidenceHasValidation(item) {
    return !!item.verified_by;
  }
  function evidenceHasAttachments(item) {
    return !!(item.attachments && item.attachments.length > 0);
  }

  // Healthy: يحتوي Lifecycle + Version + Validation معاً (بند 4 حرفياً).
  // Attention Required: يملك خيط دورة حياة (Lifecycle) لكنه لا يستوفي
  // Healthy بالكامل (عادة لغياب Validation و/أو Attachments و/أو Version).
  // Incomplete: لا يملك حتى بيانات دورة الحياة الأساسية -- أدنى مستوى.
  // عدّ/شروط بحتة على حقول موجودة أصلاً، بلا أي بيانات وهمية أو تخمين.
  function evidenceHealthStatus(item) {
    const hasLifecycle = evidenceHasLifecycle(item);
    if (hasLifecycle && evidenceHasVersion(item) && evidenceHasValidation(item)) return "Healthy";
    if (hasLifecycle) return "Attention Required";
    return "Incomplete";
  }

  function evidenceHealthStatusSlug(status) {
    return String(status || "")
      .toLowerCase()
      .replace(/\s+/g, "-");
  }

  // شارة حالة الصحة العامة -- مكوّن جديد مستقل تماماً (wq-evidence-health-
  // status)، بلا أي تعديل على wq-evidence-status-badge (حالة دورة الحياة)
  // أو wq-status-badge. الألوان الثلاث من توكنات دلالية موجودة أصلاً
  // (success/warning/error) -- بلا أي لون جديد.
  function evidenceHealthStatusBadgeHtml(status) {
    return (
      '<span class="wq-evidence-health-status" data-health="' +
      evidenceHealthStatusSlug(status) +
      '">' +
      escapeHtml(arDisplay(VISUAL_EVIDENCE_HEALTH_AR, status)) +
      "</span>"
    );
  }

  // مؤشرات الصحة الرئيسية -- عدّ بحت على evidenceVisualCatalogState فقط.
  // ممنوع صراحة (بند 3): أي استخدام لنتائج Maturity/Compliance/Scoring --
  // لا استيراد ولا قراءة لأي من تلك الملفات هنا.
  function evidenceHealthKpis() {
    const items = evidenceVisualCatalogState;
    function countWhere(predicate) {
      return items.filter(predicate).length;
    }
    return {
      total: items.length,
      approved: countWhere(function (i) {
        return i.status === "Approved";
      }),
      underReview: countWhere(function (i) {
        return i.status === "Under Review";
      }),
      archived: countWhere(function (i) {
        return i.status === "Archived";
      }),
      withAttachments: countWhere(evidenceHasAttachments),
      validated: countWhere(evidenceHasValidation),
    };
  }

  function evidenceHealthCardHtml(label, value) {
    return (
      '<div class="wq-evidence-health-card">' +
      '<div class="wq-evidence-health-card__label">' +
      escapeHtml(label) +
      "</div>" +
      '<div class="wq-evidence-health-card__value">' +
      value +
      "</div>" +
      "</div>"
    );
  }

  // القسم الجديد -- يظهر قبل قائمة الأدلة داخل مستودع الأدلة المرئية (بند
  // 1). يُعاد بناؤه بالكامل عند كل استدعاء renderVisualEvidenceRepository
  // (بلا حالة داخلية خاصة به) لأنه دائماً انعكاس مباشر وفوري لكل عناصر
  // evidenceVisualCatalogState -- لا فلترة عليه (يعرض إجمالي المجال دائماً).
  function renderEvidenceHealthDashboard() {
    const container = document.getElementById("wq-evidence-health-dashboard");
    if (!container) return;
    const kpis = evidenceHealthKpis();
    container.innerHTML =
      '<h3 class="wq-evidence-health-dashboard__title">لوحة مؤشرات صحة الأدلة</h3>' +
      '<div class="wq-evidence-health-dashboard__grid">' +
      evidenceHealthCardHtml("إجمالي الأدلة المرئية", kpis.total) +
      evidenceHealthCardHtml("الأدلة المعتمدة", kpis.approved) +
      evidenceHealthCardHtml("الأدلة قيد المراجعة", kpis.underReview) +
      evidenceHealthCardHtml("الأدلة المؤرشفة", kpis.archived) +
      evidenceHealthCardHtml("الأدلة التي تحتوي مرفقات", kpis.withAttachments) +
      evidenceHealthCardHtml("الأدلة التي تحتوي تحقق", kpis.validated) +
      "</div>";
  }

  /* ---------------------------------------------------------------- */
  /* Evidence Analytics Dashboard -- Metadata Analytics بحتة، بلا أي علاقة
     بـ Maturity/Compliance/Operational Excellence (بند 3 من مواصفة
     Evidence Governance Expansion Layer). المصدر الوحيد لكل هذه الحسابات
     هو evidenceVisualCatalogState (data/evidence_visual_catalog.json)،
     تماماً كما في Evidence Health Dashboard أعلاه -- عدّ/تجميع بسيط بلا أي
     Score أو وزن. */
  /* ---------------------------------------------------------------- */

  const EVIDENCE_STATUS_VALUES = ["Approved", "Submitted", "Under Review", "Draft", "Archived"];

  // Evidence Coverage -- الاستثناء الوحيد الذي يتغيّر مع الفلاتر/البحث عمداً
  // (عرض فقط): "الأدلة الحالية" هنا تعني عدد العناصر ضمن العرض الحالي
  // (filteredVisualEvidenceItems) مقارنةً بإجمالي المستودع المرئي، بلا أي
  // أثر على المتطلبات/الفلاتر نفسها أو أي حساب تقييم.
  function evidenceAnalyticsCoverage() {
    return {
      current: filteredVisualEvidenceItems().length,
      total: evidenceVisualCatalogState.length,
    };
  }

  function evidenceAnalyticsByStatus() {
    const items = evidenceVisualCatalogState;
    return EVIDENCE_STATUS_VALUES.map(function (status) {
      return {
        label: arDisplay(VISUAL_EVIDENCE_STATUS_AR, status),
        value: items.filter(function (i) {
          return i.status === status;
        }).length,
      };
    });
  }

  function evidenceAnalyticsByType() {
    const items = evidenceVisualCatalogState;
    return VISUAL_EVIDENCE_CATEGORIES.map(function (category) {
      return {
        label: arDisplay(VISUAL_EVIDENCE_CATEGORY_AR, category),
        value: items.filter(function (i) {
          return i.category === category;
        }).length,
      };
    });
  }

  // Evidence Aging -- حسب last_updated_date فقط حرفياً (بند 3)، بلا أي
  // استخدام لحقل "date" العام. العناصر التي لا تحمل last_updated_date
  // تُستبعَد بصمت من الحساب (لا قيمة صفرية مخترَعة لها بدل ذلك)؛ إن لم
  // يحمل أي عنصر هذا الحقل يُرجَع null فيختفي القسم بالكامل.
  function evidenceAnalyticsAging() {
    const now = Date.now();
    const buckets = [
      { label: "0–30 يوماً", value: 0 },
      { label: "31–90 يوماً", value: 0 },
      { label: "90+ يوماً", value: 0 },
    ];
    let counted = 0;
    evidenceVisualCatalogState.forEach(function (item) {
      if (!item.last_updated_date) return;
      const updated = new Date(item.last_updated_date).getTime();
      if (isNaN(updated)) return;
      counted++;
      const days = Math.floor((now - updated) / (1000 * 60 * 60 * 24));
      if (days <= 30) buckets[0].value++;
      else if (days <= 90) buckets[1].value++;
      else buckets[2].value++;
    });
    return counted > 0 ? buckets : null;
  }

  function evidenceAnalyticsCardRowsHtml(rows) {
    return rows
      .map(function (row) {
        return (
          '<div class="wq-evidence-analytics-card__row">' +
          '<span class="wq-evidence-analytics-card__label">' +
          escapeHtml(row.label) +
          "</span>" +
          '<span class="wq-evidence-analytics-card__value">' +
          row.value +
          "</span>" +
          "</div>"
        );
      })
      .join("");
  }

  function evidenceAnalyticsCardHtml(title, innerHtml) {
    return (
      '<div class="wq-evidence-analytics-card">' +
      '<h4 class="wq-evidence-analytics-card__title">' +
      escapeHtml(title) +
      "</h4>" +
      innerHtml +
      "</div>"
    );
  }

  // يُستدعى مع كل إعادة رسم لقائمة الأدلة المرئية (فلترة/بحث) حتى تبقى
  // بطاقة Evidence Coverage مطابقة دوماً للعرض الحالي -- بقية البطاقات
  // (By Status/By Type/Aging) تعكس إجمالي المستودع دائماً، بلا فلترة، تماماً
  // مثل Evidence Health Dashboard.
  function renderEvidenceAnalytics() {
    const container = document.getElementById("wq-evidence-analytics");
    if (!container) return;

    const coverage = evidenceAnalyticsCoverage();
    const coverageHtml = evidenceAnalyticsCardHtml(
      "نطاق التغطية الحالي",
      '<div class="wq-evidence-analytics-card__value wq-evidence-analytics-card__value--big">' +
        coverage.current +
        " / " +
        coverage.total +
        "</div>"
    );

    const byStatusHtml = evidenceAnalyticsCardHtml(
      "الأدلة حسب الحالة",
      evidenceAnalyticsCardRowsHtml(evidenceAnalyticsByStatus())
    );
    const byTypeHtml = evidenceAnalyticsCardHtml(
      "الأدلة حسب الفئة",
      evidenceAnalyticsCardRowsHtml(evidenceAnalyticsByType())
    );

    const aging = evidenceAnalyticsAging();
    const agingHtml = aging
      ? evidenceAnalyticsCardHtml("قِدَم الأدلة", evidenceAnalyticsCardRowsHtml(aging))
      : "";

    container.innerHTML =
      '<h3 class="wq-evidence-analytics__title">تحليلات الأدلة</h3>' +
      '<div class="wq-evidence-analytics__grid">' +
      coverageHtml +
      byStatusHtml +
      byTypeHtml +
      agingHtml +
      "</div>";
  }

  /* ---------------------------------------------------------------- */
  /* Evidence Center (بند 4) -- خمس بطاقات مؤشرات فقط، من evidenceVisual
     CatalogState حصراً (بلا أي قراءة لملفات تقييم أخرى). قسم مستقل تماماً
     عن Evidence Health Dashboard/Evidence Analytics أعلاه (كلاسات جديدة
     بالكامل: .wq-evidence-center/.wq-evidence-center-card)، بلا فلترة
     (يعكس إجمالي المستودع دائماً، تماماً كبقية لوحات المؤشرات). */
  /* ---------------------------------------------------------------- */

  function evidenceCenterKpis() {
    const items = evidenceVisualCatalogState;
    function countWhere(predicate) {
      return items.filter(predicate).length;
    }
    return {
      total: items.length,
      approved: countWhere(function (i) {
        return i.status === "Approved";
      }),
      underReview: countWhere(function (i) {
        return i.status === "Under Review";
      }),
      incomplete: countWhere(function (i) {
        return evidenceHealthStatus(i) === "Incomplete";
      }),
      validated: countWhere(evidenceHasValidation),
    };
  }

  function evidenceCenterCardHtml(label, value) {
    return (
      '<div class="wq-evidence-center-card">' +
      '<div class="wq-evidence-center-card__label">' +
      escapeHtml(label) +
      "</div>" +
      '<div class="wq-evidence-center-card__value">' +
      value +
      "</div>" +
      "</div>"
    );
  }

  function renderEvidenceCenter() {
    const container = document.getElementById("wq-evidence-center");
    if (!container) return;
    const kpis = evidenceCenterKpis();
    container.innerHTML =
      '<h3 class="wq-evidence-center__title">مركز الأدلة</h3>' +
      '<div class="wq-evidence-center__grid">' +
      evidenceCenterCardHtml("إجمالي حزم الأدلة", kpis.total) +
      evidenceCenterCardHtml("الحزم المعتمدة", kpis.approved) +
      evidenceCenterCardHtml("قيد المراجعة", kpis.underReview) +
      evidenceCenterCardHtml("الأدلة غير المكتملة", kpis.incomplete) +
      evidenceCenterCardHtml("الأدلة التي تم التحقق منها", kpis.validated) +
      "</div>";
  }

  function loadEvidenceVisualCatalog() {
    return fetch(EVIDENCE_VISUAL_CATALOG_URL)
      .then(function (response) {
        return response.ok ? response.json() : [];
      })
      .catch(function () {
        return [];
      });
  }

  function visualEvidenceItemsForCode(evidenceCode) {
    return evidenceVisualCatalogState.filter(function (item) {
      return item.evidence_code === evidenceCode;
    });
  }

  function visualEvidenceById(visualEvidenceId) {
    return evidenceVisualCatalogState.find(function (item) {
      return item.visual_evidence_id === visualEvidenceId;
    });
  }

  // بطاقة دليل مرئي واحدة -- تُستخدَم في مكانين حرفياً بنفس الشكل: قسم
  // "الأدلة المرئية المرتبطة" داخل Modal تفاصيل دليل واحد، وقسم "مستودع
  // الأدلة المرئية" العام. withContext=true يُضيف سطر Evidence Code/MQ ID
  // أعلى البطاقة فقط في السياق العام (غير ضروري داخل Modal، إذ العنوان
  // نفسه يحمل الكود بالفعل).
  function visualEvidenceCardHtml(item, withContext) {
    const participantsRow = item.participants
      ? '<span class="wq-visual-evidence-card__field"><span class="wq-visual-evidence-card__field-label">المشاركون</span>' +
        '<span class="wq-visual-evidence-card__field-value">' +
        escapeHtml(item.participants) +
        "</span></span>"
      : "";

    // ثلاثة حقول اختيارية إضافية (بند 9): الإصدار/عدد المرفقات/حالة
    // التحقق -- تُقرأ من الحقول الجاهزة نفسها المستخدَمة داخل Evidence
    // Package Viewer، بلا أي حساب جديد، وتظهر فقط إن وُجدت بياناتها.
    const versionRow = item.version
      ? '<span class="wq-visual-evidence-card__field"><span class="wq-visual-evidence-card__field-label">الإصدار</span>' +
        '<span class="wq-visual-evidence-card__field-value">' +
        escapeHtml(item.version) +
        "</span></span>"
      : "";
    const attachmentsRow =
      item.attachments && item.attachments.length > 0
        ? '<span class="wq-visual-evidence-card__field"><span class="wq-visual-evidence-card__field-label">المرفقات</span>' +
          '<span class="wq-visual-evidence-card__field-value">' +
          item.attachments.length +
          " مرفقات</span></span>"
        : "";
    const validationRow = item.validation_status
      ? '<span class="wq-visual-evidence-card__field"><span class="wq-visual-evidence-card__field-label">التحقق</span>' +
        '<span class="wq-visual-evidence-card__field-value">' +
        escapeHtml(item.validation_status) +
        "</span></span>"
      : "";
    // وسم "Validated" -- بند 5، مبني على نفس تعريف Validated Count حرفياً
    // (وجود verified_by)، وليس validation_status النصي أعلاه. يظهر فقط
    // عند تحقُّق الشرط -- لا يُعرض "Not Validated" (لا وجود لبيانات سلبية
    // مخترَعة، فقط غياب الوسم).
    const validatedTag = evidenceHasValidation(item)
      ? '<span class="wq-visual-evidence-card__field"><span class="wq-visual-evidence-card__field-value">تم التحقق</span></span>'
      : "";

    // حقل "عدد الارتباطات: N" -- بند 5 من مواصفة Evidence Relationships
    // Layer 1.0، يُبنى من evidenceRelationshipTotalCount() نفسه المستخدَم
    // في قسم Evidence Relationships داخل Package Viewer، ويظهر فقط عند
    // وجود علاقة واحدة على الأقل (بلا قيمة افتراضية "0").
    const relationshipsCount = evidenceRelationshipTotalCount(item);
    const relationshipsRow =
      relationshipsCount > 0
        ? '<span class="wq-visual-evidence-card__field"><span class="wq-visual-evidence-card__field-label">الارتباطات</span>' +
          '<span class="wq-visual-evidence-card__field-value">' +
          relationshipsCount +
          "</span></span>"
        : "";

    return (
      '<div class="wq-visual-evidence-card' +
      (withContext ? " wq-evidence-management-card" : "") +
      '">' +
      (withContext
        ? '<div class="wq-visual-evidence-card__context">' +
          '<span class="wq-visual-evidence-card__context-code">' +
          escapeHtml(item.evidence_code) +
          "</span>" +
          '<span class="wq-visual-evidence-card__context-mq">' +
          escapeHtml(item.mq_id) +
          "</span>" +
          "</div>"
        : "") +
      '<div class="wq-visual-evidence-card__head">' +
      '<span class="wq-visual-evidence-badge">' +
      escapeHtml(arDisplay(VISUAL_EVIDENCE_CATEGORY_AR, item.category)) +
      "</span>" +
      evidenceHealthStatusBadgeHtml(evidenceHealthStatus(item)) +
      "</div>" +
      '<p class="wq-visual-evidence-card__title">' +
      escapeHtml(item.title) +
      "</p>" +
      '<div class="wq-visual-evidence-card__meta">' +
      '<span class="wq-visual-evidence-card__field"><span class="wq-visual-evidence-card__field-label">التاريخ</span>' +
      '<span class="wq-visual-evidence-card__field-value">' +
      escapeHtml(item.date) +
      "</span></span>" +
      participantsRow +
      versionRow +
      attachmentsRow +
      validationRow +
      validatedTag +
      relationshipsRow +
      '<span class="wq-visual-evidence-card__field"><span class="wq-visual-evidence-card__field-label">الحالة</span>' +
      evidenceStatusBadgeHtml(item.status) +
      "</span>" +
      "</div>" +
      '<button type="button" class="wq-visual-evidence-card__action" data-visual-evidence-id="' +
      escapeHtml(item.visual_evidence_id) +
      '">عرض الحزمة →</button>' +
      "</div>"
    );
  }

  /* ---------------------------------------------------------------- */
  /* جدول إدارة الأدلة (بند 5) -- عرض جدولي اختياري بديل لنفس بطاقات
     مستودع الأدلة المرئية، على نفس العناصر المفلترة فعلياً (filteredVisual
     EvidenceItems) بلا أي حساب جديد. زر "عرض الحزمة" يعيد استخدام كلاس
     .wq-visual-evidence-card__action الموجود أصلاً حرفياً، فيُلتقَط تلقائياً
     بواسطة مُستمع النقر المفوَّض الحالي في wireVisualEvidenceActions بلا
     أي وصل جديد. */
  /* ---------------------------------------------------------------- */

  function evidenceManagementTableRowHtml(item) {
    return (
      "<tr>" +
      "<td>" +
      escapeHtml(item.evidence_code) +
      "</td>" +
      "<td>" +
      escapeHtml(item.title) +
      "</td>" +
      "<td>" +
      escapeHtml(arDisplay(VISUAL_EVIDENCE_CATEGORY_AR, item.category)) +
      "</td>" +
      "<td>" +
      evidenceStatusBadgeHtml(item.status) +
      "</td>" +
      "<td>" +
      evidenceHealthStatusBadgeHtml(evidenceHealthStatus(item)) +
      "</td>" +
      "<td>" +
      (item.validation_status ? escapeHtml(item.validation_status) : "—") +
      "</td>" +
      "<td>" +
      (item.version ? "الإصدار " + escapeHtml(item.version) : "—") +
      "</td>" +
      "<td>" +
      (item.attachments ? item.attachments.length : 0) +
      "</td>" +
      "<td>" +
      '<button type="button" class="wq-visual-evidence-card__action" data-visual-evidence-id="' +
      escapeHtml(item.visual_evidence_id) +
      '">عرض الحزمة</button>' +
      "</td>" +
      "</tr>"
    );
  }

  function evidenceManagementTableHtml(items) {
    return (
      '<table class="wq-evidence-management-table">' +
      "<thead><tr>" +
      "<th>معرف الدليل</th>" +
      "<th>العنوان</th>" +
      "<th>الفئة</th>" +
      "<th>الحالة</th>" +
      "<th>الصحة</th>" +
      "<th>التحقق</th>" +
      "<th>الإصدار</th>" +
      "<th>عدد المرفقات</th>" +
      "<th>الإجراء</th>" +
      "</tr></thead>" +
      "<tbody>" +
      items.map(evidenceManagementTableRowHtml).join("") +
      "</tbody>" +
      "</table>"
    );
  }

  // القسم داخل Modal تفاصيل الدليل -- يُبنى دائماً (مع رسالة فارغة صريحة
  // عند غياب مرفقات) بلا التأثير على أي حقل آخر في النافذة.
  function visualEvidenceSectionHtml(evidenceCode) {
    const items = visualEvidenceItemsForCode(evidenceCode);

    const body =
      items.length === 0
        ? '<p class="wq-visual-evidence-empty">لا توجد أدلة مرئية مرتبطة بهذا الدليل حالياً.</p>'
        : '<div class="wq-visual-evidence-list">' +
          items.map(function (item) { return visualEvidenceCardHtml(item, false); }).join("") +
          "</div>";

    return (
      '<div class="wq-visual-evidence-section">' +
      '<h4 class="wq-visual-evidence-section__title">الأدلة المرئية المرتبطة' +
      (items.length > 0 ? " — عدد الأدلة المرئية: " + items.length : "") +
      "</h4>" +
      body +
      "</div>"
    );
  }

  // جلب فعلي لملف مرئي واحد (fetch حقيقي، نفس أسلوب openEvidenceFile()
  // الموجود أصلاً لملفات مستودع الأدلة الحقيقية) -- نقطة وحيدة يُعاد
  // استخدامها من كل أنماط المعاينة أدناه (صورة/PDF/فتح خارجي). حقل status
  // في الكتالوج ("Available") يصف دورة حياة السجل نفسه (تم توثيقه/تسجيله)،
  // وهو مستقل عن توفر نسخة العرض التجريبية الفعلية للملف الثنائي -- لذلك
  // يُحاوَل الجلب دائماً، ويُعرَض بصدق "الملف غير متوفر في نسخة العرض
  // الحالية" بدل رابط أو معاينة معطوبة عندما لا توجد نسخة ملف فعلية بعد.
  function fetchVisualEvidenceFile(fileName) {
    return fetch("../" + VISUAL_EVIDENCE_FILE_BASE + fileName).then(function (response) {
      if (!response.ok) throw new Error("HTTP " + response.status);
      return response.blob();
    });
  }

  // يحدد نمط المعاينة من file_type فقط -- لا تخمين ولا معاينة مزيَّفة:
  // صورة قابلة للعرض المباشر، PDF قابل للعرض داخل إطار، أو "خارجي" (فتح في
  // تبويب جديد فقط، بلا محاولة معاينة Word/Excel/PowerPoint داخل الصفحة).
  function evidencePreviewMode(fileType) {
    const t = String(fileType || "").toUpperCase();
    if (t === "PNG" || t === "JPG" || t === "JPEG") return "image";
    if (t === "PDF") return "pdf";
    return "external";
  }

  function visualEvidenceUnavailableHtml() {
    return '<p class="wq-evidence-preview__unavailable">الملف غير متوفر في نسخة العرض الحالية</p>';
  }

  // يُستدعى بعد إدراج Modal في DOM -- يملأ #wq-evidence-preview بمحاولة
  // جلب حقيقية (صورة/PDF)، أو يصل زر الفتح الخارجي (Word/Excel/PowerPoint
  // وأي نوع آخر غير معروف) بنفس دالة الجلب -- بلا أي رابط وهمي.
  function loadEvidencePreview(item) {
    const container = document.getElementById("wq-evidence-preview");
    if (!container) return;
    const mode = evidencePreviewMode(item.file_type);

    if (mode === "image") {
      fetchVisualEvidenceFile(item.file_name)
        .then(function (blob) {
          const url = URL.createObjectURL(blob);
          container.innerHTML =
            '<img class="wq-evidence-preview__image" src="' + url + '" alt="' + escapeHtml(item.title) + '" />';
        })
        .catch(function () {
          container.innerHTML = visualEvidenceUnavailableHtml();
        });
      return;
    }

    if (mode === "pdf") {
      fetchVisualEvidenceFile(item.file_name)
        .then(function (blob) {
          const url = URL.createObjectURL(blob);
          container.innerHTML =
            '<iframe class="wq-evidence-preview__pdf" src="' + url + '" title="' + escapeHtml(item.title) + '"></iframe>';
        })
        .catch(function () {
          container.innerHTML = visualEvidenceUnavailableHtml();
        });
      return;
    }

    // external: DOCX/XLSX/PPTX وأي نوع آخر -- بلا محاولة معاينة داخلية.
    container.innerHTML =
      '<button type="button" class="wq-evidence-preview__external-btn" id="wq-evidence-preview-external-btn">فتح الملف الخارجي</button>';
    const btn = document.getElementById("wq-evidence-preview-external-btn");
    btn.addEventListener("click", function () {
      btn.disabled = true;
      fetchVisualEvidenceFile(item.file_name)
        .then(function (blob) {
          const url = URL.createObjectURL(blob);
          window.open(url, "_blank", "noopener");
          btn.disabled = false;
        })
        .catch(function () {
          container.innerHTML = visualEvidenceUnavailableHtml();
        });
    });
  }

  // "نظرة عامة" -- عنوان الدليل ووصفه وفئته، كلها حقول موجودة أصلاً على
  // كائن الدليل المرئي نفسه (title/description/category) -- بلا اختراع أي
  // وصف. القسم بالكامل غائب إن غاب العنوان (الحد الأدنى المعقول لعرضه).
  function evidencePackageOverviewHtml(item) {
    if (!item.title) return "";
    const descriptionHtml = item.description
      ? '<p class="wq-evidence-package-overview__description">' + escapeHtml(item.description) + "</p>"
      : "";
    return (
      '<div class="wq-evidence-package-overview">' +
      '<h4 class="wq-evidence-package-overview__title">نظرة عامة</h4>' +
      '<p class="wq-evidence-package-overview__name">' +
      escapeHtml(item.title) +
      "</p>" +
      descriptionHtml +
      "</div>"
    );
  }

  // "علاقة التقييم" -- عرض/بحث فقط، بلا أي منطق حسابي: المتطلب المرتبط
  // (mq_id موجود أصلاً)، نوع الدليل (من بادئة evidence_code، نفس
  // evidenceTypeLabel المستخدَمة أصلاً في مستودع الأدلة)، دور الدليل (نص
  // ثابت لا يتغيّر)، ومستوى النضج المرتبط -- بحث فقط عن level_number
  // الجاهز أصلاً في sample_maturity_report.json عبر findEvaluatedEvidenceLevel
  // (بلا أي إعادة حساب)، ويُعرض فقط إذا وُجد.
  function evidenceAssessmentLinkHtml(item) {
    const typeLabel = evidenceTypeLabel(item.evidence_code);
    const level = findEvaluatedEvidenceLevel(item.evidence_code);

    const levelRow =
      typeof level === "number"
        ? '<div class="wq-evidence-assessment-link__row">' +
          '<span class="wq-evidence-assessment-link__label">مستوى النضج المرتبط</span>' +
          '<span class="wq-evidence-assessment-link__value">مستوى ' +
          level +
          "</span></div>"
        : "";

    return (
      '<div class="wq-evidence-assessment-link">' +
      '<h4 class="wq-evidence-assessment-link__title">علاقة التقييم</h4>' +
      '<div class="wq-evidence-assessment-link__row">' +
      '<span class="wq-evidence-assessment-link__label">المتطلب المرتبط</span>' +
      '<span class="wq-evidence-assessment-link__value">' +
      escapeHtml(item.mq_id) +
      "</span></div>" +
      (typeLabel
        ? '<div class="wq-evidence-assessment-link__row">' +
          '<span class="wq-evidence-assessment-link__label">نوع الدليل</span>' +
          '<span class="wq-evidence-assessment-link__value">' +
          escapeHtml(typeLabel) +
          "</span></div>"
        : "") +
      '<div class="wq-evidence-assessment-link__row">' +
      '<span class="wq-evidence-assessment-link__label">دور الدليل</span>' +
      '<span class="wq-evidence-assessment-link__value">دليل مُستخدَم في التقييم</span></div>' +
      levelRow +
      "</div>"
    );
  }

  // "المرفقات" -- عرض فقط لمصفوفة attachments الجاهزة إن وُجدت. كل حقل
  // (name/type/size/date/path) اختياري تماماً -- لا رفع حقيقي، لا Backend،
  // لا Workflow، فقط سرد. أيقونة عرض فقط حسب type (بلا فتح فعلي -- المثال
  // المعطى صراحة يعرض اسم الملف فقط بلا زر).
  const EVIDENCE_ATTACHMENT_ICONS = {
    PDF: "📄",
    DOCX: "📄",
    XLSX: "📄",
    PNG: "🖼",
    JPG: "🖼",
    JPEG: "🖼",
  };

  function evidenceAttachmentsSectionHtml(item) {
    const attachments = item.attachments;
    if (!attachments || attachments.length === 0) return "";

    const rowsHtml = attachments
      .filter(function (a) {
        return a.name;
      })
      .map(function (a) {
        const icon = EVIDENCE_ATTACHMENT_ICONS[String(a.type || "").toUpperCase()] || "📎";
        const metaParts = [a.type, a.size, a.date].filter(Boolean);
        const metaHtml = metaParts.length
          ? '<span class="wq-evidence-attachment-item__meta">' + escapeHtml(metaParts.join(" · ")) + "</span>"
          : "";
        return (
          '<li class="wq-evidence-attachment-item">' +
          '<span class="wq-evidence-attachment-item__icon" aria-hidden="true">' +
          icon +
          "</span>" +
          '<span class="wq-evidence-attachment-item__name">' +
          escapeHtml(a.name) +
          "</span>" +
          metaHtml +
          "</li>"
        );
      })
      .join("");

    if (!rowsHtml) return "";

    return (
      '<div class="wq-evidence-attachments">' +
      '<h4 class="wq-evidence-attachments__title">المرفقات</h4>' +
      '<ul class="wq-evidence-attachments__list">' +
      rowsHtml +
      "</ul>" +
      "</div>"
    );
  }

  // "تفاصيل الدليل" -- يعرض فقط الحقول الموجودة فعلياً على العنصر (لا
  // Placeholder وهمي لأي حقل غائب). صف "الحالة" يعرض شارة دورة الحياة
  // (evidenceStatusBadgeHtml) بدل النص الخام -- بند 5.
  function evidenceMetadataPanelHtml(item) {
    const plainRows = [
      ["اسم الملف", item.file_name],
      ["نوع الملف", item.file_type],
      ["التاريخ", item.date],
      ["المالك", item.owner],
      ["المشاركون", item.participants],
      ["رافع الدليل", item.uploaded_by],
      ["المراجع", item.reviewer],
      ["رقم الإصدار", item.version],
      ["تاريخ آخر تحديث", item.last_updated_date],
      ["تاريخ المراجعة", item.review_date],
      ["ملاحظات المراجع", item.reviewer_notes],
    ]
      .filter(function (row) {
        return row[1];
      })
      .map(function (row) {
        return (
          '<div class="wq-evidence-metadata__row">' +
          '<span class="wq-evidence-metadata__label">' +
          escapeHtml(row[0]) +
          "</span>" +
          '<span class="wq-evidence-metadata__value">' +
          escapeHtml(row[1]) +
          "</span>" +
          "</div>"
        );
      })
      .join("");

    const statusRow = item.status
      ? '<div class="wq-evidence-metadata__row">' +
        '<span class="wq-evidence-metadata__label">الحالة</span>' +
        evidenceStatusBadgeHtml(item.status) +
        "</div>"
      : "";

    return (
      '<div class="wq-evidence-metadata">' +
      '<h4 class="wq-evidence-metadata__title">تفاصيل الدليل</h4>' +
      statusRow +
      plainRows +
      "</div>"
    );
  }

  // "ملخص التدقيق" -- بطاقة تجميعية للحقول الموجودة أصلاً (owner/reviewer/
  // version/review_date/status) بلا أي منطق إضافي، ولا حساب جديد. القسم
  // بالكامل غائب إن لم يتوفر ولو حقل واحد من الخمسة.
  function evidenceAuditSummaryHtml(item) {
    const rows = [
      ["مالك الدليل", item.owner],
      ["المراجع", item.reviewer],
      ["الإصدار الحالي", item.version],
      ["آخر مراجعة", item.review_date],
    ]
      .filter(function (row) {
        return row[1];
      })
      .map(function (row) {
        return (
          '<div class="wq-evidence-audit-summary__row">' +
          '<span class="wq-evidence-audit-summary__label">' +
          escapeHtml(row[0]) +
          "</span>" +
          '<span class="wq-evidence-audit-summary__value">' +
          escapeHtml(row[1]) +
          "</span>" +
          "</div>"
        );
      })
      .join("");

    const statusRow = item.status
      ? '<div class="wq-evidence-audit-summary__row">' +
        '<span class="wq-evidence-audit-summary__label">حالة دورة الحياة</span>' +
        evidenceStatusBadgeHtml(item.status) +
        "</div>"
      : "";

    if (!rows && !statusRow) return "";

    return (
      '<div class="wq-evidence-audit-summary">' +
      '<h4 class="wq-evidence-audit-summary__title">ملخص التدقيق</h4>' +
      rows +
      statusRow +
      "</div>"
    );
  }

  // "حالة التحقق" -- عرض فقط لقيمة validation_status الجاهزة إن وُجدت. لا
  // حساب ولا Workflow حقيقي؛ القسم بالكامل غائب عند غياب الحقل.
  function evidenceValidationSectionHtml(item) {
    if (!item.validation_status) return "";
    const badgeAttr =
      item.validation_status === "مراجع" ? "pass" : item.validation_status === "غير مراجع" ? "fail" : "pending";

    // حقول إضافية اختيارية (تم التحقق بواسطة/تاريخ التحقق/ملاحظات) -- نفس
    // نمط الصفوف المستخدَم في وحدات أخرى (Label/Value)، تُعرض فقط إن وُجدت.
    const extraRows = [
      ["تم التحقق بواسطة", item.verified_by],
      ["تاريخ التحقق", item.verification_date],
      ["ملاحظات التحقق", item.validation_notes],
    ]
      .filter(function (row) {
        return row[1];
      })
      .map(function (row) {
        return (
          '<div class="wq-evidence-validation__row">' +
          '<span class="wq-evidence-validation__label">' +
          escapeHtml(row[0]) +
          "</span>" +
          '<span class="wq-evidence-validation__value">' +
          escapeHtml(row[1]) +
          "</span>" +
          "</div>"
        );
      })
      .join("");

    return (
      '<div class="wq-evidence-validation">' +
      '<h4 class="wq-evidence-validation__title">التحقق من الدليل</h4>' +
      '<div class="wq-evidence-validation__row">' +
      '<span class="wq-evidence-validation__label">حالة التحقق</span>' +
      '<span class="wq-status-badge" data-status="' +
      badgeAttr +
      '"><span class="wq-status-badge__dot"></span>' +
      escapeHtml(item.validation_status) +
      "</span>" +
      "</div>" +
      extraRows +
      "</div>"
    );
  }

  // "دورة حياة الدليل" -- عرض رأسي فقط لمراحل lifecycle_history الجاهزة
  // إن وُجدت (Draft/Submitted/Under Review/Approved بالترتيب الثابت
  // دائماً)، كل مرحلة تعرض التاريخ + الشخص المسؤول إن وُجد. أي مرحلة
  // غائبة من الكائن لا تُعرض؛ القسم بالكامل غائب إن غاب الحقل أو كان فارغاً.
  function evidenceLifecycleHistorySectionHtml(item) {
    const history = item.lifecycle_history;
    if (!history) return "";

    const steps = EVIDENCE_LIFECYCLE_PROGRESSION.filter(function (stage) {
      return history[stage] && history[stage].date;
    }).map(function (stage) {
      const entry = history[stage];
      const personRow = entry.responsible_person
        ? '<span class="wq-evidence-lifecycle__step-person">' + escapeHtml(entry.responsible_person) + "</span>"
        : "";
      return (
        '<li class="wq-evidence-lifecycle__step">' +
        '<span class="wq-evidence-lifecycle__step-label">' +
        escapeHtml(arDisplay(VISUAL_EVIDENCE_STATUS_AR, stage)) +
        "</span>" +
        '<span class="wq-evidence-lifecycle__step-date">' +
        escapeHtml(entry.date) +
        "</span>" +
        personRow +
        "</li>"
      );
    });

    if (steps.length === 0) return "";

    return (
      '<div class="wq-evidence-lifecycle">' +
      '<h4 class="wq-evidence-lifecycle__title">دورة حياة الدليل</h4>' +
      '<ol class="wq-evidence-lifecycle__list">' +
      steps.join("") +
      "</ol>" +
      "</div>"
    );
  }

  // "سجل التدقيق" (Audit Trail Layer) -- Timeline رأسي فقط لمصفوفة
  // audit_trail الاختيارية إن وُجدت (تاريخ/جهة فاعلة/إجراء)، بلا أي Editing
  // أو Workflow أو منطق اعتماد -- عرض تسلسلي بالترتيب المخزَّن في الملف
  // فقط. أي سجل ناقص (بلا التواريخ الثلاثة معاً) يُستبعَد بصمت بدل عرضه
  // جزئياً؛ القسم بالكامل غائب عند غياب الحقل أو خلوّه من سجلات صالحة.
  function evidenceHasAuditTrail(item) {
    return !!(item.audit_trail && item.audit_trail.length > 0);
  }

  function evidenceAuditTrailSectionHtml(item) {
    const trail = item.audit_trail;
    if (!trail || trail.length === 0) return "";

    const itemsHtml = trail
      .filter(function (entry) {
        return entry.date && entry.actor && entry.action;
      })
      .map(function (entry) {
        return (
          '<li class="wq-evidence-audit-item">' +
          '<span class="wq-evidence-audit-item__date">' +
          escapeHtml(entry.date) +
          "</span>" +
          '<span class="wq-evidence-audit-item__actor">' +
          escapeHtml(entry.actor) +
          "</span>" +
          '<span class="wq-evidence-audit-item__action">' +
          escapeHtml(arDisplay(VISUAL_EVIDENCE_AUDIT_ACTION_AR, entry.action)) +
          "</span>" +
          "</li>"
        );
      })
      .join("");

    if (!itemsHtml) return "";

    return (
      '<div class="wq-evidence-audit-trail">' +
      '<h4 class="wq-evidence-audit-trail__title">سجل التدقيق</h4>' +
      '<ul class="wq-evidence-audit-trail__list">' +
      itemsHtml +
      "</ul>" +
      "</div>"
    );
  }

  // "سجل الإصدارات" -- عرض فقط لمصفوفة version_history الجاهزة إن وُجدت.
  // بلا أي Workflow للتعديل -- سرد فقط بالترتيب المخزَّن في الملف.
  function evidenceVersionHistorySectionHtml(item) {
    const history = item.version_history;
    if (!history || history.length === 0) return "";

    const rowsHtml = history
      .map(function (entry) {
        return (
          '<li class="wq-evidence-version__row">' +
          '<span class="wq-evidence-version__number">الإصدار ' +
          escapeHtml(entry.version) +
          "</span>" +
          '<span class="wq-evidence-version__note">' +
          escapeHtml(entry.note) +
          "</span>" +
          "</li>"
        );
      })
      .join("");

    return (
      '<div class="wq-evidence-version">' +
      '<h4 class="wq-evidence-version__title">سجل الإصدارات</h4>' +
      '<ul class="wq-evidence-version__list">' +
      rowsHtml +
      "</ul>" +
      "</div>"
    );
  }

  /* ---------------------------------------------------------------- */
  /* Evidence Export Engine (طبقة تصدير حزم الأدلة) -- زر + معاينة عرض فقط،
     بلا أي Backend حقيقي أو تنزيل فعلي أو حساب جديد. "معلومات الحزمة"
     (Evidence Package Summary، بند 2 من هذه المواصفة) هي أول قسم داخل
     المعاينة تحديداً (بند 3: "بداية الحزمة")، تليها بقية الأقسام المُعاد
     استخدامها حرفياً من دوالها الأصلية بالترتيب المطلوب: معلومات الحزمة ->
     ربط التقييم -> البيانات الوصفية -> دورة الحياة -> سجل التدقيق -> سجل
     الإصدارات -> العلاقات -> المرفقات -> التحقق. كل قسم يُغلَّف بكلاس جديد
     مستقل (.wq-evidence-export-section) لإعطاء المعاينة "تصميماً مستقلاً"
     (بند 3) بلا أي تعديل على كلاسات الأقسام الأصلية نفسها؛ الأقسام الفارغة
     لا تُغلَّف ولا تظهر إطلاقاً (لا صناديق فارغة). */
  /* ---------------------------------------------------------------- */

  // "معلومات الحزمة" -- سبعة حقول جاهزة فقط (معرف/اسم/نوع/متطلب مرتبط/
  // حالة حالية/حالة صحة/حالة تحقق)؛ حالة صحة الدليل محسوبة دائماً
  // (evidenceHealthStatus لا تُرجع أبداً فارغاً)، وبقية الحقول تُعرض فقط
  // إن وُجدت فعلياً -- بلا أي قيمة مخترَعة. يُعاد استخدام صفوف
  // .wq-evidence-metadata__row/__label/__value الموجودة أصلاً (بلا تعديل
  // عليها) بدل ابتكار كلاس صفوف جديد لم يُطلَب في هذه المواصفة.
  function evidencePackageSummarySectionHtml(item) {
    function row(label, valueHtml) {
      return (
        '<div class="wq-evidence-metadata__row">' +
        '<span class="wq-evidence-metadata__label">' +
        escapeHtml(label) +
        "</span>" +
        valueHtml +
        "</div>"
      );
    }
    function textValue(value) {
      return '<span class="wq-evidence-metadata__value">' + escapeHtml(value) + "</span>";
    }

    const plainRows = [
      ["معرف الدليل", item.evidence_code],
      ["اسم الدليل", item.title],
      ["نوع الدليل", item.category],
      ["المتطلب المرتبط (MQ)", item.mq_id],
    ]
      .filter(function (r) {
        return r[1];
      })
      .map(function (r) {
        return row(r[0], textValue(r[1]));
      })
      .join("");

    const statusRow = item.status ? row("الحالة الحالية", evidenceStatusBadgeHtml(item.status)) : "";
    const healthRow = row("حالة صحة الدليل", evidenceHealthStatusBadgeHtml(evidenceHealthStatus(item)));
    const validationRow = item.validation_status ? row("حالة التحقق", textValue(item.validation_status)) : "";

    return (
      '<div class="wq-evidence-export-section">' +
      '<h4 class="wq-evidence-export-section__title">معلومات الحزمة</h4>' +
      plainRows +
      statusRow +
      healthRow +
      validationRow +
      "</div>"
    );
  }

  // يغلّف قسماً مُعاد استخدامه (نتيجة دالة أصلية جاهزة) بكلاس المعاينة
  // الجديد -- بلا أي قسم فارغ (إن أرجعت الدالة الأصلية "" لعدم توفر
  // بياناتها، لا يظهر أي صندوق فارغ هنا أيضاً).
  function evidenceExportSectionWrap(sectionHtml) {
    return sectionHtml ? '<div class="wq-evidence-export-section">' + sectionHtml + "</div>" : "";
  }

  function evidenceExportPreviewSectionsHtml(item) {
    return (
      evidencePackageSummarySectionHtml(item) +
      evidenceExportSectionWrap(evidenceAssessmentLinkHtml(item)) +
      evidenceExportSectionWrap(evidenceMetadataPanelHtml(item)) +
      evidenceExportSectionWrap(evidenceLifecycleHistorySectionHtml(item)) +
      evidenceExportSectionWrap(evidenceAuditTrailSectionHtml(item)) +
      evidenceExportSectionWrap(evidenceVersionHistorySectionHtml(item)) +
      evidenceExportSectionWrap(evidenceRelationshipsSectionHtml(item)) +
      evidenceExportSectionWrap(evidenceAttachmentsSectionHtml(item)) +
      evidenceExportSectionWrap(evidenceValidationSectionHtml(item))
    );
  }

  // ملاحظة إصلاح (مرحلة التدقيق النهائي): المعاينة تُترَك فارغة عند البناء
  // الأولي بدل تضمين نسخة كاملة من كل الأقسام (بما فيها أزرار "فتح الحزمة"
  // الحية داخل العلاقات) مخفية بـCSS فقط -- كانت هذه النسخة المخفية تسبق
  // القسم الظاهر الفعلي في ترتيب DOM، فتُعطي نتيجة خاطئة لأي بحث بـ
  // querySelector المفرد (يُرجع أول تطابق) رغم أن النقر الفعلي بالفأرة كان
  // يعمل بشكل صحيح دائماً (Hit-testing يتجاهل العناصر المخفية). المحتوى
  // يُبنى الآن مرة واحدة فقط عند أول فتح فعلي للمعاينة (انظر مستمع النقر
  // في wireVisualEvidenceActions)، فلا تُوجد أي نسخة مكرَّرة من عناصر
  // تفاعلية في DOM قبل أن يطلبها المستخدم صراحة.
  function evidenceExportPackageHtml(item) {
    return (
      '<div class="wq-evidence-export">' +
      '<button type="button" class="wq-evidence-export__trigger" data-visual-evidence-id="' +
      escapeHtml(item.visual_evidence_id) +
      '">تصدير حزمة الدليل</button>' +
      '<div class="wq-evidence-export__preview" data-open="false"></div>' +
      "</div>"
    );
  }

  /* ---------------------------------------------------------------- */
  /* AI Evidence Assistant Preparation Layer (بند 4) -- واجهة جاهزة فقط، بلا
     أي AI حقيقي. كل حقل إما قيمة حقيقية موجودة أصلاً في Metadata (جاهزة/
     Metadata Ready) أو النص الثابت "No AI analysis available" حرفياً عند
     غياب أي إشارة حقيقية -- ممنوع صراحة إنشاء أي تحليل/اقتراح مُصطنَع. */
  /* ---------------------------------------------------------------- */

  const AI_NO_ANALYSIS_TEXT = "لا يتوفر تحليل ذكاء اصطناعي";

  // "Missing Information" -- قائمة حقيقية محسوبة من غياب حقول اختيارية
  // معروفة في المخطط نفسه (بلا أي تخمين)، تماماً كما تُستخدَم نفس الشروط
  // في أقسام أخرى من هذا الملف (evidenceHas*).
  function evidenceAiMissingInformationList(item) {
    const missing = [];
    if (!item.version) missing.push("رقم الإصدار");
    if (!evidenceHasAttachments(item)) missing.push("المرفقات");
    if (!item.participants) missing.push("المشاركون");
    if (!item.reviewer) missing.push("المراجع");
    if (!item.validation_status) missing.push("حالة التحقق");
    if (!evidenceHasRelationships(item)) missing.push("العلاقات (Relationships)");
    if (!evidenceHasLifecycle(item)) missing.push("دورة حياة الدليل");
    if (!evidenceHasAuditTrail(item)) missing.push("سجل التدقيق (Audit Trail)");
    return missing;
  }

  // "Related Evidence" -- إعادة استخدام حرفية لبيانات Evidence Relationships
  // الحقيقية الموجودة أصلاً (بند العلاقات من الجولة السابقة)، بلا أي حساب
  // أو تخمين جديد.
  function evidenceAiRelatedEvidenceText(item) {
    if (!evidenceHasRelationships(item)) return null;
    const rel = item.relationships;
    const codes = []
      .concat(rel.supports || [])
      .concat(rel.related_evidence || [])
      .concat(rel.related_requirements || []);
    return codes
      .map(function (code) {
        const name = resolveRelationshipTargetName(code);
        return name ? code + " — " + name : code;
      })
      .join("، ");
  }

  function evidenceAiAnalysisPanelHtml(item) {
    const summary = item.description || AI_NO_ANALYSIS_TEXT;

    const missingList = evidenceAiMissingInformationList(item);
    const missing = missingList.length > 0 ? missingList.join("، ") : AI_NO_ANALYSIS_TEXT;

    // لا يوجد أي حقل بيانات حقيقي في المخطط الحالي يمثّل "اقتراحات تحقق" --
    // النص الثابت هنا دائماً، بلا استثناء، لتجنّب أي تحليل مُصطنَع.
    const validationSuggestions = AI_NO_ANALYSIS_TEXT;

    const related = evidenceAiRelatedEvidenceText(item) || AI_NO_ANALYSIS_TEXT;
    const improvement = item.reviewer_notes || item.validation_notes || AI_NO_ANALYSIS_TEXT;

    const rowsHtml = [
      ["ملخص الدليل", summary],
      ["معلومات ناقصة", missing],
      ["اقتراحات التحقق", validationSuggestions],
      ["أدلة مرتبطة", related],
      ["ملاحظات التحسين", improvement],
    ]
      .map(function (row) {
        return (
          '<div class="wq-ai-evidence-panel__row">' +
          '<span class="wq-ai-evidence-panel__label">' +
          escapeHtml(row[0]) +
          "</span>" +
          '<span class="wq-ai-evidence-panel__value">' +
          escapeHtml(row[1]) +
          "</span>" +
          "</div>"
        );
      })
      .join("");

    return (
      '<div class="wq-ai-evidence-panel">' +
      '<h4 class="wq-ai-evidence-panel__title">معاينة تحليل الذكاء الاصطناعي</h4>' +
      '<p class="wq-ai-evidence-panel__disclaimer">تحضير بيانات فقط — بلا أي تحليل ذكاء اصطناعي حقيقي.</p>' +
      rowsHtml +
      "</div>"
    );
  }

  // Evidence Viewer Modal -- نفس مكوّن Modal الموجود أصلاً (overlay/title/
  // body)، بمحتوى جديد بالكامل يستبدل ما كان معروضاً فيه (سواء كان فارغاً
  // أو محتوى Evidence Detail Modal الذي فُتح منه هذا العنصر). عرض ومتابعة
  // فقط -- لا قراءة أو تعديل لأي من ملفات النضج/الامتثال/التميز التشغيلي.
  // يجمع أي أقسام فرعية غير فارغة داخل <details> واحد قابل للطي (Progressive
  // Disclosure -- بند 9 من مواصفة UI/UX). لا يغيّر أي دالة قسم بذاتها ولا
  // البيانات التي تقرأها؛ فقط يغلّف نصوص HTML الجاهزة أصلاً. إن كانت كل
  // الأقسام فارغة (كل الحقول غائبة عن هذا العنصر تحديداً)، لا يُطبع أي شيء
  // -- نفس سلوك كل دالة قسم أخرى هنا حين لا توجد بيانات.
  function evidenceMoreDetailsHtml(sectionsHtml) {
    const combined = sectionsHtml.filter(Boolean).join("");
    if (!combined) return "";
    return (
      '<details class="wq-evidence-more-details">' +
      '<summary class="wq-evidence-more-details__summary">' +
      "<span>تفاصيل إضافية وسجل النشاط</span>" +
      '<svg class="wq-evidence-more-details__icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>' +
      "</summary>" +
      '<div class="wq-evidence-more-details__body">' +
      combined +
      "</div>" +
      "</details>"
    );
  }

  function openEvidenceViewerModal(item) {
    const overlay = document.getElementById("wq-modal-overlay");
    const modal = overlay.querySelector(".wq-modal");
    const title = document.getElementById("wq-modal-title");
    const body = document.getElementById("wq-modal-body");

    title.textContent = item.title;
    // عرض أوسع لهذا العارض تحديداً (محتوى أطول بكثير من مودال تفاصيل
    // الفجوة البسيط) -- عرض/إغلاق فقط، بلا تغيير على radius/padding/بنية
    // الرأس. تُزال في closeModal() وفي openEvidenceModal() (المودال
    // البسيط) حتى لا تبقى عالقة على الاستخدام التالي للمودال المشترك.
    if (modal) modal.classList.add("wq-modal--wide");

    // Evidence Package Viewer 1.0 -- الترتيب الثابت المطلوب (بعد Evidence
    // Governance Expansion Layer): نظرة عامة -> علاقة التقييم -> العلاقات
    // -> البيانات الوصفية -> الأدلة المرئية (المعاينة) -> دورة الحياة ->
    // سجل التدقيق (جديد) -> سجل الإصدارات -> المرفقات -> التحقق -> AI
    // Analysis Preview (جديد، دائماً في النهاية). ملخص التدقيق (من جولة
    // سابقة) يبقى في أعلى المحتوى كملخص سريع. زر Export Evidence Package
    // (جديد) يُدرَج مباشرة تحت الرأس -- عرض فقط، بلا Backend حقيقي.
    //
    // Progressive Disclosure (UI/UX): المحتوى الأساسي (نظرة عامة/علاقة
    // التقييم/البيانات الوصفية/المعاينة/المرفقات) يبقى ظاهراً دوماً؛
    // الأقسام الأعمق (العلاقات/دورة الحياة/سجل التدقيق/سجل الإصدارات/
    // التحقق/AI) تُجمَّع خلف "تفاصيل إضافية وسجل النشاط" قابلة للطي --
    // نفس الترتيب الثابت أعلاه، فقط معروضة بشكل مختلف.
    body.innerHTML =
      '<div class="wq-evidence-package">' +
      '<div class="wq-evidence-viewer__header">' +
      '<span class="wq-visual-evidence-badge">' +
      escapeHtml(arDisplay(VISUAL_EVIDENCE_CATEGORY_AR, item.category)) +
      "</span>" +
      '<span class="wq-evidence-viewer__code">' +
      escapeHtml(item.evidence_code) +
      "</span>" +
      '<span class="wq-evidence-viewer__mq">' +
      escapeHtml(item.mq_id) +
      "</span>" +
      "</div>" +
      evidenceExportPackageHtml(item) +
      evidenceAuditSummaryHtml(item) +
      evidencePackageOverviewHtml(item) +
      evidenceAssessmentLinkHtml(item) +
      evidenceMetadataPanelHtml(item) +
      '<div class="wq-evidence-preview" id="wq-evidence-preview">' +
      '<p class="wq-evidence-preview__loading">جارٍ التحقق من توفر الملف…</p>' +
      "</div>" +
      evidenceAttachmentsSectionHtml(item) +
      evidenceMoreDetailsHtml([
        evidenceRelationshipsSectionHtml(item),
        evidenceLifecycleHistorySectionHtml(item),
        evidenceAuditTrailSectionHtml(item),
        evidenceVersionHistorySectionHtml(item),
        evidenceValidationSectionHtml(item),
        evidenceAiAnalysisPanelHtml(item),
      ]) +
      "</div>";

    overlay.setAttribute("data-open", "true");
    loadEvidencePreview(item);
  }

  // تفويض نقر واحد على مستوى body -- يغطي أزرار البطاقات داخل Modal تفاصيل
  // الدليل وداخل قسم "مستودع الأدلة المرئية" المستقل معاً، بلا الحاجة
  // لوصل الحدث في أكثر من مكان.
  function wireVisualEvidenceActions() {
    document.body.addEventListener("click", function (event) {
      const button = event.target.closest(".wq-visual-evidence-card__action");
      if (!button || button.disabled) return;
      event.stopPropagation();
      const item = visualEvidenceById(button.getAttribute("data-visual-evidence-id"));
      if (item) openEvidenceViewerModal(item);
    });

    // زر "فتح الحزمة" داخل بطاقات العلاقات (Evidence Relationships) --
    // ينقل التنقّل إلى نفس Evidence Package Viewer لدليل مرئي آخر موجود
    // فعلياً، بنفس آلية الفتح تماماً، بلا أي منطق تقييم جديد.
    document.body.addEventListener("click", function (event) {
      const button = event.target.closest(".wq-evidence-related-item__open");
      if (!button) return;
      event.stopPropagation();
      const item = visualEvidenceById(button.getAttribute("data-visual-evidence-id"));
      if (item) openEvidenceViewerModal(item);
    });

    // زر "تصدير حزمة الدليل" -- عرض/إخفاء معاينة التصدير المجاورة فقط
    // (toggle على data-open)؛ بلا أي تنزيل أو Backend حقيقي. المحتوى يُبنى
    // مرة واحدة فقط عند أول فتح فعلي (بدل تضمينه مسبقاً بالكامل مخفياً)،
    // لتفادي وجود نسخة مكرَّرة من عناصر تفاعلية (كأزرار "فتح الحزمة" داخل
    // العلاقات) في DOM قبل أن يطلبها المستخدم صراحة.
    document.body.addEventListener("click", function (event) {
      const button = event.target.closest(".wq-evidence-export__trigger");
      if (!button) return;
      event.stopPropagation();
      const preview = button.parentElement.querySelector(".wq-evidence-export__preview");
      if (!preview) return;
      const isOpen = preview.getAttribute("data-open") === "true";
      if (!isOpen && !preview.innerHTML) {
        const item = visualEvidenceById(button.getAttribute("data-visual-evidence-id"));
        if (item) {
          preview.innerHTML =
            '<h4 class="wq-evidence-export__preview-title">معاينة تصدير حزمة الدليل</h4>' +
            evidenceExportPreviewSectionsHtml(item);
        }
      }
      preview.setAttribute("data-open", isOpen ? "false" : "true");
      button.textContent = isOpen ? "تصدير حزمة الدليل" : "إخفاء معاينة التصدير";
    });
  }

  /* ---------------------------------------------------------------- */
  /* Visual Evidence Repository -- قسم مستقل، بعد مستودع الأدلة مباشرة     */
  /* ---------------------------------------------------------------- */

  let activeVisualEvidenceMqFilter = "ALL";
  let activeVisualEvidenceCategoryFilter = "ALL";
  let activeVisualEvidenceStatusFilter = "ALL";
  let activeVisualEvidenceDateFilter = "ALL";
  let activeVisualEvidenceVersionFilter = "ALL";
  let activeVisualEvidenceUploaderFilter = "ALL";
  let activeVisualEvidenceReviewerFilter = "ALL";
  let activeVisualEvidenceHealthFilter = "ALL";
  let activeVisualEvidenceValidationFilter = "ALL";
  let activeVisualEvidenceRelationshipFilter = "ALL";
  let activeVisualEvidenceExportReadyFilter = "ALL";
  let activeVisualEvidenceAttachmentsFilter = "ALL";
  let activeVisualEvidenceLifecycleFilter = "ALL";
  let activeVisualEvidenceSearchQuery = "";
  // بند 5: تبديل عرض بطاقات/جدول -- عرض فقط، بلا أي أثر على الفلاتر أو
  // البيانات المفلترة نفسها (filteredVisualEvidenceItems لا تُستخدَم إلا
  // لتحديد أي العناصر تُعرَض، بصرف النظر عن شكل العرض).
  let visualEvidenceViewMode = "cards";

  function filteredVisualEvidenceItems() {
    const query = activeVisualEvidenceSearchQuery.trim().toLowerCase();
    return evidenceVisualCatalogState.filter(function (item) {
      if (activeVisualEvidenceMqFilter !== "ALL" && item.mq_id !== activeVisualEvidenceMqFilter) return false;
      if (activeVisualEvidenceCategoryFilter !== "ALL" && item.category !== activeVisualEvidenceCategoryFilter)
        return false;
      if (activeVisualEvidenceStatusFilter !== "ALL" && item.status !== activeVisualEvidenceStatusFilter)
        return false;
      if (activeVisualEvidenceDateFilter !== "ALL" && item.date !== activeVisualEvidenceDateFilter) return false;
      if (activeVisualEvidenceVersionFilter !== "ALL" && item.version !== activeVisualEvidenceVersionFilter)
        return false;
      if (activeVisualEvidenceUploaderFilter !== "ALL" && item.uploaded_by !== activeVisualEvidenceUploaderFilter)
        return false;
      if (activeVisualEvidenceReviewerFilter !== "ALL" && item.reviewer !== activeVisualEvidenceReviewerFilter)
        return false;
      // فلاتر عرض فقط (بند 6) -- لا تدخل في أي حساب، فقط تقارن حالة جاهزة
      // (evidenceHealthStatus) أو وجود verified_by بحقل واحد.
      if (activeVisualEvidenceHealthFilter !== "ALL" && evidenceHealthStatus(item) !== activeVisualEvidenceHealthFilter)
        return false;
      if (activeVisualEvidenceValidationFilter === "Validated" && !evidenceHasValidation(item)) return false;
      if (activeVisualEvidenceValidationFilter === "Not Validated" && evidenceHasValidation(item)) return false;
      // فلتر عرض فقط (بند 6 -- Relationship Status) -- يقارن فقط ناتج
      // evidenceHasRelationships() الجاهز، بلا أي أثر على الحسابات.
      if (activeVisualEvidenceRelationshipFilter === "Has Relationships" && !evidenceHasRelationships(item))
        return false;
      if (activeVisualEvidenceRelationshipFilter === "No Relationships" && evidenceHasRelationships(item))
        return false;
      // فلاتر عرض فقط جديدة (بند 6 من طبقة تصدير حزم الأدلة) -- "جاهز
      // للتصدير" يعني حرفياً item.status === "Approved" (الحالة الوحيدة
      // المعتمدة رسمياً)، بلا أي حساب جديد أو علاقة بالتقييم. "يحتوي
      // مرفقات" و"حالة دورة الحياة" يعيدان استخدام evidenceHasAttachments/
      // evidenceHasLifecycle الجاهزتين حرفياً.
      if (activeVisualEvidenceExportReadyFilter === "Ready" && item.status !== "Approved") return false;
      if (activeVisualEvidenceExportReadyFilter === "Not Ready" && item.status === "Approved") return false;
      if (activeVisualEvidenceAttachmentsFilter === "Has Attachments" && !evidenceHasAttachments(item))
        return false;
      if (activeVisualEvidenceAttachmentsFilter === "No Attachments" && evidenceHasAttachments(item))
        return false;
      if (activeVisualEvidenceLifecycleFilter === "Has Lifecycle" && !evidenceHasLifecycle(item)) return false;
      if (activeVisualEvidenceLifecycleFilter === "No Lifecycle" && evidenceHasLifecycle(item)) return false;
      if (query) {
        const haystack = (String(item.title || "") + " " + String(item.description || "")).toLowerCase();
        if (haystack.indexOf(query) === -1) return false;
      }
      return true;
    });
  }

  // قيم مميّزة لحقل اختياري عبر كل الأدلة المرئية -- تتجاهل العناصر التي لا
  // تحمل الحقل (بدل عرض خيار فلترة فارغ/undefined). تُستخدَم لبناء خيارات
  // فلاتر الإصدار/رافع الدليل/المراجع ديناميكياً من البيانات الفعلية فقط.
  function distinctVisualEvidenceValues(fieldName) {
    return Array.from(
      new Set(
        evidenceVisualCatalogState
          .map(function (i) {
            return i[fieldName];
          })
          .filter(Boolean)
      )
    ).sort();
  }

  function visualEvidenceFilterGroupHtml(groupLabel, options, activeValue, filterKey, extraClass) {
    return (
      '<div class="wq-visual-evidence-filter-group' +
      (extraClass ? " " + extraClass : "") +
      '">' +
      '<span class="wq-visual-evidence-filter-group__label">' +
      escapeHtml(groupLabel) +
      "</span>" +
      '<div class="wq-visual-evidence-filter-group__buttons">' +
      options
        .map(function (opt) {
          return (
            '<button type="button" class="wq-filter-btn" data-filter-key="' +
            filterKey +
            '" data-filter-value="' +
            escapeHtml(opt.value) +
            '" aria-pressed="' +
            (opt.value === activeValue) +
            '">' +
            escapeHtml(opt.label) +
            "</button>"
          );
        })
        .join("") +
      "</div>" +
      "</div>"
    );
  }

  function renderVisualEvidenceFilters() {
    const bar = document.getElementById("wq-visual-evidence-filters");
    const items = evidenceVisualCatalogState;

    const mqIds = Array.from(
      new Set(
        items.map(function (i) {
          return i.mq_id;
        })
      )
    ).sort();
    const statuses = Array.from(
      new Set(
        items.map(function (i) {
          return i.status;
        })
      )
    ).sort();
    const dates = Array.from(
      new Set(
        items.map(function (i) {
          return i.date;
        })
      )
    ).sort();

    bar.innerHTML =
      visualEvidenceFilterGroupHtml(
        "المتطلب",
        [{ value: "ALL", label: "الكل" }].concat(
          mqIds.map(function (id) {
            return { value: id, label: id };
          })
        ),
        activeVisualEvidenceMqFilter,
        "mq"
      ) +
      visualEvidenceFilterGroupHtml(
        "الفئة",
        [{ value: "ALL", label: "الكل" }].concat(
          VISUAL_EVIDENCE_CATEGORIES.map(function (c) {
            return { value: c, label: arDisplay(VISUAL_EVIDENCE_CATEGORY_AR, c) };
          })
        ),
        activeVisualEvidenceCategoryFilter,
        "category"
      ) +
      visualEvidenceFilterGroupHtml(
        "الحالة",
        [{ value: "ALL", label: "الكل" }].concat(
          statuses.map(function (s) {
            return { value: s, label: arDisplay(VISUAL_EVIDENCE_STATUS_AR, s) };
          })
        ),
        activeVisualEvidenceStatusFilter,
        "status"
      ) +
      visualEvidenceFilterGroupHtml(
        "التاريخ",
        [{ value: "ALL", label: "الكل" }].concat(
          dates.map(function (d) {
            return { value: d, label: d };
          })
        ),
        activeVisualEvidenceDateFilter,
        "date"
      ) +
      visualEvidenceFilterGroupHtml(
        "الإصدار",
        [{ value: "ALL", label: "الكل" }].concat(
          distinctVisualEvidenceValues("version").map(function (v) {
            return { value: v, label: "الإصدار " + v };
          })
        ),
        activeVisualEvidenceVersionFilter,
        "version"
      ) +
      visualEvidenceFilterGroupHtml(
        "رافع الدليل",
        [{ value: "ALL", label: "الكل" }].concat(
          distinctVisualEvidenceValues("uploaded_by").map(function (u) {
            return { value: u, label: u };
          })
        ),
        activeVisualEvidenceUploaderFilter,
        "uploader"
      ) +
      visualEvidenceFilterGroupHtml(
        "المراجع",
        [{ value: "ALL", label: "الكل" }].concat(
          distinctVisualEvidenceValues("reviewer").map(function (r) {
            return { value: r, label: r };
          })
        ),
        activeVisualEvidenceReviewerFilter,
        "reviewer"
      ) +
      // الثلاث مجموعات التالية كانت بالإنجليزية بالكامل (عنوان المجموعة
      // والخيارات معاً) -- ترجمة عرض فقط، بلا تغيير على data-filter-value
      // الداخلية (Arabic Cleanup Pass).
      visualEvidenceFilterGroupHtml(
        "حالة الأدلة",
        [
          { value: "ALL", label: "الكل" },
          { value: "Healthy", label: arDisplay(VISUAL_EVIDENCE_HEALTH_AR, "Healthy") },
          { value: "Attention Required", label: arDisplay(VISUAL_EVIDENCE_HEALTH_AR, "Attention Required") },
          { value: "Incomplete", label: arDisplay(VISUAL_EVIDENCE_HEALTH_AR, "Incomplete") },
        ],
        activeVisualEvidenceHealthFilter,
        "health",
        "wq-evidence-health-filter"
      ) +
      visualEvidenceFilterGroupHtml(
        "حالة التحقق",
        [
          { value: "ALL", label: "الكل" },
          { value: "Validated", label: arDisplay(VISUAL_EVIDENCE_VALIDATION_AR, "Validated") },
          { value: "Not Validated", label: arDisplay(VISUAL_EVIDENCE_VALIDATION_AR, "Not Validated") },
        ],
        activeVisualEvidenceValidationFilter,
        "validation",
        "wq-evidence-health-filter"
      ) +
      visualEvidenceFilterGroupHtml(
        "حالة الارتباط",
        [
          { value: "ALL", label: "الكل" },
          { value: "Has Relationships", label: arDisplay(VISUAL_EVIDENCE_RELATIONSHIP_AR, "Has Relationships") },
          { value: "No Relationships", label: arDisplay(VISUAL_EVIDENCE_RELATIONSHIP_AR, "No Relationships") },
        ],
        activeVisualEvidenceRelationshipFilter,
        "relationship",
        "wq-evidence-health-filter"
      ) +
      visualEvidenceFilterGroupHtml(
        "جاهز للتصدير",
        [
          { value: "ALL", label: "الكل" },
          { value: "Ready", label: "جاهز" },
          { value: "Not Ready", label: "غير جاهز" },
        ],
        activeVisualEvidenceExportReadyFilter,
        "exportReady",
        "wq-evidence-health-filter"
      ) +
      visualEvidenceFilterGroupHtml(
        "يحتوي مرفقات",
        [
          { value: "ALL", label: "الكل" },
          { value: "Has Attachments", label: "يحتوي مرفقات" },
          { value: "No Attachments", label: "بلا مرفقات" },
        ],
        activeVisualEvidenceAttachmentsFilter,
        "attachments",
        "wq-evidence-health-filter"
      ) +
      visualEvidenceFilterGroupHtml(
        "حالة دورة الحياة",
        [
          { value: "ALL", label: "الكل" },
          { value: "Has Lifecycle", label: "تحتوي بيانات دورة حياة" },
          { value: "No Lifecycle", label: "بلا بيانات دورة حياة" },
        ],
        activeVisualEvidenceLifecycleFilter,
        "lifecycle",
        "wq-evidence-health-filter"
      );

    bar.querySelectorAll(".wq-filter-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const key = btn.getAttribute("data-filter-key");
        const value = btn.getAttribute("data-filter-value");
        if (key === "mq") activeVisualEvidenceMqFilter = value;
        if (key === "category") activeVisualEvidenceCategoryFilter = value;
        if (key === "status") activeVisualEvidenceStatusFilter = value;
        if (key === "date") activeVisualEvidenceDateFilter = value;
        if (key === "version") activeVisualEvidenceVersionFilter = value;
        if (key === "uploader") activeVisualEvidenceUploaderFilter = value;
        if (key === "reviewer") activeVisualEvidenceReviewerFilter = value;
        if (key === "health") activeVisualEvidenceHealthFilter = value;
        if (key === "validation") activeVisualEvidenceValidationFilter = value;
        if (key === "relationship") activeVisualEvidenceRelationshipFilter = value;
        if (key === "exportReady") activeVisualEvidenceExportReadyFilter = value;
        if (key === "attachments") activeVisualEvidenceAttachmentsFilter = value;
        if (key === "lifecycle") activeVisualEvidenceLifecycleFilter = value;
        renderVisualEvidenceFilters();
        renderEvidenceAnalytics();
        renderVisualEvidenceRepositoryList();
      });
    });
  }

  function renderVisualEvidenceRepositoryList() {
    const list = document.getElementById("wq-visual-evidence-repo-list");
    const items = filteredVisualEvidenceItems();

    if (evidenceVisualCatalogState.length === 0) {
      list.innerHTML = '<div class="wq-empty-state">لا تتوفر أدلة مرئية لهذا المجال.</div>';
      return;
    }
    if (items.length === 0) {
      list.innerHTML = '<div class="wq-empty-state">لا توجد أدلة مرئية ضمن هذا الفلتر.</div>';
      return;
    }
    if (visualEvidenceViewMode === "table") {
      list.innerHTML = evidenceManagementTableHtml(items);
      return;
    }
    list.innerHTML = items
      .map(function (item) {
        return visualEvidenceCardHtml(item, true);
      })
      .join("");
  }

  function renderVisualEvidenceRepository() {
    renderEvidenceHealthDashboard();
    renderEvidenceAnalytics();
    renderEvidenceCenter();
    renderVisualEvidenceFilters();
    renderVisualEvidenceRepositoryList();
  }

  // نفس أسلوب حقن الأقسام أعلاه (injectComplianceSection/
  // injectEvidenceRepositorySection) بالضبط -- بلا لمس index.html. يُدرَج
  // بعد مستودع الأدلة الحالي مباشرة وقبل بطاقات MQ. حاوية Evidence Center
  // الجديدة (بند 4) تُدرَج بعد Evidence Analytics مباشرة وقبل شريط البحث؛
  // زر تبديل العرض (بطاقات/جدول -- بند 5) يُدرَج بعد شريط البحث مباشرة --
  // عناصر إضافية جديدة فقط، بلا أي تعديل على العناصر الأخرى.
  // إعادة ترتيب (User Journey Restructuring Pass): تُدرَج الآن بعد Evidence
  // Repository مباشرة (نفس خطوة "الأدلة" في الرحلة) بدل قبل MQ Cards.
  // انظر تعليق injectEvidenceRepositorySection() أعلاه.
  function injectVisualEvidenceRepositorySection() {
    const anchor = document.getElementById("evidence-repository");
    const html =
      '<section class="wq-section" id="visual-evidence-repository" aria-labelledby="ve-repo-title">' +
      '<div class="wq-section__head">' +
      "<div>" +
      '<p class="wq-section__kicker">الفهرس والبيانات الوصفية</p>' +
      '<h2 class="wq-section__title" id="ve-repo-title">مستودع الأدلة المرئية</h2>' +
      '<p class="wq-section__hint">كل الأدلة المرئية المرتبطة بمتطلبات مجال تصنيف البيانات، قابلة للبحث والفلترة حسب المتطلب/الفئة/الحالة/التاريخ.</p>' +
      "</div>" +
      "</div>" +
      // ثلاث لوحات KPI منفصلة (Health Dashboard وحدها 6 بطاقات) كانت تُعرض
      // دائماً قبل شريط البحث نفسه -- لمستودع لا يتجاوز 6 عناصر إجمالاً
      // وقت كتابة هذا (data/evidence_visual_catalog.json)، أي بطاقة واحدة
      // تقريباً لكل عنصر فعلي. هذا "تحليل عن التحليل" قبل أن يرى المستخدم
      // العنصر الواحد نفسه -- عكس ترتيب القصة المطلوب (الدليل أولاً، ثم
      // التفاصيل عند الطلب). غُلِّفت الآن خلف Progressive Disclosure
      // (User Journey Restructuring Pass)، **مغلقة افتراضياً** بخلاف شريط
      // الفلاتر أعلاه (الفلترة إجراء أساسي يُستخدَم فوراً؛ لوحات الصحة/
      // التحليلات معلومات استقصائية ثانوية) -- بلا أي تغيير على
      // renderEvidenceHealthDashboard()/renderEvidenceAnalytics()/
      // renderEvidenceCenter() أو العناصر الهدف الثلاثة نفسها.
      '<details class="wq-evidence-more-details">' +
      '<summary class="wq-evidence-more-details__summary">' +
      "<span>لوحة صحة وتحليلات الأدلة المرئية</span>" +
      '<svg class="wq-evidence-more-details__icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>' +
      "</summary>" +
      '<div class="wq-evidence-more-details__body">' +
      '<div class="wq-evidence-health-dashboard" id="wq-evidence-health-dashboard"></div>' +
      '<div class="wq-evidence-analytics" id="wq-evidence-analytics"></div>' +
      '<div class="wq-evidence-center" id="wq-evidence-center"></div>' +
      "</div>" +
      "</details>" +
      '<input type="search" class="wq-visual-evidence-search" id="wq-visual-evidence-search" placeholder="ابحث بعنوان أو وصف الدليل المرئي…" />' +
      '<button type="button" class="wq-filter-btn" id="wq-visual-evidence-view-toggle" aria-pressed="false">عرض كجدول</button>' +
      // شريط الفلاتر (13 مجموعة) كان يُعرض مسطّحاً بالكامل دائماً -- كثافة
      // بصرية عالية بلا داعٍ حين لا يحتاج المستخدم فلترة فورية. غُلِّف بـ
      // Progressive Disclosure (نفس مكوّن .wq-evidence-more-details بصرياً،
      // انظر components.css) بلا تغيير على renderVisualEvidenceFilters() أو
      // العنصر الهدف #wq-visual-evidence-filters نفسه -- فقط غلاف عرض حوله.
      // كانت مفتوحة افتراضياً (open) في جولة سابقة بحجة "الفلترة إجراء
      // أساسي" -- لكن الفحص البصري الفعلي (Final UX Simplification Pass)
      // أظهر أن 13 مجموعة فلتر مفتوحة تدفع بطاقات الأدلة الفعلية خارج
      // الشاشة الأولى بالكامل تقريباً، أي "Analytics/Filters قبل Evidence"
      // حرفياً -- عكس المطلوب تماماً. أصبحت مغلقة افتراضياً؛ العنصر
      // الهدف وسلوك الفلترة نفسه لم يتغيّرا، فقط الحالة الافتراضية للعرض.
      '<details class="wq-filters-disclosure">' +
      '<summary class="wq-filters-disclosure__summary">' +
      "<span>خيارات الفلترة</span>" +
      '<svg class="wq-filters-disclosure__icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>' +
      "</summary>" +
      '<div class="wq-filters-disclosure__body">' +
      '<div class="wq-visual-evidence-filters" id="wq-visual-evidence-filters"></div>' +
      "</div>" +
      "</details>" +
      '<div class="wq-visual-evidence-repo-list" id="wq-visual-evidence-repo-list"></div>' +
      "</section>";
    anchor.insertAdjacentHTML("afterend", html);

    document.getElementById("wq-visual-evidence-search").addEventListener("input", function (event) {
      activeVisualEvidenceSearchQuery = event.target.value;
      renderEvidenceAnalytics();
      renderVisualEvidenceRepositoryList();
    });

    // زر تبديل العرض (بند 5) -- عرض فقط، بلا أي أثر على الفلاتر أو البيانات
    // نفسها؛ يبدّل فقط بين نفس بطاقات المستودع الجاهزة أصلاً وجدول جديد
    // يعرض نفس العناصر المفلترة حالياً.
    document.getElementById("wq-visual-evidence-view-toggle").addEventListener("click", function () {
      visualEvidenceViewMode = visualEvidenceViewMode === "cards" ? "table" : "cards";
      this.textContent = visualEvidenceViewMode === "cards" ? "عرض كجدول" : "عرض كبطاقات";
      this.setAttribute("aria-pressed", String(visualEvidenceViewMode === "table"));
      renderVisualEvidenceRepositoryList();
    });
  }

  function loadEvidenceCatalog() {
    return fetch(EVIDENCE_REPOSITORY_CATALOG_URL)
      .then(function (response) {
        return response.ok ? response.json() : [];
      })
      .catch(function () {
        return [];
      });
  }

  function evidenceCatalogForMq(mqId) {
    return evidenceCatalogState.filter(function (e) {
      return e.mq_id === mqId;
    });
  }

  function evidenceFileUrl(relativePath) {
    return "../" + relativePath;
  }

  // "ملفات الدليل المتاحة" -- يُبنى فقط من evidenceCatalogState (بيانات
  // Metadata حقيقية مطابقة لملفات موجودة فعلياً على القرص، تحقّق مسبق قبل
  // التنفيذ)، بلا أي بيانات مُخترَعة. لا علاقة بـ evaluated_evidence أعلاه
  // (قائمة منفصلة تماماً، تعرض التقييم الرسمي PASS/FAIL كما كانت).
  function evidenceRepositoryFileItemHtml(mqId, item) {
    return (
      "<li>" +
      '<div class="wq-evidence-file-item__main">📄 ' +
      escapeHtml(item.evidence_code) +
      "</div>" +
      '<div class="wq-evidence-file-item__name">اسم الملف: ' +
      escapeHtml(item.file_name) +
      "</div>" +
      '<div class="wq-evidence-file-item__actions">' +
      '<button type="button" class="wq-evidence-open-btn" data-mq-id="' +
      escapeHtml(mqId) +
      '" data-path="' +
      escapeHtml(item.relative_path) +
      '">فتح الملف ↗</button>' +
      '<button type="button" class="wq-evidence-export-btn" data-mq-id="' +
      escapeHtml(mqId) +
      '" data-path="' +
      escapeHtml(item.relative_path) +
      '" data-filename="' +
      escapeHtml(item.file_name) +
      '">تصدير</button>' +
      "</div>" +
      "</li>"
    );
  }

  function evidenceRepositoryBlockHtml(mqId) {
    const items = evidenceCatalogForMq(mqId);
    if (items.length === 0) return "";
    return (
      '<div class="wq-detail-block">' +
      '<div class="wq-detail-block__label">ملفات الدليل المتاحة</div>' +
      '<ul class="wq-evidence-file-list">' +
      items
        .map(function (item) {
          return evidenceRepositoryFileItemHtml(mqId, item);
        })
        .join("") +
      "</ul>" +
      '<p class="wq-evidence-file-error" id="wq-evidence-file-error-' +
      escapeHtml(mqId) +
      '" hidden></p>' +
      '<button type="button" class="wq-export-mq-btn" data-mq-id="' +
      escapeHtml(mqId) +
      '">تصدير الأدلة</button>' +
      "</div>"
    );
  }

  function showEvidenceFileError(mqId, message) {
    const el = document.getElementById("wq-evidence-file-error-" + mqId);
    if (!el) return;
    el.textContent = message;
    el.hidden = false;
  }

  function clearEvidenceFileError(mqId) {
    const el = document.getElementById("wq-evidence-file-error-" + mqId);
    if (!el) return;
    el.hidden = true;
    el.textContent = "";
  }

  // فتح الملف ↗ -- يتحقق من توفره فعلياً عبر fetch حقيقي قبل العرض (بدل
  // رابط عادي قد يفتح تبويباً بصفحة خطأ متصفح غير واضحة)، ثم يعرضه في
  // تبويب جديد كـ Blob مؤقت (لا يُخزَّن، لا Base64، لا نسخ دائم).
  function openEvidenceFile(mqId, relativePath) {
    clearEvidenceFileError(mqId);
    fetch(evidenceFileUrl(relativePath))
      .then(function (response) {
        if (!response.ok) throw new Error("HTTP " + response.status);
        return response.blob();
      })
      .then(function (blob) {
        const blobUrl = URL.createObjectURL(blob);
        window.open(blobUrl, "_blank", "noopener");
      })
      .catch(function () {
        showEvidenceFileError(mqId, EVIDENCE_UNAVAILABLE_MESSAGE);
      });
  }

  // تصدير (ملف واحد) -- نفس المصدر، لكن تنزيل صريح باسم الملف الرسمي بدل
  // فتح تبويب.
  function exportEvidenceFile(mqId, relativePath, fileName) {
    clearEvidenceFileError(mqId);
    fetch(evidenceFileUrl(relativePath))
      .then(function (response) {
        if (!response.ok) throw new Error("HTTP " + response.status);
        return response.blob();
      })
      .then(function (blob) {
        triggerBlobDownload(blob, fileName);
      })
      .catch(function () {
        showEvidenceFileError(mqId, EVIDENCE_UNAVAILABLE_MESSAGE);
      });
  }

  function triggerBlobDownload(blob, fileName) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () {
      URL.revokeObjectURL(url);
    }, 1000);
  }

  /* ---- ZIP encoder بحت (STORE/بلا ضغط)، بلا أي مكتبة خارجية --------- */
  /* تنسيق ZIP قياسي (Local File Header + Central Directory + EOCD)، مصدره
     فقط بايتات الملفات الحقيقية المقروءة عبر fetch وقت التصدير -- لا يُبقي
     أي نسخة على القرص، Blob مؤقت في المتصفح فقط ثم تنزيل. */

  function buildCrcTable() {
    const table = [];
    for (let n = 0; n < 256; n++) {
      let c = n;
      for (let k = 0; k < 8; k++) {
        c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
      }
      table[n] = c >>> 0;
    }
    return table;
  }
  const CRC_TABLE = buildCrcTable();

  function crc32(bytes) {
    let crc = 0 ^ -1;
    for (let i = 0; i < bytes.length; i++) {
      crc = (crc >>> 8) ^ CRC_TABLE[(crc ^ bytes[i]) & 0xff];
    }
    return (crc ^ -1) >>> 0;
  }

  function dosDateTimeNow() {
    const d = new Date();
    const dosTime = ((d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1)) & 0xffff;
    const dosDate = (((d.getFullYear() - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate()) & 0xffff;
    return { dosTime: dosTime, dosDate: dosDate };
  }

  // entries: [{ name: string, data: Uint8Array }] -> Blob (application/zip)
  function buildZip(entries) {
    const dt = dosDateTimeNow();
    const localParts = [];
    const centralParts = [];
    let offset = 0;

    entries.forEach(function (entry) {
      const nameBytes = new TextEncoder().encode(entry.name);
      const data = entry.data;
      const crc = crc32(data);

      const local = new Uint8Array(30 + nameBytes.length);
      const lv = new DataView(local.buffer);
      lv.setUint32(0, 0x04034b50, true);
      lv.setUint16(4, 20, true);
      lv.setUint16(6, 0, true);
      lv.setUint16(8, 0, true);
      lv.setUint16(10, dt.dosTime, true);
      lv.setUint16(12, dt.dosDate, true);
      lv.setUint32(14, crc, true);
      lv.setUint32(18, data.length, true);
      lv.setUint32(22, data.length, true);
      lv.setUint16(26, nameBytes.length, true);
      lv.setUint16(28, 0, true);
      local.set(nameBytes, 30);
      localParts.push(local, data);

      const central = new Uint8Array(46 + nameBytes.length);
      const cv = new DataView(central.buffer);
      cv.setUint32(0, 0x02014b50, true);
      cv.setUint16(4, 20, true);
      cv.setUint16(6, 20, true);
      cv.setUint16(8, 0, true);
      cv.setUint16(10, 0, true);
      cv.setUint16(12, dt.dosTime, true);
      cv.setUint16(14, dt.dosDate, true);
      cv.setUint32(16, crc, true);
      cv.setUint32(20, data.length, true);
      cv.setUint32(24, data.length, true);
      cv.setUint16(28, nameBytes.length, true);
      cv.setUint16(30, 0, true);
      cv.setUint16(32, 0, true);
      cv.setUint16(34, 0, true);
      cv.setUint16(36, 0, true);
      cv.setUint32(38, 0, true);
      cv.setUint32(42, offset, true);
      central.set(nameBytes, 46);
      centralParts.push(central);

      offset += local.length + data.length;
    });

    const centralStart = offset;
    let centralSize = 0;
    centralParts.forEach(function (p) {
      centralSize += p.length;
    });

    const eocd = new Uint8Array(22);
    const ev = new DataView(eocd.buffer);
    ev.setUint32(0, 0x06054b50, true);
    ev.setUint16(4, 0, true);
    ev.setUint16(6, 0, true);
    ev.setUint16(8, entries.length, true);
    ev.setUint16(10, entries.length, true);
    ev.setUint32(12, centralSize, true);
    ev.setUint32(16, centralStart, true);
    ev.setUint16(20, 0, true);

    return new Blob(localParts.concat(centralParts).concat([eocd]), { type: "application/zip" });
  }

  // تصدير الأدلة (كل ملفات MQ واحد كـ ZIP). أفضل-جهد: يتخطّى أي ملف يتعذّر
  // جلبه (ويُظهر التنبيه)، ويُصدِّر ما نجح فقط -- لا يُوقف العملية كاملة
  // لأجل ملف واحد مفقود.
  function exportMqEvidenceZip(mqId) {
    clearEvidenceFileError(mqId);
    const items = evidenceCatalogForMq(mqId);
    if (items.length === 0) {
      showEvidenceFileError(mqId, EVIDENCE_UNAVAILABLE_MESSAGE);
      return;
    }

    Promise.all(
      items.map(function (item) {
        return fetch(evidenceFileUrl(item.relative_path))
          .then(function (response) {
            if (!response.ok) return null;
            return response.arrayBuffer().then(function (buf) {
              return { name: item.file_name, data: new Uint8Array(buf) };
            });
          })
          .catch(function () {
            return null;
          });
      })
    ).then(function (results) {
      const entries = results.filter(function (r) {
        return r !== null;
      });
      if (entries.length === 0) {
        showEvidenceFileError(mqId, EVIDENCE_UNAVAILABLE_MESSAGE);
        return;
      }
      if (entries.length < items.length) {
        showEvidenceFileError(
          mqId,
          EVIDENCE_UNAVAILABLE_MESSAGE + " (تعذّر تضمين " + (items.length - entries.length) + " ملف/ملفات)"
        );
      }
      const zipBlob = buildZip(entries);
      const mqSuffix = mqId.replace("DC.MQ.", "");
      triggerBlobDownload(zipBlob, "Wathiq_DC_MQ" + mqSuffix + "_Evidence.zip");
    });
  }

  /* ---------------------------------------------------------------- */
  /* Modal                                                                */
  /* ---------------------------------------------------------------- */

  // "حالة الدليل" في نافذة التفاصيل -- عرض فقط، بلا أي حساب جديد. لدليل
  // النضج (DC.M): تُعرض statusLabelAr(evidence.status) كما هي (نفس القيمة
  // المعروضة أصلاً على بطاقة المتطلب). لدليل الامتثال (DC.C): إن وُجدت
  // مواصفة مطابقة بنفس الرمز ضمن complianceState (بيانات DC_compliance.json
  // المحمَّلة أصلاً لعرض قسم Compliance)، تُعرض compliance_status الجاهزة
  // لها (ممتثل/غير ممتثل) بدل مصطلح النضج -- بحث فقط. عدم وجود مطابقة يرجع
  // للعرض الافتراضي (statusLabelAr) حتى لا يختفي شيء كان معروضاً أصلاً.
  function evidenceDetailStatusLabel(evidence) {
    if (evidenceTypeKind(evidence.evidence_code) === "compliance") {
      const spec = findComplianceSpec(evidence.evidence_code);
      if (spec) {
        return spec.compliance_status === "COMPLIANT" ? "ممتثل" : "غير ممتثل";
      }
    }
    // إضافة دفاعية بلا تغيير سلوك: مسارَي الاستدعاء الأصليين (بطاقة MQ/عرض
    // الفجوات) يمرّران دائماً evidence.status فعلياً (PASS/FAIL/…)، فهذا
    // الفرع لا يتأثر لهما إطلاقاً. يُفعَّل فقط عند الفتح من مستودع الأدلة
    // لعنصر كتالوج لم يُقيَّم قط (raw_status=null) -- فيُطابق حرفياً نفس
    // النص المعروض أصلاً في قائمة مستودع الأدلة لذات الحالة.
    if (!evidence.status) {
      return "غير مُقيّم في المصدر الحالي";
    }
    return statusLabelAr(evidence.status);
  }

  // اسم الدليل: نفس رسالة الاحتياط المستخدَمة أصلاً في مستودع الأدلة
  // (evidenceRepositoryNameFallback) -- تختلف حسب النوع. لا تغيير على
  // مسارَي بطاقة MQ/الفجوات (evidence_name متوفر دائماً هناك أصلاً).
  function evidenceDetailNameLabel(evidence) {
    if (evidence.evidence_name) return evidenceNameDisplay(evidence.evidence_name);
    return evidenceTypeKind(evidence.evidence_code) === "compliance"
      ? "اسم المواصفة غير متوفر في المصدر الحالي"
      : "اسم الدليل غير متوفر في المصدر الحالي";
  }

  function openEvidenceModal(mq, evidence, fromGapView) {
    const overlay = document.getElementById("wq-modal-overlay");
    const title = document.getElementById("wq-modal-title");
    const body = document.getElementById("wq-modal-body");
    const modal = overlay.querySelector(".wq-modal");
    // هذا المودال البسيط لا يحتاج العرض الأوسع؛ إزالته هنا احتياطاً في حال
    // فُتح مباشرة بعد عارض الأدلة بلا إغلاق وسيط.
    if (modal) modal.classList.remove("wq-modal--wide");

    if (!evidence) {
      title.textContent = "تفاصيل غير متاحة";
      body.innerHTML = "<p>لا تتوفر بيانات إضافية لهذا العنصر ضمن البيانات التجريبية الحالية.</p>";
    } else {
      const typeLabel = evidenceTypeLabel(evidence.evidence_code);
      title.textContent = evidence.evidence_code;
      body.innerHTML =
        "<p><strong>الاسم:</strong> " +
        escapeHtml(evidenceDetailNameLabel(evidence)) +
        "</p>" +
        (typeLabel ? "<p><strong>النوع:</strong> " + escapeHtml(typeLabel) + "</p>" : "") +
        "<p><strong>الحالة:</strong> " +
        escapeHtml(evidenceDetailStatusLabel(evidence)) +
        "</p>" +
        "<p><strong>المتطلب المرتبط:</strong> " +
        escapeHtml(mq.mq_id) +
        (mq.question ? " — " + escapeHtml(mq.question) : "") +
        "</p>" +
        "<p><strong>مستوى النضج المرتبط:</strong> " +
        (typeof evidence.level_number === "number"
          ? "مستوى " + evidence.level_number
          : "غير متوفر في المصدر الحالي") +
        "</p>" +
        // حقول اختيارية -- تُعرض فقط إن وُجدت فعلياً على كائن evidence (لا
        // يحملها المصدر الحالي)، بلا أي Placeholder وهمي عند غيابها.
        (evidence.evidence_source
          ? "<p><strong>مصدر الدليل:</strong> " + escapeHtml(evidence.evidence_source) + "</p>"
          : "") +
        (evidence.assessment_date
          ? "<p><strong>تاريخ التقييم:</strong> " + escapeHtml(evidence.assessment_date) + "</p>"
          : "") +
        (evidence.verification_notes
          ? "<p><strong>ملاحظات التحقق:</strong> " + escapeHtml(evidence.verification_notes) + "</p>"
          : "") +
        (fromGapView
          ? '<p style="margin-top:14px;color:var(--text-faint);font-size:12.5px;">هذا العنصر ضمن الفجوات القادمة أمام ' +
            escapeHtml(mq.next_level_name || "المستوى التالي") +
            "</p>"
          : "") +
        visualEvidenceSectionHtml(evidence.evidence_code);
    }

    overlay.setAttribute("data-open", "true");
  }

  function closeModal() {
    const overlay = document.getElementById("wq-modal-overlay");
    overlay.setAttribute("data-open", "false");
    const modal = overlay.querySelector(".wq-modal");
    // إزالة عرض الـEvidence Viewer الأوسع عند الإغلاق حتى لا يبقى مطبَّقاً
    // على الاستخدام التالي البسيط لنفس الـModal المشترك (openEvidenceModal).
    if (modal) modal.classList.remove("wq-modal--wide");
  }

  function wireModal() {
    const overlay = document.getElementById("wq-modal-overlay");

    // إصلاح ضروري (JS فقط، بلا لمس .wq-modal في components.css): محتوى
    // Evidence Package Viewer أصبح أطول بكثير من أي استخدام سابق لهذا
    // الـModal (8+ أقسام)، و.wq-modal الأصلية بلا max-height/overflow --
    // ما كان يدفع زر الإغلاق خارج نطاق الشاشة على الشاشات الأقصر. تحديد
    // ارتفاع أقصى + تمرير داخلي لـ #wq-modal-body وحدها (لا .wq-modal
    // نفسها) يبقي رأس النافذة وزر الإغلاق ثابتين ومرئيين دائماً، بلا أي
    // تغيير على تصميم/توكنات .wq-modal الأصلية.
    const modalBody = document.getElementById("wq-modal-body");
    modalBody.style.maxHeight = "65vh";
    modalBody.style.overflowY = "auto";

    document.getElementById("wq-modal-close").addEventListener("click", closeModal);
    overlay.addEventListener("click", function (event) {
      if (event.target === overlay) closeModal();
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") closeModal();
    });
  }

  /* ---------------------------------------------------------------- */
  /* Boot                                                                 */
  /* ---------------------------------------------------------------- */

  // لا يوجد "Template/Empty State" منفصل في هذا المشروع -- النصوص
  // الافتراضية ("—") في index.html هي حالة ما قبل التحميل فقط. بدون هذا
  // catch()، فشل تحميل data/sample_maturity_report.json (مثلاً عند فتح
  // index.html مباشرة كملف file:// بدل تشغيله عبر خادم HTTP محلي، حيث
  // تمنع المتصفحات fetch() لملفات محلية) كان يترك الصفحة عالقة بصمت على
  // هذه النصوص الافتراضية -- وهو ما يبدو وكأنه "صفحة عامة" منفصلة رغم أنه
  // نفس index.html بالضبط، فقط قبل نجاح التحميل.
  function renderLoadError(err) {
    var msg =
      "تعذّر تحميل بيانات نضج تصنيف البيانات (DC) من " +
      MATURITY_DATA_URL +
      ". إن كنت فتحت هذا الملف مباشرة (file://) فهذا هو السبب على الأغلب" +
      " -- شغّل الصفحة عبر خادم HTTP محلي بدل فتحها بنقرتين. تفاصيل الخطأ: " +
      (err && err.message ? err.message : String(err));
    document.getElementById("wq-domain-name").textContent = "تعذّر التحميل";
    document.getElementById("wq-header-domain").textContent = "تعذّر التحميل";
    document.getElementById("wq-domain-context").textContent = "تعذّر التحميل";
    document.getElementById("wq-architectural-note").textContent = msg;
    document.getElementById("wq-mq-grid").innerHTML =
      '<div class="wq-empty-state">' + escapeHtml(msg) + "</div>";
  }

  /* ---------------------------------------------------------------- */
  /* View Router (Sidebar Navigation Pass) -- عرض/إخفاء الأقسام الثمانية
     الموجودة أصلاً (id فقط، بلا أي بنية داخلية جديدة) كـViews مستقلة عبر
     السمة الأصلية hidden، بدل ظهورها جميعاً في تمرير واحد طويل. لا علاقة
     له بأي render function ولا بأي بيانات -- عرض/تنقّل بحت. المصدر
     الوحيد للـView الحالية هو location.hash (بلا Backend، بلا Routing
     حقيقي) حتى يبقى زر رجوع المتصفح وإعادة تحميل الصفحة يعملان بشكل
     متوقَّع. */
  /* ---------------------------------------------------------------- */

  // v2 (2026-08-11): "home" أولاً فيصبح هو العرض الافتراضي عند عدم وجود
  // hash مطابق. الخمسة الجديدة هي الوحيدة المرتبطة بروابط في القائمة
  // الجانبية الآن (index.html) -- الثمانية القديمة بعدها تبقى ضمن القائمة
  // فقط لضمان أن showView() تستمر بإخفائها بشكل صحيح (hidden) بلا حذف أي
  // HTML/JS/بيانات خاصة بها.
  const WATHIQ_VIEWS = [
    "home",
    "assessment",
    "maturity-live",
    "evidence-live",
    "reports",
    "overview",
    "mq-cards",
    "evidence-repository",
    "visual-evidence-repository",
    "gaps",
    "recommendations",
    "compliance",
    "operational-excellence",
  ];

  const WATHIQ_VIEW_TITLES = {
    "home": "الرئيسية",
    "assessment": "التقييم",
    "maturity-live": "النضج والامتثال",
    "evidence-live": "الأدلة",
    "reports": "التقارير",
    "overview": "نظرة عامة",
    "mq-cards": "متطلبات النضج",
    "evidence-repository": "مستودع الأدلة",
    "visual-evidence-repository": "الأدلة المرئية",
    "gaps": "الفجوات",
    "recommendations": "التوصيات",
    "compliance": "قياس الامتثال",
    "operational-excellence": "التميز التشغيلي",
  };

  function currentViewFromHash() {
    const raw = (window.location.hash || "").replace("#", "");
    return WATHIQ_VIEWS.indexOf(raw) !== -1 ? raw : WATHIQ_VIEWS[0];
  }

  function closeSidebarDrawer() {
    const sidebar = document.getElementById("wq-sidebar");
    const scrim = document.getElementById("wq-sidebar-scrim");
    const toggle = document.getElementById("wq-sidebar-toggle");
    if (sidebar) sidebar.setAttribute("data-open", "false");
    if (scrim) scrim.setAttribute("data-open", "false");
    if (toggle) toggle.setAttribute("aria-expanded", "false");
  }

  function openSidebarDrawer() {
    const sidebar = document.getElementById("wq-sidebar");
    const scrim = document.getElementById("wq-sidebar-scrim");
    const toggle = document.getElementById("wq-sidebar-toggle");
    if (sidebar) sidebar.setAttribute("data-open", "true");
    if (scrim) scrim.setAttribute("data-open", "true");
    if (toggle) toggle.setAttribute("aria-expanded", "true");
  }

  // كل قسم من الثمانية موجود أصلاً في الصفحة (index.html أو مُدرَج عبر
  // inject*Section أعلاه) بمعرّفه كما هو -- هذه الدالة لا تبني أي HTML
  // جديد، فقط تُخفي كل قسم ما عدا viewId عبر hidden، وتحدّث عنوان
  // الصفحة في الرأس + الحالة النشطة في القائمة الجانبية.
  function showView(viewId) {
    WATHIQ_VIEWS.forEach(function (id) {
      const section = document.getElementById(id);
      if (section) section.hidden = id !== viewId;
    });

    const titleEl = document.getElementById("wq-page-title");
    if (titleEl) titleEl.textContent = WATHIQ_VIEW_TITLES[viewId] || WATHIQ_VIEW_TITLES[WATHIQ_VIEWS[0]];

    document.querySelectorAll(".wq-nav-link").forEach(function (link) {
      const isActive = link.getAttribute("data-view") === viewId;
      link.classList.toggle("wq-nav-link--active", isActive);
      if (isActive) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });

    closeSidebarDrawer();
    window.scrollTo(0, 0);
  }

  function wireSidebarNav() {
    window.addEventListener("hashchange", function () {
      showView(currentViewFromHash());
    });
  }

  function wireSidebarDrawer() {
    const toggle = document.getElementById("wq-sidebar-toggle");
    const scrim = document.getElementById("wq-sidebar-scrim");
    if (toggle) {
      toggle.addEventListener("click", function () {
        const sidebar = document.getElementById("wq-sidebar");
        const isOpen = sidebar && sidebar.getAttribute("data-open") === "true";
        if (isOpen) closeSidebarDrawer();
        else openSidebarDrawer();
      });
    }
    if (scrim) scrim.addEventListener("click", closeSidebarDrawer);
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") closeSidebarDrawer();
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    wireModal();
    wireVisualEvidenceActions();
    injectUploadModal();
    wireUploadModal();
    // قسمان مستقلان بالكامل -- حاويتان منفصلتان، بلا عنوان أو Container
    // مشترك بينهما (طلب صريح: فصل Operational Excellence عن Compliance).
    injectComplianceSection();
    injectOperationalExcellenceSection();
    injectEvidenceRepositorySection();
    injectVisualEvidenceRepositorySection();

    // كل الأقسام الثمانية موجودة الآن في الـDOM -- يمكن للـRouter تفعيل
    // View الصحيحة (من location.hash أو "overview" افتراضياً) قبل بدء
    // تحميل البيانات، حتى لا يظهر أي وميض لكل الأقسام مجتمعة قبل التبديل.
    wireSidebarNav();
    wireSidebarDrawer();
    showView(currentViewFromHash());

    // localStorage (تخزين هذا المتصفح فقط) يُقدَّم أولوية على بذرة
    // uploaded_evidence.json إن وُجد -- يمثّل ما رفعه المستخدم فعلياً في
    // جلسات سابقة على هذا الجهاز.
    const storedEvidence = readUploadedEvidenceFromStorage();

    loadMaturityData()
      .then(function (data) {
        return Promise.all([
          loadUploadedEvidenceSeed(),
          loadEvidenceCatalog(),
          loadComplianceData(),
          getOperationalExcellenceData(),
          loadEvidenceVisualCatalog(),
        ]).then(function (results) {
          const seed = results[0];
          uploadedEvidenceState = storedEvidence !== null ? storedEvidence : seed;
          evidenceCatalogState = results[1];
          complianceState = (results[2] && results[2].specifications) || [];
          evidenceVisualCatalogState = results[4] || [];
          loadedMaturityData = data;
          renderOverview(data);
          renderMqCards(data);
          renderGapFilters(data);
          renderGapList(data);
          renderRecommendations(data);
          renderCompliance(results[2]);
          renderOperationalExcellence(results[3]);
          renderEvidenceRepository(data);
          renderVisualEvidenceRepository();
        });
      })
      .catch(renderLoadError);
  });
})();
