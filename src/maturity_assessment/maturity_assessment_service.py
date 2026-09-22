"""Maturity Assessment Service -- Integration Layer.

The first official path inside Wathiq wiring Evidence Assessment results to
a Maturity Level result for a single MQ:

    Evidence Assessment Results (data/assessment_results/DC_results.json)
                    |
                    v
        Maturity Assessment Service   (this file)
                    |
                    v
        MQ Maturity Level (0-5)

This file does not implement any evaluation logic itself. It only glues two
already-existing, already-verified pieces together:
  - evidence_satisfaction_resolver.py  (PASS/PARTIAL_PASS/FAIL/NOT_PROVIDED
    -> SATISFIED/NOT_SATISFIED, with no numeric input and no silent
    PARTIAL_PASS default)
  - maturity_level_walker.py           (cumulative level-by-level walk over
    a data/maturity_models/DC_MQ_*.json model)

SDAIA Alignment protection (read before changing anything below):
  1. Evidence Coverage is not Maturity Level. coverage_percentage and
     compliance_percentage (produced by src/evidence_assessment/
     gap_analysis_engine.py and aggregated by src/scoring/
     domain_progress_engine.py) are internal, engineering-defined, continuous
     text-assessment metrics with no SDAIA/NDMO source. This service's public
     function does not accept coverage_percentage, compliance_percentage, or
     domain_compliance_percentage as a parameter, and never reads any of
     those field names from assessment_results -- only the categorical
     evidence status (combined_summary.combined_overall_status) is used.
  2. Compliance Decision Layer is out of scope here. Whether an evidence
     document ultimately satisfies an official SDAIA Specification (page 14
     of "المحتوى التدريبي لمؤشر نضيء": binary 0%/100% per specification) is
     a separate, unimplemented layer (src/compliance/compliance_decision_layer.py).
     This service never imports from src/compliance/ and never produces a
     compliance verdict.
  3. Domain Average Maturity is not computed here. No official weight or
     averaging rule between DC.MQ.1/2/3 (the three MQs of the same domain)
     is documented in any SDAIA/NDMO source available to this project -- the
     page-18 domain weights referenced elsewhere in this codebase apply
     between the 14 national domains, not between MQs inside one domain.
     This service returns exactly one result per mq_id and stops there;
     callers needing all three MQs call it three times and do not average
     the results themselves.

This module never reads, writes, or imports anything from
src/evidence_assessment/, src/scoring/, src/compliance/, or dashboard/. Its
only two dependencies are the sibling modules in this same package.
"""

from __future__ import annotations

from typing import Any, Dict

from src.maturity_assessment.maturity_level_walker import (
    build_status_map_from_results,
    walk_mq_maturity_levels,
)

# Deliberately not a parameter of calculate_mq_maturity_from_assessment
# (see PARTIAL_PASS handling below): this Integration Layer never supplies
# a partial_pass_policy of its own. Any PARTIAL_PASS status the walker
# actually reaches is left to raise
# evidence_satisfaction_resolver.PartialPassPolicyRequiredError, uncaught,
# all the way up to this function's caller. Inventing a policy here -- even
# as an optional default -- would be exactly the "لا تخترع قرار" this
# service is required to avoid.
_NO_PARTIAL_PASS_POLICY = None


def calculate_mq_maturity_from_assessment(
    mq_id: str,
    maturity_model: Dict[str, Any],
    assessment_results: Dict[str, Any],
) -> Dict[str, Any]:
    """Compute one MQ's supported maturity level from evidence assessment results.

    This is the only public entry point this service exposes. It accepts no
    coverage_percentage, compliance_percentage, or domain_compliance_percentage
    parameter -- the sole input signal is the categorical evidence status
    carried inside assessment_results.

    Args:
        mq_id: The MQ identifier being evaluated (e.g. "DC.MQ.1"). Must match
            maturity_model["mq_id"] -- a mismatch is almost certainly the
            wrong maturity_model being passed in, not a valid case, so it is
            rejected rather than silently evaluated against the wrong model.
        maturity_model: The parsed, unmodified content of
            data/maturity_models/DC_MQ_X.json for this mq_id (levels 0-5,
            each with its evidence_code list and level_name). This service
            never reads the file itself -- the caller loads it and passes
            the parsed dict, keeping this function pure and file-I/O-free.
        assessment_results: The parsed, unmodified content of
            data/assessment_results/DC_results.json (or an equivalent dict
            shaped {evidence_code: {..., "combined_summary":
            {"combined_overall_status": "PASS"/"PARTIAL_PASS"/"FAIL"/
            "NOT_PROVIDED"}}}). Only combined_overall_status is read; no
            numeric field from this structure is ever consulted.

    Returns:
        A dict shaped exactly:
        {
          "mq_id": str,
          "achieved_level": int,               # 0-5
          "level_name": str,                   # Arabic level name from the model
          "missing_requirements_for_next_level": list[str],
          "evaluated_evidence": list[dict],     # [{evidence_code, status, satisfied}]
          "warnings": list[str],
          "conflicts": list[dict],              # [{evidence_code, level_number, conflicting_statuses}]
          "is_completed": bool,                 # True only when achieved_level == 5
        }

    Raises:
        ValueError: mq_id does not match maturity_model["mq_id"].
        evidence_satisfaction_resolver.PartialPassPolicyRequiredError:
            an evidence_code required at or below the achieved level has
            status PARTIAL_PASS. Not caught here -- this service has no
            policy to offer, by design (see module docstring, SDAIA
            Alignment protection, point 1, and rule 6-a of this task).
        maturity_level_walker.MaturityModelDataError: maturity_model itself
            has a non-zero level with an empty evidence[] list -- a defect
            in the source JSON, not a valid input to evaluate.
    """
    model_mq_id = maturity_model.get("mq_id")
    if model_mq_id != mq_id:
        raise ValueError(
            f"mq_id mismatch: requested '{mq_id}' but the supplied maturity_model "
            f"is for '{model_mq_id}'. Refusing to evaluate mq_id against the wrong "
            "maturity model instead of guessing which one was intended."
        )

    evidence_status_map = build_status_map_from_results(assessment_results)

    result = walk_mq_maturity_levels(
        maturity_model,
        evidence_status_map,
        partial_pass_policy=_NO_PARTIAL_PASS_POLICY,
    )

    return result.to_dict()


def _safe_print(line: str) -> None:
    import sys

    try:
        print(line)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        print(line.encode(encoding, errors="replace").decode(encoding))


def main() -> None:
    """Read-only self-test: loads the real DC_MQ_*.json models and the real
    DC_results.json (never writes to either) through the public
    calculate_mq_maturity_from_assessment() entry point, and checks the
    result against the independently-derived manual reference:
      DC.MQ.1 -> level 2
      DC.MQ.2 -> level 2, missing [DC.C.3.1, DC.C.3.2, DC.C.3.3, DC.M.8]
      DC.MQ.3 -> level 3, missing [DC.M.12]
    """
    import json
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[2]

    with open(project_root / "data" / "assessment_results" / "DC_results.json", "r", encoding="utf-8") as f:
        assessment_results = json.load(f)

    expected = {
        "DC.MQ.1": {"achieved_level": 2, "missing": ["DC.M.2"]},
        "DC.MQ.2": {"achieved_level": 2, "missing": ["DC.C.3.1", "DC.C.3.2", "DC.C.3.3", "DC.M.8"]},
        "DC.MQ.3": {"achieved_level": 3, "missing": ["DC.M.12"]},
    }

    passed = 0
    failed = 0

    _safe_print("=" * 60)
    _safe_print("Maturity Assessment Service -- Self Test (DC.MQ.1/2/3)")
    _safe_print("=" * 60)

    for mq_num in (1, 2, 3):
        mq_id = f"DC.MQ.{mq_num}"
        with open(project_root / "data" / "maturity_models" / f"DC_MQ_{mq_num}.json", "r", encoding="utf-8") as f:
            maturity_model = json.load(f)

        result = calculate_mq_maturity_from_assessment(mq_id, maturity_model, assessment_results)

        exp = expected[mq_id]
        level_ok = result["achieved_level"] == exp["achieved_level"]
        missing_ok = sorted(result["missing_requirements_for_next_level"]) == sorted(exp["missing"])
        is_pass = level_ok and missing_ok

        if is_pass:
            passed += 1
        else:
            failed += 1

        status = "PASS" if is_pass else "FAIL"
        _safe_print(
            f"[{status}] {mq_id}: achieved_level={result['achieved_level']} "
            f"({result['level_name']}) [expected={exp['achieved_level']}] "
            f"missing={result['missing_requirements_for_next_level']} "
            f"[expected_missing={exp['missing']}] "
            f"conflicts={len(result['conflicts'])} warnings={len(result['warnings'])} "
            f"is_completed={result['is_completed']}"
        )

    _safe_print("")
    _safe_print(f"mq_id mismatch guard test:")
    with open(project_root / "data" / "maturity_models" / "DC_MQ_2.json", "r", encoding="utf-8") as f:
        mq2_model = json.load(f)
    try:
        calculate_mq_maturity_from_assessment("DC.MQ.1", mq2_model, assessment_results)
        _safe_print("  [FAIL] expected ValueError for mismatched mq_id, none raised")
        failed += 1
    except ValueError as exc:
        _safe_print(f"  [PASS] ValueError raised as expected: {exc}")
        passed += 1

    _safe_print("")
    _safe_print("=" * 60)
    _safe_print(f"عدد الاختبارات الناجحة: {passed}")
    _safe_print(f"عدد الاختبارات الفاشلة: {failed}")
    _safe_print(f"Overall Result: {'PASS' if failed == 0 else 'FAIL'}")
    _safe_print("=" * 60)


if __name__ == "__main__":
    main()
