"""Maturity Level Walker.

Consumes:
  - a parsed data/maturity_models/DC_MQ_*.json maturity model (read-only --
    this module never writes to that file; treats it as the reference
    schema, exactly as it exists on disk).
  - a mapping evidence_code -> list of raw Evidence Assessment Layer
    statuses (PASS/PARTIAL_PASS/FAIL/NOT_PROVIDED). A list, not a single
    string, so that more than one observed status for the same
    evidence_code is visible to this module instead of silently collapsed
    by the caller (see "Conflict" handling below).

Produces exactly one MQ-level result per call: the highest maturity level
(0-5) whose evidence requirements, and every level below it, are all
SATISFIED -- walking data/maturity_models/DC_MQ_*.json cumulatively,
starting at level 1, stopping at the first level containing any
NOT_SATISFIED / missing / conflicted evidence.

Explicitly out of scope (see src/maturity_assessment/__init__.py):
    Aggregating DC.MQ.1/2/3 into a single DC "Domain Maturity" result. No
    weight or averaging rule between the three MQs of the same domain is
    documented in any SDAIA/NDMO source available to this project (the
    page-18-referenced domain weights, per the comments already present in
    src/scoring/maturity_level_engine.py, apply between the 14 national
    domains, not between MQs inside one domain). Callers get three separate
    MQMaturityResult values and stop there.

Architectural boundary (do not weaken): this module never reads
coverage_percentage or compliance_percentage. Its only evidence-level input
is the categorical status resolved by evidence_satisfaction_resolver.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.maturity_assessment.evidence_satisfaction_resolver import (
    PartialPassPolicy,
    resolve_evidence_satisfaction,
)


class MaturityModelDataError(Exception):
    """Raised when data/maturity_models/DC_MQ_*.json itself is malformed --
    specifically, a level other than 0 with an empty evidence[] list.

    This is a data-model error, not a walk outcome: per Phase 5 of this
    engine's design, such a level must never be silently treated as
    satisfied or failed. The source JSON is never modified by this module;
    fixing it (if warranted) is a separate, explicit, human decision.
    """


@dataclass(frozen=True)
class EvaluatedEvidence:
    """One evidence_code's outcome as seen by the walker at a given level.

    status is one of the raw categorical statuses (PASS/PARTIAL_PASS/FAIL/
    NOT_PROVIDED), or the sentinel "NO_RESULT" (evidence_code has no
    assessment result at all) or "CONFLICT" (more than one distinct status
    observed for this evidence_code -- see EvidenceConflict).
    """

    evidence_code: str
    level_number: int
    status: str
    satisfied: bool
    warning: Optional[str] = None


@dataclass(frozen=True)
class EvidenceConflict:
    """More than one distinct raw status was observed for the same
    evidence_code. Never auto-resolved -- Requires Human Decision on which
    source of truth wins before this evidence_code can be walked."""

    evidence_code: str
    level_number: int
    conflicting_statuses: List[str]


@dataclass
class MQMaturityResult:
    """Result of walking one MQ's maturity model.

    missing_requirements_for_next_level lists exactly the evidence_code
    values that blocked progress past achieved_level (empty if achieved_level
    == 5, i.e. is_completed).
    """

    mq_id: str
    achieved_level: int
    level_name: str
    missing_requirements_for_next_level: List[str] = field(default_factory=list)
    evaluated_evidence: List[EvaluatedEvidence] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    conflicts: List[EvidenceConflict] = field(default_factory=list)
    is_completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Presentation-safe dict, matching the output shape requested for
        this engine (mq_id, achieved_level, level_name,
        missing_requirements_for_next_level, evaluated_evidence[])."""
        return {
            "mq_id": self.mq_id,
            "achieved_level": self.achieved_level,
            "level_name": self.level_name,
            "missing_requirements_for_next_level": list(self.missing_requirements_for_next_level),
            "evaluated_evidence": [
                {
                    "evidence_code": e.evidence_code,
                    "status": e.status,
                    "satisfied": e.satisfied,
                }
                for e in self.evaluated_evidence
            ],
            "warnings": list(self.warnings),
            "conflicts": [
                {
                    "evidence_code": c.evidence_code,
                    "level_number": c.level_number,
                    "conflicting_statuses": list(c.conflicting_statuses),
                }
                for c in self.conflicts
            ],
            "is_completed": self.is_completed,
        }


def walk_mq_maturity_levels(
    model_data: Dict[str, Any],
    evidence_status_map: Dict[str, List[str]],
    partial_pass_policy: Optional[PartialPassPolicy] = None,
) -> MQMaturityResult:
    """Walk one MQ's maturity model cumulatively from level 1 upward.

    Args:
        model_data: Parsed data/maturity_models/DC_MQ_*.json (read-only;
            uses its real keys: mq_id, levels[].level_number,
            levels[].level_name, levels[].evidence[].evidence_code).
        evidence_status_map: evidence_code -> list of raw Evidence
            Assessment Layer statuses observed for that code. A code absent
            from this map is treated as "no result" (Phase 5, case 1). A
            code mapped to 2+ distinct statuses is a Conflict (Phase 5,
            case 2) and is never auto-resolved.
        partial_pass_policy: Forwarded to evidence_satisfaction_resolver.
            No default -- omitting it while a PARTIAL_PASS status is
            encountered raises PartialPassPolicyRequiredError.

    Returns:
        An MQMaturityResult.

    Raises:
        MaturityModelDataError: a level other than 0 has no evidence[]
            entries (Phase 5, case 3).
        PartialPassPolicyRequiredError: propagated from the resolver when a
            PARTIAL_PASS status is hit with no policy supplied.
    """
    mq_id = model_data["mq_id"]
    sorted_levels = sorted(model_data["levels"], key=lambda lv: lv["level_number"])
    level_name_by_number = {lv["level_number"]: lv["level_name"] for lv in sorted_levels}

    achieved_level = 0
    achieved_name = level_name_by_number.get(0, "")
    evaluated_evidence: List[EvaluatedEvidence] = []
    warnings: List[str] = []
    conflicts: List[EvidenceConflict] = []
    missing_requirements_for_next_level: List[str] = []

    for level_data in sorted_levels:
        level_num: int = level_data["level_number"]
        if level_num == 0:
            continue  # baseline "no capability" level -- no evidence to check by definition

        level_evidence = level_data.get("evidence") or []
        if not level_evidence:
            raise MaturityModelDataError(
                f"{mq_id}: level {level_num} ('{level_data.get('level_name')}') has an "
                "empty evidence[] list but is not level 0. This is a data-model error in "
                "the maturity model JSON itself (data/maturity_models/), not a walk "
                "outcome. The source file was not modified -- fix it deliberately, or "
                "confirm level 0 numbering, before this MQ can be evaluated."
            )

        level_satisfied = True
        level_gaps: List[str] = []

        for requirement in level_evidence:
            code = requirement["evidence_code"]
            raw_statuses = evidence_status_map.get(code)

            if not raw_statuses:
                evaluated_evidence.append(
                    EvaluatedEvidence(
                        evidence_code=code,
                        level_number=level_num,
                        status="NO_RESULT",
                        satisfied=False,
                        warning=f"No assessment result found for '{code}'.",
                    )
                )
                warnings.append(
                    f"'{code}' (required at level {level_num}) has no assessment result; "
                    "treated as NOT_SATISFIED."
                )
                level_satisfied = False
                level_gaps.append(code)
                continue

            distinct_statuses = sorted(set(raw_statuses))
            if len(distinct_statuses) > 1:
                conflicts.append(
                    EvidenceConflict(
                        evidence_code=code,
                        level_number=level_num,
                        conflicting_statuses=distinct_statuses,
                    )
                )
                evaluated_evidence.append(
                    EvaluatedEvidence(
                        evidence_code=code,
                        level_number=level_num,
                        status="CONFLICT",
                        satisfied=False,
                        warning=(
                            f"'{code}' has conflicting assessment results "
                            f"{distinct_statuses}; not auto-resolved."
                        ),
                    )
                )
                level_satisfied = False
                level_gaps.append(code)
                continue

            status = raw_statuses[0]
            resolved = resolve_evidence_satisfaction(code, status, partial_pass_policy)
            evaluated_evidence.append(
                EvaluatedEvidence(
                    evidence_code=code,
                    level_number=level_num,
                    status=resolved.status,
                    satisfied=resolved.satisfied,
                    warning=resolved.warning,
                )
            )
            if resolved.warning:
                warnings.append(resolved.warning)
            if not resolved.satisfied:
                level_satisfied = False
                level_gaps.append(code)

        if not level_satisfied:
            missing_requirements_for_next_level = level_gaps
            break

        achieved_level = level_num
        achieved_name = level_data["level_name"]

    return MQMaturityResult(
        mq_id=mq_id,
        achieved_level=achieved_level,
        level_name=achieved_name,
        missing_requirements_for_next_level=missing_requirements_for_next_level,
        evaluated_evidence=evaluated_evidence,
        warnings=warnings,
        conflicts=conflicts,
        is_completed=(achieved_level == 5),
    )


def build_status_map_from_results(results: Dict[str, Any]) -> Dict[str, List[str]]:
    """Build an evidence_status_map from data/assessment_results/DC_results.json's
    shape ({evidence_code: {..., "combined_summary": {"combined_overall_status": ...}}}).

    Reads combined_overall_status specifically (not text_compliance_result.
    overall_status), matching the field dashboard/data_layer.py already
    documented as the one that preserves the PARTIAL_PASS distinction.
    Each code maps to a single-element list -- this source has exactly one
    result per evidence_code, never a conflict by construction.
    """
    status_map: Dict[str, List[str]] = {}
    for code, entry in results.items():
        combined = entry.get("combined_summary") or {}
        status = combined.get("combined_overall_status", "NOT_PROVIDED")
        status_map[code] = [status]
    return status_map


def _safe_print(line: str) -> None:
    import sys

    try:
        print(line)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        print(line.encode(encoding, errors="replace").decode(encoding))


def main() -> None:
    """Read-only self-test: loads the real DC_MQ_*.json models and the real
    DC_results.json (never writes to either), walks all three MQs, and
    checks the result against the independently-derived manual reference
    (DC.MQ.1=2, DC.MQ.2=2, DC.MQ.3=3) from this project's earlier
    source-based audit.

    partial_pass_policy below is an explicit, visible choice made only for
    this demo run -- NOT a default baked into the resolver (there is none).
    For the current DC_results.json data, no PARTIAL_PASS status actually
    occurs at or before any MQ's stopping level, so this choice does not
    affect the reference numbers either way; it is supplied only because
    the resolver refuses to run at all without an explicit answer.
    """
    import json
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[2]
    demo_partial_pass_policy: PartialPassPolicy = "NOT_SATISFIED"

    with open(project_root / "data" / "assessment_results" / "DC_results.json", "r", encoding="utf-8") as f:
        results = json.load(f)
    status_map = build_status_map_from_results(results)

    expected_levels = {"DC.MQ.1": 2, "DC.MQ.2": 2, "DC.MQ.3": 3}
    passed = 0
    failed = 0

    _safe_print("=" * 60)
    _safe_print("Maturity Level Walker -- Self Test (DC.MQ.1/2/3)")
    _safe_print(f"partial_pass_policy for this demo run: {demo_partial_pass_policy}")
    _safe_print("=" * 60)

    for mq_num in (1, 2, 3):
        mq_id = f"DC.MQ.{mq_num}"
        with open(project_root / "data" / "maturity_models" / f"DC_MQ_{mq_num}.json", "r", encoding="utf-8") as f:
            model_data = json.load(f)

        result = walk_mq_maturity_levels(model_data, status_map, partial_pass_policy=demo_partial_pass_policy)

        expected = expected_levels[mq_id]
        is_pass = result.achieved_level == expected
        status = "PASS" if is_pass else "FAIL"
        if is_pass:
            passed += 1
        else:
            failed += 1

        _safe_print(
            f"[{status}] {mq_id}: achieved_level={result.achieved_level} "
            f"({result.level_name}) [expected={expected}] "
            f"missing_for_next={result.missing_requirements_for_next_level} "
            f"conflicts={len(result.conflicts)} warnings={len(result.warnings)}"
        )

    _safe_print("")
    _safe_print("=" * 60)
    _safe_print(f"عدد الاختبارات الناجحة: {passed}")
    _safe_print(f"عدد الاختبارات الفاشلة: {failed}")
    _safe_print(f"Overall Result: {'PASS' if failed == 0 else 'FAIL'}")
    _safe_print("=" * 60)


if __name__ == "__main__":
    main()
