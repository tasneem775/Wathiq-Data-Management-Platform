"""Maturity Assessment Reporting Layer.

Formats already-computed MQ Maturity results (from
maturity_assessment_service.calculate_mq_maturity_from_assessment(), one
call per MQ) into a single structured JSON report, consumable later by a
Dashboard, a PDF report generator, or the Wathiq UI. This is the fourth
stage of the platform's first official maturity path:

    Evidence Assessment -> Maturity Assessment -> MQ Maturity Report -> Gap Identification

This file performs formatting only. It never computes anything:
    - it does not calculate a new maturity level (that already happened in
      maturity_level_walker.py before this module ever sees the result);
    - it does not modify or reinterpret an MQ's achieved_level,
      level_name, or gap list;
    - it does not convert any value into a percentage;
    - it does not produce, or approximate, an SDAIA Compliance verdict.
It reshapes and relabels fields that already exist in its input, and
nothing else.

Read this before extending this file (SDAIA Alignment):
    1) This report shows MQ Maturity only -- one row per MQ, independently
       computed. There is no per-domain row.
    2) Evidence Coverage is not Maturity. This module never reads
       coverage_percentage, compliance_percentage, or
       domain_compliance_percentage, and never will -- its only input is
       the already-resolved MQ maturity result dicts produced by
       src/maturity_assessment/maturity_assessment_service.py.
    3) Compliance Decision is out of scope of this layer entirely. This
       module never imports from src/compliance/ and never produces a
       Pass/Fail or Compliant/Non-Compliant verdict of any kind.
    4) Domain Maturity is not computed here, on purpose, not as an
       oversight. No official SDAIA/NDMO source available to this project
       documents a rule for aggregating DC.MQ.1/2/3 into one DC-level
       maturity score (verified by direct search of the extracted source
       text, not merely assumed absent). "maturity_assessment_status"
       below reports this gap explicitly instead of silently omitting a
       domain score or inventing an averaging/weighting rule to fill it.

This module never reads, writes, or imports anything from
src/evidence_assessment/, src/scoring/, src/compliance/, or dashboard/. Its
only input is the plain dict shape produced by
maturity_assessment_service.calculate_mq_maturity_from_assessment() (or any
equivalent dict carrying the same four keys: mq_id, achieved_level,
level_name, missing_requirements_for_next_level).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Static display label only -- duplicated here deliberately rather than
# imported from src/scoring/domain_progress_engine.py::DOMAIN_NAMES_AR, to
# keep this package's promise of zero imports from src/scoring/. Extend this
# dict, not the import boundary, if a second domain is ever reported.
_DOMAIN_NAMES_AR = {
    "DC": "تصنيف البيانات",
}

_MANDATORY_WARNINGS = [
    "MQ maturity is calculated independently.",
    "Domain maturity aggregation requires official SDAIA/NDMO rule.",
]


def _domain_code_from_mq_id(mq_id: str) -> str:
    """Extracts the domain code from an mq_id like 'DC.MQ.1' -> 'DC'.

    Pure string parsing -- not a computation over evidence or maturity
    data, so it does not violate this module's formatting-only contract.
    """
    return mq_id.split(".", 1)[0]


def generate_mq_maturity_report(mq_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Format a list of MQ maturity results into a single reporting-layer JSON.

    Args:
        mq_results: One dict per MQ, each shaped like the output of
            maturity_assessment_service.calculate_mq_maturity_from_assessment():
            at minimum {mq_id, achieved_level, level_name,
            missing_requirements_for_next_level}. Extra keys the service
            also returns (evaluated_evidence, warnings, conflicts,
            is_completed) are read only to surface real data-quality
            warnings/conflicts into this report's own "warnings" list (see
            below) -- their presence or absence does not change
            current_level/level_name/next_level_gaps formatting. All
            results must belong to the same domain (same mq_id prefix);
            this function refuses to guess when that is not the case.

    Returns:
        {
          "domain": str,
          "domain_name": str,
          "maturity_assessment_status": {
              "domain_level_calculation": "NOT_AVAILABLE",
              "reason": "No official aggregation rule between MQs found",
          },
          "mq_results": [
              {"mq_id": str, "current_level": int, "level_name": str,
               "next_level_gaps": list[str]},
              ...
          ],
          "warnings": list[str],   # 2 mandatory disclaimers + any real
                                    # per-MQ warnings/conflicts passed through
        }

    Raises:
        ValueError: mq_results is empty, or spans more than one domain
            (mixed mq_id prefixes) -- refuses to pick one arbitrarily.
    """
    if not mq_results:
        raise ValueError(
            "generate_mq_maturity_report() received an empty mq_results list; "
            "there is nothing to report. Refusing to fabricate a domain label "
            "or an empty-but-labeled report."
        )

    domain_codes = {_domain_code_from_mq_id(r["mq_id"]) for r in mq_results}
    if len(domain_codes) > 1:
        raise ValueError(
            f"mq_results span more than one domain {sorted(domain_codes)}; this "
            "report generator produces one single-domain report per call and "
            "refuses to guess which domain is intended. Call it once per domain."
        )
    domain_code = next(iter(domain_codes))
    domain_name = _DOMAIN_NAMES_AR.get(domain_code, domain_code)

    formatted_mq_results: List[Dict[str, Any]] = []
    passthrough_warnings: List[str] = []

    for result in mq_results:
        mq_id = result["mq_id"]

        formatted_mq_results.append(
            {
                "mq_id": mq_id,
                "current_level": result["achieved_level"],
                "level_name": result["level_name"],
                "next_level_gaps": list(result.get("missing_requirements_for_next_level", [])),
            }
        )

        for warning in result.get("warnings") or []:
            passthrough_warnings.append(f"[{mq_id}] {warning}")

        for conflict in result.get("conflicts") or []:
            code = conflict.get("evidence_code")
            statuses = conflict.get("conflicting_statuses")
            passthrough_warnings.append(
                f"[{mq_id}] Unresolved evidence conflict for '{code}': {statuses}."
            )

    return {
        "domain": domain_code,
        "domain_name": domain_name,
        "maturity_assessment_status": {
            "domain_level_calculation": "NOT_AVAILABLE",
            "reason": "No official aggregation rule between MQs found",
        },
        "mq_results": formatted_mq_results,
        "warnings": [*_MANDATORY_WARNINGS, *passthrough_warnings],
    }


def _safe_print(line: str) -> None:
    import sys

    try:
        print(line)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        print(line.encode(encoding, errors="replace").decode(encoding))


def main() -> None:
    """Read-only self-test / verification suite (Test 1-4 from this task).

    Loads the real DC_MQ_*.json models and DC_results.json (never writes to
    either) through maturity_assessment_service.calculate_mq_maturity_from_assessment(),
    formats the results through generate_mq_maturity_report(), and checks:
      Test 1: DC.MQ.1 report row shows current_level == 2
      Test 2: DC.MQ.2 report row shows next_level_gaps ==
              [DC.C.3.1, DC.C.3.2, DC.C.3.3, DC.M.8]
      Test 3: DC.MQ.3 report row shows next_level_gaps == [DC.M.12]
      Test 4: the report contains no domain_score / domain_maturity_level /
              compliance_percentage / coverage_percentage field anywhere
    """
    import json
    from pathlib import Path

    from src.maturity_assessment.maturity_assessment_service import (
        calculate_mq_maturity_from_assessment,
    )

    project_root = Path(__file__).resolve().parents[2]

    with open(project_root / "data" / "assessment_results" / "DC_results.json", "r", encoding="utf-8") as f:
        assessment_results = json.load(f)

    mq_results = []
    for mq_num in (1, 2, 3):
        mq_id = f"DC.MQ.{mq_num}"
        with open(project_root / "data" / "maturity_models" / f"DC_MQ_{mq_num}.json", "r", encoding="utf-8") as f:
            maturity_model = json.load(f)
        mq_results.append(calculate_mq_maturity_from_assessment(mq_id, maturity_model, assessment_results))

    report = generate_mq_maturity_report(mq_results)

    passed = 0
    failed = 0

    def check(name: str, condition: bool, detail: str) -> None:
        nonlocal passed, failed
        status = "PASS" if condition else "FAIL"
        if condition:
            passed += 1
        else:
            failed += 1
        _safe_print(f"[{status}] {name}: {detail}")

    _safe_print("=" * 60)
    _safe_print("Maturity Report Generator -- Self Test")
    _safe_print("=" * 60)

    by_mq = {row["mq_id"]: row for row in report["mq_results"]}

    check(
        "Test 1 (DC.MQ.1 current_level)",
        by_mq["DC.MQ.1"]["current_level"] == 2,
        f"current_level={by_mq['DC.MQ.1']['current_level']} (expected 2)",
    )
    check(
        "Test 2 (DC.MQ.2 next_level_gaps)",
        sorted(by_mq["DC.MQ.2"]["next_level_gaps"]) == sorted(["DC.C.3.1", "DC.C.3.2", "DC.C.3.3", "DC.M.8"]),
        f"next_level_gaps={by_mq['DC.MQ.2']['next_level_gaps']}",
    )
    check(
        "Test 3 (DC.MQ.3 next_level_gaps)",
        by_mq["DC.MQ.3"]["next_level_gaps"] == ["DC.M.12"],
        f"next_level_gaps={by_mq['DC.MQ.3']['next_level_gaps']}",
    )

    report_text = json.dumps(report, ensure_ascii=False)
    forbidden_fields = ["domain_score", "domain_maturity_level", "compliance_percentage", "coverage_percentage"]
    found_forbidden = [field for field in forbidden_fields if field in report_text]
    check(
        "Test 4 (no forbidden fields present)",
        not found_forbidden,
        f"found={found_forbidden}" if found_forbidden else "none of the 4 forbidden fields present",
    )

    check(
        "domain_level_calculation == NOT_AVAILABLE",
        report["maturity_assessment_status"]["domain_level_calculation"] == "NOT_AVAILABLE",
        str(report["maturity_assessment_status"]),
    )

    _safe_print("")
    _safe_print("Full report:")
    _safe_print(json.dumps(report, ensure_ascii=False, indent=2))

    _safe_print("")
    _safe_print("=" * 60)
    _safe_print(f"عدد الاختبارات الناجحة: {passed}")
    _safe_print(f"عدد الاختبارات الفاشلة: {failed}")
    _safe_print(f"Overall Result: {'PASS' if failed == 0 else 'FAIL'}")
    _safe_print("=" * 60)


if __name__ == "__main__":
    main()
