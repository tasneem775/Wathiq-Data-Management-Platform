"""Evidence Satisfaction Resolver.

Single responsibility: translate a single Evidence Assessment Layer status
(the categorical output of src/evidence_assessment/gap_analysis_engine.py /
evidence_assessment_orchestrator.py -- PASS, PARTIAL_PASS, FAIL,
NOT_PROVIDED) into the two-value signal the Maturity Level Walker needs:
SATISFIED / NOT_SATISFIED.

Architectural boundary (do not weaken):
    This module's public function accepts only a categorical status string.
    It has no parameter, branch, or fallback that reads coverage_percentage,
    compliance_percentage, or any other numeric value. That boundary exists
    specifically to prevent Evidence Coverage (a continuous internal
    text-assessment metric with no SDAIA/NDMO source) from leaking into
    Maturity Level computation -- the exact violation already found and
    blocked in src/scoring/maturity_level_engine.py::MaturityInputGuardError
    earlier in this project's remediation work.

Decision table:
    PASS          -> SATISFIED
    FAIL          -> NOT_SATISFIED
    NOT_PROVIDED  -> NOT_SATISFIED   (no evidence text was submitted at all;
                      this is not a policy question -- nothing to evaluate)
    PARTIAL_PASS  -> NOT decided by this module. No SDAIA/NDMO source
                      available to this project states whether a
                      partially-satisfied evidence document counts toward a
                      maturity level. The caller MUST pass an explicit
                      `partial_pass_policy`; there is no default. Calling
                      without one when a PARTIAL_PASS status is encountered
                      raises PartialPassPolicyRequiredError -- this module
                      refuses to guess.
    anything else (e.g. "UNKNOWN", or a typo/未来 status) -> NOT_SATISFIED,
                      with a warning attached. This is a data-quality
                      finding, not a policy question, so it does not require
                      the same human decision PARTIAL_PASS does.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

PartialPassPolicy = Literal["SATISFIED", "NOT_SATISFIED"]

# The four statuses this project's Evidence Assessment Layer actually
# produces (src/evidence_assessment/gap_analysis_engine.py::analyze_gap,
# combined_summary.combined_overall_status). Anything outside this set is
# treated as a data-quality anomaly, not a recognized evidence outcome.
KNOWN_EVIDENCE_STATUSES = {"PASS", "PARTIAL_PASS", "FAIL", "NOT_PROVIDED"}


class PartialPassPolicyRequiredError(Exception):
    """Raised when a PARTIAL_PASS status must be resolved but no explicit
    partial_pass_policy was supplied by the caller.

    This is not a bug -- it is the module refusing to invent an SDAIA/NDMO
    decision that does not exist in any source available to this project.
    Requires Human Decision (or an official SDAIA/NDMO source defining how
    a partially-satisfied evidence document counts toward maturity) before
    this can be called with a fixed policy in production code.
    """


@dataclass(frozen=True)
class SatisfactionResult:
    """Outcome of resolving one evidence_code's status to SATISFIED/NOT_SATISFIED.

    Attributes:
        evidence_code: The evidence code this result belongs to.
        status: The raw categorical status that was resolved (verbatim,
            for traceability -- never a numeric value).
        satisfied: True (SATISFIED) or False (NOT_SATISFIED).
        warning: Set only for unrecognized status values; None otherwise.
    """

    evidence_code: str
    status: str
    satisfied: bool
    warning: Optional[str] = None


def resolve_evidence_satisfaction(
    evidence_code: str,
    status: str,
    partial_pass_policy: Optional[PartialPassPolicy] = None,
) -> SatisfactionResult:
    """Resolve one evidence_code's categorical status to SATISFIED/NOT_SATISFIED.

    Args:
        evidence_code: The evidence code being resolved (e.g. "DC.M.1").
        status: One of PASS/PARTIAL_PASS/FAIL/NOT_PROVIDED (or an
            unrecognized value, handled as a data-quality warning).
        partial_pass_policy: Required only when status == "PARTIAL_PASS".
            Must be explicitly supplied by the caller; there is no default.

    Returns:
        A SatisfactionResult.

    Raises:
        PartialPassPolicyRequiredError: status is "PARTIAL_PASS" and
            partial_pass_policy was not supplied.
    """
    if status == "PASS":
        return SatisfactionResult(evidence_code=evidence_code, status=status, satisfied=True)

    if status in ("FAIL", "NOT_PROVIDED"):
        return SatisfactionResult(evidence_code=evidence_code, status=status, satisfied=False)

    if status == "PARTIAL_PASS":
        if partial_pass_policy is None:
            raise PartialPassPolicyRequiredError(
                f"evidence_code '{evidence_code}' has status PARTIAL_PASS, but no "
                "partial_pass_policy was supplied. No SDAIA/NDMO source available to "
                "this project defines whether a partially-satisfied evidence document "
                "counts toward a maturity level. Requires Human Decision before this "
                "evidence_code can be resolved."
            )
        return SatisfactionResult(
            evidence_code=evidence_code,
            status=status,
            satisfied=(partial_pass_policy == "SATISFIED"),
        )

    return SatisfactionResult(
        evidence_code=evidence_code,
        status=status,
        satisfied=False,
        warning=(
            f"Unrecognized evidence status '{status}' for '{evidence_code}' "
            f"(expected one of {sorted(KNOWN_EVIDENCE_STATUSES)}); treated as "
            "NOT_SATISFIED pending data-quality review."
        ),
    )


def resolve_many(
    evidence_status_map: dict[str, str],
    partial_pass_policy: Optional[PartialPassPolicy] = None,
) -> dict[str, SatisfactionResult]:
    """Resolve a batch of evidence_code -> status pairs.

    Args:
        evidence_status_map: evidence_code -> raw categorical status.
        partial_pass_policy: Passed through to resolve_evidence_satisfaction
            for every PARTIAL_PASS entry; still no default.

    Returns:
        evidence_code -> SatisfactionResult.
    """
    return {
        code: resolve_evidence_satisfaction(code, status, partial_pass_policy)
        for code, status in evidence_status_map.items()
    }
