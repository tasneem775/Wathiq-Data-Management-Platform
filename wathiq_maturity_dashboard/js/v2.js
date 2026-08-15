/* Wathiq -- v2 (2026-08-11): Home / Assessment Stepper / Live Maturity /
   Live Evidence / Reports.
   ======================================================================
   يقرأ فقط من الملفات الحقيقية عند الجذر (data/evidence_catalog/*.json،
   data/maturity_models/*.json، data/assessment_results/DC_results.json) --
   لا JSON وهمي جديد، ولا أي اعتماد على sample_maturity_report.json /
   DC_compliance.json / operational_excellence_simulation.json /
   evidence_visual_catalog.json.

   يتطلب تشغيل الخادم الثابت من جذر المشروع (وليس من داخل
   wathiq_maturity_dashboard/) حتى تُحلّ المسارات النسبية "../data/..." إلى
   المجلد الحقيقي.

   لا يوجد أي HTTP API في المشروع اليوم (src/api/ فارغ) -- لذلك زر "بدء
   التقييم" هنا لا يُشغّل أي تقييم حقيقي، ويعرض ذلك بوضوح بدل تزييف نتيجة.
   لا منطق تسجيل/Scoring/Gap Analysis/Recommendation منقول من Python هنا:
   حساب النسب في هذا الملف هو نفس العدّ البسيط (PASS/PARTIAL/FAIL + متوسط
   coverage_percentage) الذي يقوم به src/scoring/domain_progress_engine.py
   على نفس ملف النتائج الحقيقي -- عرض فقط، وليس تقييماً جديداً. */

(function () {
  "use strict";

  var DATA_ROOT = "../data/";
  var EVIDENCE_CATALOG_DIR = DATA_ROOT + "evidence_catalog/";
  var MATURITY_MODELS_DIR = DATA_ROOT + "maturity_models/";
  var RESULTS_URL = DATA_ROOT + "assessment_results/DC_results.json";
  var MANIFEST_URL = EVIDENCE_CATALOG_DIR + "dc_evidence_catalog.json";
  // نسبي لنفس الأصل (wathiq_api.py يخدم الواجهة والـ API على نفس المنفذ) --
  // بلا CORS. إن تعذّر الوصول (خادم ثابت فقط بلا API)، يُعرَض ذلك بوضوح
  // في handleStartAssessment() بدل نتيجة مزيَّفة.
  var ASSESS_API_URL = "/api/assess";

  var STATUS_LABEL_AR = { PASS: "مستوفٍ", PARTIAL_PASS: "مستوفٍ جزئياً", FAIL: "غير مستوفٍ" };
  var STATUS_BADGE_KEY = { PASS: "pass", PARTIAL_PASS: "partial", FAIL: "fail" };

  var state = {
    mqCatalog: null, // [{mq_id, mq_name, max_level, items:[{code,name,acceptance_criteria,level_number,level_name}]}]
    results: null, // raw DC_results.json
    selectedMq: null,
    selectedEvidence: null,
    dataError: null,
  };

  function fetchJSON(url) {
    return fetch(url).then(function (res) {
      if (!res.ok) throw new Error(url + " -> HTTP " + res.status);
      return res.json();
    });
  }

  function escapeHtml(text) {
    var div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
  }

  /* -------------------------------------------------------------- */
  /* Data loading -- real files only                                  */
  /* -------------------------------------------------------------- */
  function loadAll() {
    return fetchJSON(MANIFEST_URL)
      .then(function (manifest) {
        var mqEntries = manifest.mq_catalogs || [];
        return Promise.all(
          mqEntries.map(function (mqEntry) {
            var catalogUrl = "../" + mqEntry.catalog_file;
            var modelUrl = "../" + mqEntry.requirements_file;
            return Promise.all([fetchJSON(catalogUrl), fetchJSON(modelUrl)]).then(function (pair) {
              var catalogData = pair[0];
              var modelData = pair[1];
              var itemsByCode = {};
              (catalogData.evidence_items || []).forEach(function (entry) {
                if (!entry.code) return;
                itemsByCode[entry.code] = {
                  code: entry.code,
                  name: entry.name || "",
                  acceptance_criteria: entry.acceptance_criteria || [],
                  level_number: null,
                  level_name: null,
                };
              });
              var levels = modelData.levels || [];
              var maxLevel = null;
              levels.forEach(function (level) {
                if (level.level_number != null) {
                  maxLevel = maxLevel == null ? level.level_number : Math.max(maxLevel, level.level_number);
                }
                (level.evidence || []).forEach(function (ev) {
                  if (itemsByCode[ev.evidence_code]) {
                    itemsByCode[ev.evidence_code].level_number = level.level_number;
                    itemsByCode[ev.evidence_code].level_name = level.level_name;
                  }
                });
              });
              return {
                mq_id: mqEntry.mq_id,
                mq_name: mqEntry.name || mqEntry.mq_id,
                max_level: maxLevel,
                items: Object.keys(itemsByCode).map(function (k) { return itemsByCode[k]; }),
              };
            });
          })
        ).then(function (mqList) {
          state.mqCatalog = mqList;
        });
      })
      .then(function () {
        return fetchJSON(RESULTS_URL).then(function (results) {
          state.results = results;
        });
      })
      .catch(function (err) {
        state.dataError = err;
      });
  }

  /* -------------------------------------------------------------- */
  /* Shared aggregation (mirrors domain_progress_engine.py's simple   */
  /* counting -- display only, no new scoring logic)                  */
  /* -------------------------------------------------------------- */
  function evidenceToMqMap() {
    var map = {};
    (state.mqCatalog || []).forEach(function (mq) {
      mq.items.forEach(function (item) { map[item.code] = mq.mq_id; });
    });
    return map;
  }

  function allEvidenceCodes() {
    var codes = [];
    (state.mqCatalog || []).forEach(function (mq) {
      mq.items.forEach(function (item) { codes.push(item); });
    });
    return codes;
  }

  function resultFor(code) {
    var entry = state.results && state.results[code];
    if (!entry || !entry.combined_summary) return null;
    return {
      status: entry.combined_summary.combined_overall_status,
      coverage: (entry.text_compliance_result && entry.text_compliance_result.coverage_percentage) || 0,
    };
  }

  function computeStats(items) {
    var total = items.length, assessed = 0, pass = 0, partial = 0, fail = 0, coverageSum = 0;
    items.forEach(function (item) {
      var r = resultFor(item.code);
      if (r) {
        assessed++;
        coverageSum += r.coverage || 0;
        if (r.status === "PASS") pass++;
        else if (r.status === "PARTIAL_PASS") partial++;
        else if (r.status === "FAIL") fail++;
      }
    });
    return {
      total: total, assessed: assessed, pass: pass, partial: partial, fail: fail,
      completionPct: total ? Math.round((assessed / total) * 100) : 0,
      coveragePct: total ? Math.round(coverageSum / total) : 0,
    };
  }

  /* -------------------------------------------------------------- */
  /* Renderers                                                        */
  /* -------------------------------------------------------------- */
  function renderHome() {
    var box = document.getElementById("wq-v2-home-stats");
    if (!box) return;
    if (state.dataError) { box.innerHTML = '<p class="wq-section__hint">تعذر تحميل بيانات النظرة السريعة.</p>'; return; }
    var stats = computeStats(allEvidenceCodes());
    var cards = box.querySelectorAll(".wq-kpi-card__value");
    cards[0].textContent = stats.total;
    cards[1].textContent = stats.completionPct + "%";
    cards[2].textContent = stats.coveragePct + "%";
  }

  function renderStepper(activeStep) {
    var steps = [["domain", "المجال"], ["requirement", "المتطلب"], ["evidence", "الدليل"], ["upload", "التقييم"]];
    var order = ["domain", "requirement", "evidence", "upload"];
    var activeIndex = order.indexOf(activeStep);
    var html = "";
    steps.forEach(function (pair, i) {
      var cls = i < activeIndex ? "wq-stepper__step--done" : i === activeIndex ? "wq-stepper__step--active" : "";
      var mark = i < activeIndex ? "✓" : String(i + 1);
      html += '<div class="wq-stepper__step ' + cls + '"><div class="wq-stepper__circle">' + mark + '</div><div class="wq-stepper__label">' + pair[1] + "</div></div>";
      if (i < steps.length - 1) html += '<div class="wq-stepper__connector"></div>';
    });
    var el = document.getElementById("wq-v2-stepper");
    if (el) el.innerHTML = html;
  }

  function goToStep(step) {
    ["domain", "requirement", "evidence", "upload"].forEach(function (s) {
      var el = document.getElementById("wq-v2-step-" + s);
      if (el) el.hidden = s !== step;
    });
    renderStepper(step);
  }

  function renderRequirementList() {
    var box = document.getElementById("wq-v2-requirement-list");
    if (!box) return;
    if (state.dataError || !state.mqCatalog) { box.innerHTML = '<p class="wq-section__hint">تعذر تحميل قائمة المتطلبات.</p>'; return; }
    var html = "";
    state.mqCatalog.forEach(function (mq) {
      var levelText = mq.max_level != null ? "Level " + mq.max_level : "—";
      html +=
        '<div class="wq-option-card" data-mq="' + escapeHtml(mq.mq_id) + '">' +
        '<div class="wq-option-card__title">' + escapeHtml(mq.mq_id) + " — " + escapeHtml(mq.mq_name) + "</div>" +
        '<div class="wq-option-card__meta">المستوى المستهدف: ' + levelText + " · عدد الأدلة: " + mq.items.length + "</div>" +
        '<button type="button" class="wq-option-card__action" data-select-mq="' + escapeHtml(mq.mq_id) + '">اختيار ' + escapeHtml(mq.mq_id) + " ←</button>" +
        "</div>";
    });
    box.innerHTML = html;
  }

  function renderEvidenceList() {
    var box = document.getElementById("wq-v2-evidence-list");
    var context = document.getElementById("wq-v2-evidence-context");
    if (!box || !state.selectedMq) return;
    var mq = state.selectedMq;
    if (context) context.textContent = "المتطلب: " + mq.mq_id + " — " + mq.mq_name;
    if (!mq.items.length) { box.innerHTML = '<p class="wq-section__hint">لا توجد أدلة معرَّفة لهذا المتطلب.</p>'; return; }
    var html = "";
    mq.items.forEach(function (item) {
      var levelText = item.level_number != null ? "Level " + item.level_number : "—";
      var criteria = item.acceptance_criteria && item.acceptance_criteria[0] ? item.acceptance_criteria[0] : "";
      html +=
        '<div class="wq-option-card" data-evidence="' + escapeHtml(item.code) + '">' +
        '<div class="wq-option-card__title">' + escapeHtml(item.code) + "</div>" +
        '<div class="wq-option-card__meta">' + escapeHtml(item.name) + "</div>" +
        '<div class="wq-option-card__meta">مرتبط بـ: ' + escapeHtml(mq.mq_id) + " · المستوى: " + levelText + "</div>" +
        (criteria ? '<div class="wq-option-card__meta">' + escapeHtml(criteria) + "</div>" : "") +
        '<button type="button" class="wq-option-card__action" data-select-evidence="' + escapeHtml(item.code) + '">اختيار هذا الدليل (' + escapeHtml(item.code) + ")</button>" +
        "</div>";
    });
    box.innerHTML = html;
  }

  function renderUploadStep() {
    var context = document.getElementById("wq-v2-upload-context");
    var resultBox = document.getElementById("wq-v2-result");
    var fileReady = document.getElementById("wq-v2-file-ready");
    var startBtn = document.getElementById("wq-v2-start-assessment");
    if (context && state.selectedMq && state.selectedEvidence) {
      context.textContent = "المتطلب: " + state.selectedMq.mq_id + " · الدليل: " + state.selectedEvidence.code + " — " + state.selectedEvidence.name;
    }
    if (fileReady) fileReady.innerHTML = '<p class="wq-section__hint">ارفع ملف الدليل للبدء.</p>';
    if (resultBox) resultBox.innerHTML = "";
    if (startBtn) { startBtn.disabled = true; startBtn.textContent = "بدء التقييم"; }
    var fileInput = document.getElementById("wq-v2-file-input");
    if (fileInput) fileInput.value = "";
  }

  function renderMaturityLive() {
    var kpiBox = document.getElementById("wq-v2-maturity-kpis");
    var tableBody = document.querySelector("#wq-v2-mq-table tbody");
    if (!kpiBox || !tableBody) return;
    if (state.dataError || !state.mqCatalog || !state.results) {
      kpiBox.innerHTML = '<p class="wq-section__hint">تعذر تحميل بيانات النضج والامتثال.</p>';
      return;
    }
    var overall = computeStats(allEvidenceCodes());
    kpiBox.innerHTML =
      '<div class="wq-kpi-card wq-kpi-card--hero"><div class="wq-kpi-card__label">متوسط تغطية الأدلة</div><div class="wq-kpi-card__value">' + overall.coveragePct + "%</div></div>" +
      '<div class="wq-kpi-card"><div class="wq-kpi-card__label">نسبة اكتمال التقييم</div><div class="wq-kpi-card__value">' + overall.completionPct + "%</div></div>" +
      '<div class="wq-kpi-card"><div class="wq-kpi-card__label">إجمالي الأدلة</div><div class="wq-kpi-card__value">' + overall.total + "</div></div>" +
      '<div class="wq-kpi-card"><div class="wq-kpi-card__label">مستوفٍ / جزئي / غير مستوفٍ</div><div class="wq-kpi-card__value">' + overall.pass + " / " + overall.partial + " / " + overall.fail + "</div></div>";

    var rows = "";
    state.mqCatalog.forEach(function (mq) {
      var stats = computeStats(mq.items);
      rows += "<tr><td>" + escapeHtml(mq.mq_id) + " — " + escapeHtml(mq.mq_name) + "</td><td>" + mq.items.length + "</td><td>" + stats.coveragePct + "%</td></tr>";
    });
    tableBody.innerHTML = rows || '<tr><td colspan="3">لا توجد بيانات.</td></tr>';
  }

  function renderEvidenceLive() {
    var tableBody = document.querySelector("#wq-v2-evidence-table tbody");
    if (!tableBody) return;
    if (state.dataError || !state.mqCatalog || !state.results) {
      tableBody.innerHTML = '<tr><td colspan="5">تعذر تحميل بيانات الأدلة.</td></tr>';
      return;
    }
    var mqMap = evidenceToMqMap();
    var rows = "";
    allEvidenceCodes().forEach(function (item) {
      var r = resultFor(item.code);
      var statusLabel = r ? (STATUS_LABEL_AR[r.status] || r.status) : "لم يُقيَّم بعد";
      var badgeKey = r ? STATUS_BADGE_KEY[r.status] : null;
      var statusHtml = badgeKey
        ? '<span class="wq-status-badge" data-status="' + badgeKey + '"><span class="wq-status-badge__dot"></span>' + statusLabel + "</span>"
        : statusLabel;
      var coverage = r ? r.coverage + "%" : "—";
      rows +=
        "<tr><td>" + escapeHtml(item.code) + "</td><td>" + escapeHtml(item.name) + "</td><td>" + escapeHtml(mqMap[item.code] || "—") + "</td><td>" + statusHtml + "</td><td>" + coverage + "</td></tr>";
    });
    tableBody.innerHTML = rows || '<tr><td colspan="5">لا توجد أدلة.</td></tr>';
  }

  /* -------------------------------------------------------------- */
  /* Assessment trigger -- calls the real Python pipeline via          */
  /* wathiq_api.py::POST /api/assess. No result is ever fabricated:    */
  /* every field rendered below comes verbatim from the Presentation   */
  /* Dict returned by src/dashboard/assessment_dashboard_adapter.py::  */
  /* prepare_dashboard_assessment() -- same function, same shape,      */
  /* already used and tested via the Streamlit build.                  */
  /* -------------------------------------------------------------- */
  function handleStartAssessment() {
    var resultBox = document.getElementById("wq-v2-result");
    var startBtn = document.getElementById("wq-v2-start-assessment");
    var fileInput = document.getElementById("wq-v2-file-input");
    if (!resultBox || !fileInput || !fileInput.files || !fileInput.files[0]) return;
    if (!state.selectedEvidence) return;

    startBtn.disabled = true;
    startBtn.textContent = "جاري تحليل الدليل...";
    resultBox.innerHTML = '<p class="wq-loading-note">جاري تحليل الدليل...</p>';

    var formData = new FormData();
    formData.append("evidence_code", state.selectedEvidence.code);
    formData.append("file", fileInput.files[0]);

    fetch(ASSESS_API_URL, { method: "POST", body: formData })
      .then(function (res) {
        return res.json().then(function (body) { return { ok: res.ok, body: body }; });
      })
      .then(function (r) {
        if (!r.ok || r.body.success === false) {
          resultBox.innerHTML =
            '<div class="wq-backend-note"><b>تعذر إتمام التقييم.</b><br />' + escapeHtml(r.body.message || "حدث خطأ غير متوقع.") + "</div>";
          return;
        }
        renderAssessmentResult(r.body);
      })
      .catch(function () {
        resultBox.innerHTML =
          '<div class="wq-backend-note"><b>تعذر الوصول إلى خادم التقييم.</b><br />' +
          "تأكد من تشغيل الخادم عبر <code>python wathiq_api.py</code> وأن الصفحة مفتوحة من نفس المنفذ." +
          "</div>";
      })
      .finally(function () {
        startBtn.disabled = false;
        startBtn.textContent = "بدء التقييم";
      });
  }

  function statusBadgeHtml(status, labelAr) {
    var key = STATUS_BADGE_KEY[status] || "pending";
    return '<span class="wq-status-badge" data-status="' + key + '"><span class="wq-status-badge__dot"></span>' + escapeHtml(labelAr) + "</span>";
  }

  function renderAssessmentResult(result) {
    var resultBox = document.getElementById("wq-v2-result");
    if (!resultBox) return;

    var parts = [];
    parts.push('<h3 class="wq-section__title" style="font-size:16px;">نتيجة تقييم الدليل</h3>');
    parts.push('<p class="wq-section__hint">' + escapeHtml(result.message || "") + "</p>");

    if (!result.assessment_available) {
      resultBox.innerHTML = parts.join("");
      return;
    }

    parts.push('<div style="margin:8px 0 16px;">' + statusBadgeHtml(result.overall_status, result.overall_status_ar || result.overall_status || "—") + "</div>");

    parts.push('<div class="wq-kpi-grid">');
    parts.push('<div class="wq-kpi-card wq-kpi-card--hero"><div class="wq-kpi-card__label">نسبة التغطية</div><div class="wq-kpi-card__value">' + (result.coverage_percentage || 0) + "%</div></div>");
    var criticalCount = (result.critical_findings || []).length;
    var mediumCount = (result.medium_findings || []).length;
    var recos = result.recommendations || {};
    var totalReco = (recos.high_priority || []).length + (recos.medium_priority || []).length;
    parts.push('<div class="wq-kpi-card"><div class="wq-kpi-card__label">الفجوات الحرجة</div><div class="wq-kpi-card__value">' + criticalCount + "</div></div>");
    parts.push('<div class="wq-kpi-card"><div class="wq-kpi-card__label">الفجوات المتوسطة</div><div class="wq-kpi-card__value">' + mediumCount + "</div></div>");
    parts.push('<div class="wq-kpi-card"><div class="wq-kpi-card__label">إجمالي التوصيات</div><div class="wq-kpi-card__value">' + totalReco + "</div></div>");
    parts.push("</div>");

    // ما تم استيفاؤه / الفجوات
    var satisfied = result.satisfied_findings || [];
    var gaps = (result.critical_findings || []).concat(result.medium_findings || []);
    parts.push('<div class="wq-finding-grid">');
    parts.push('<div class="wq-card"><div class="wq-card-label" style="font-weight:700;margin-bottom:6px;">ما تم استيفاؤه</div>');
    if (satisfied.length) {
      satisfied.forEach(function (item) {
        parts.push('<div class="wq-finding-item wq-finding-item--good"><div class="wq-finding-item__mark">✓</div><div>' + escapeHtml(item) + "</div></div>");
      });
    } else {
      parts.push('<p class="wq-section__hint">لا توجد عناصر مستوفاة بعد.</p>');
    }
    parts.push("</div>");
    parts.push('<div class="wq-card"><div class="wq-card-label" style="font-weight:700;margin-bottom:6px;">الفجوات</div>');
    if (gaps.length) {
      gaps.forEach(function (item) {
        parts.push('<div class="wq-finding-item wq-finding-item--gap"><div class="wq-finding-item__mark">!</div><div>' + escapeHtml(item) + "</div></div>");
      });
    } else {
      parts.push('<p class="wq-section__hint">لا توجد فجوات.</p>');
    }
    parts.push("</div></div>");

    // التوصيات -- النص الحقيقي (action.description) وليس recommendation_type الخام
    parts.push('<h3 class="wq-section__title" style="font-size:16px;">التوصيات المقترحة</h3>');
    var allRecos = (recos.high_priority || []).map(function (r) { return { r: r, level: "high", label: "أولوية عالية" }; })
      .concat((recos.medium_priority || []).map(function (r) { return { r: r, level: "medium", label: "أولوية متوسطة" }; }));
    if (!allRecos.length) {
      parts.push('<p class="wq-section__hint">لا توجد توصيات إضافية — الدليل يغطي المتطلبات بشكل كافٍ.</p>');
    } else {
      allRecos.forEach(function (entry) {
        var action = (entry.r && entry.r.action) || {};
        var description = action.description || "";
        parts.push(
          '<div class="wq-reco-card wq-reco-card--' + entry.level + '"><div class="wq-reco-card__title">' + entry.label + '</div><div class="wq-reco-card__body">' + escapeHtml(description) + "</div></div>"
        );
      });
    }

    // تقرير Word
    if (result.report_download_url) {
      parts.push('<a class="wq-option-card__action" href="' + result.report_download_url + '" download style="display:inline-block;text-decoration:none;margin-top:12px;">تحميل تقرير التقييم ↓</a>');
    }

    resultBox.innerHTML = parts.join("");
  }

  /* -------------------------------------------------------------- */
  /* Event wiring                                                     */
  /* -------------------------------------------------------------- */
  function wireEvents() {
    document.addEventListener("click", function (e) {
      var domainBtn = e.target.closest("#wq-v2-domain-continue");
      if (domainBtn) { goToStep("requirement"); renderRequirementList(); return; }

      var selectMqBtn = e.target.closest("[data-select-mq]");
      if (selectMqBtn) {
        var mqId = selectMqBtn.getAttribute("data-select-mq");
        state.selectedMq = (state.mqCatalog || []).filter(function (m) { return m.mq_id === mqId; })[0] || null;
        state.selectedEvidence = null;
        goToStep("evidence");
        renderEvidenceList();
        return;
      }

      var selectEvBtn = e.target.closest("[data-select-evidence]");
      if (selectEvBtn) {
        var code = selectEvBtn.getAttribute("data-select-evidence");
        state.selectedEvidence = (state.selectedMq ? state.selectedMq.items : []).filter(function (it) { return it.code === code; })[0] || null;
        goToStep("upload");
        renderUploadStep();
        return;
      }

      var backBtn = e.target.closest("[data-v2-back]");
      if (backBtn) {
        var target = backBtn.getAttribute("data-v2-back");
        if (target === "domain") { state.selectedMq = null; state.selectedEvidence = null; }
        if (target === "requirement") { state.selectedEvidence = null; }
        goToStep(target);
        if (target === "requirement") renderRequirementList();
        if (target === "evidence") renderEvidenceList();
        return;
      }

      var startBtn = e.target.closest("#wq-v2-start-assessment");
      if (startBtn && !startBtn.disabled) { handleStartAssessment(); return; }
    });

    var fileInput = document.getElementById("wq-v2-file-input");
    if (fileInput) {
      fileInput.addEventListener("change", function () {
        var fileReady = document.getElementById("wq-v2-file-ready");
        var startBtn = document.getElementById("wq-v2-start-assessment");
        var file = fileInput.files && fileInput.files[0];
        if (file) {
          var sizeKb = (file.size / 1024).toFixed(1);
          if (fileReady) {
            fileReady.innerHTML =
              '<div class="wq-file-ready"><div><b>📄 ' + escapeHtml(file.name) + "</b><div class=\"wq-option-card__meta\">Word Document · " + sizeKb + " كيلوبايت · جاهز للتقييم ✓</div></div></div>";
          }
          if (startBtn) startBtn.disabled = false;
        } else {
          if (fileReady) fileReady.innerHTML = "";
          if (startBtn) startBtn.disabled = true;
        }
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    wireEvents();
    goToStep("domain");
    loadAll().then(function () {
      renderHome();
      renderRequirementList();
      renderMaturityLive();
      renderEvidenceLive();
    });
  });
})();
