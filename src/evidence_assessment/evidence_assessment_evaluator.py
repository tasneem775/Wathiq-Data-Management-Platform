"""Evidence assessment evaluator for maturity level assessment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.evidence.evidence_validator import MQValidationResult


@dataclass
class MQLevelResult:
    """Evaluation result for a single MQ maturity assessment.

    Attributes:
        mq_id: Identifier of the MQ (e.g. "DC.MQ.1").
        achieved_level: Highest maturity level fully satisfied (0-5).
        level_name: Arabic name of the achieved level.
        present_codes: Evidence codes confirmed present in the repository.
        missing_next_level: Codes required for the next level that are absent.
        is_completed: True when achieved_level equals 5.
    """

    mq_id: str
    achieved_level: int
    level_name: str
    present_codes: list[str] = field(default_factory=list)
    missing_next_level: list[str] = field(default_factory=list)
    is_completed: bool = False


class EvidenceAssessmentEvaluator:
    """Evaluates achieved maturity levels based on evidence codes and model requirements.

    Applies a cumulative maturity model: a level is achieved only when all
    requirements at that level are present, and all lower levels have been
    achieved first.

    Schema note (architecture fix, read-only source): the maturity model
    JSON files under data/maturity_models/ (e.g. DC_MQ_1.json) are the
    reference schema and were not modified for this fix. Their actual keys
    are ``level_number`` (not ``level``), ``evidence`` (not
    ``requirements``), and ``evidence_code`` (not ``code``) for each
    evidence item. This evaluator was previously written against the old,
    incorrect key names and would raise KeyError on every real call; it now
    reads the JSON's real keys directly instead.
    """

    def evaluate(
        self,
        mq_id: str,
        model_data: dict[str, Any],
        validation_result: MQValidationResult,
    ) -> MQLevelResult:
        """Determine the highest achieved maturity level for a single MQ.

        Iterates levels 1 through 5 in ascending order. Stops at the first
        level where any required code is missing, then reports that level's
        absent codes as the gap for the next level.

        Args:
            mq_id: The MQ identifier (e.g. "DC.MQ.1").
            model_data: Parsed maturity model dictionary from the JSON file
                (data/maturity_models/DC_MQ_*.json), using its real keys:
                levels[].level_number, levels[].level_name,
                levels[].evidence[].evidence_code.
            validation_result: Evidence scan result containing matched codes.

        Returns:
            An MQLevelResult describing the achieved level and any code gaps.
        """
        matched_set = set(validation_result.matched_codes)
        sorted_levels = sorted(model_data["levels"], key=lambda lv: lv["level_number"])

        achieved_level = 0
        achieved_name = sorted_levels[0]["level_name"]

        for level_data in sorted_levels:
            level_num: int = level_data["level_number"]
            if level_num == 0:
                continue

            codes = [req["evidence_code"] for req in level_data.get("evidence", [])]
            missing = [c for c in codes if not self._is_code_matched(c, matched_set)]

            if missing:
                return MQLevelResult(
                    mq_id=mq_id,
                    achieved_level=achieved_level,
                    level_name=achieved_name,
                    present_codes=sorted(validation_result.matched_codes),
                    missing_next_level=missing,
                    is_completed=False,
                )

            achieved_level = level_num
            achieved_name = level_data["level_name"]

        return MQLevelResult(
            mq_id=mq_id,
            achieved_level=achieved_level,
            level_name=achieved_name,
            present_codes=sorted(validation_result.matched_codes),
            missing_next_level=[],
            is_completed=(achieved_level == 5),
        )

    def _is_code_matched(self, code: str, matched_codes: set[str]) -> bool:
        """Check whether a requirement code has corresponding evidence on disk.

        Handles a known naming inconsistency in the maturity model files where
        control-type codes are written as "DC.X.Y" instead of "DC.C.X.Y".
        Both forms are tried before returning False.

        Args:
            code: Requirement code from the maturity model JSON.
            matched_codes: Set of evidence codes confirmed present on disk.

        Returns:
            True if the code or its normalized equivalent is present.
        """
        if code in matched_codes:
            return True

        parts = code.split(".")
        if len(parts) == 3:
            candidate = f"{parts[0]}.C.{parts[1]}.{parts[2]}"
            return candidate in matched_codes

        return False
