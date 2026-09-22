"""Evidence validator for the NDI-Sentinel project."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class MQValidationResult:
    """Holds the validation outcome for a single MQ evidence folder.

    Attributes:
        mq_id: Identifier of the MQ (e.g. "DC.MQ.1").
        required_codes: All evidence codes declared in the MQ evidence JSON.
        matched_codes: Codes that have a corresponding .docx file in the folder.
        missing_codes: Codes with no matching .docx file in the folder.
        extra_files: Stems of .docx files in the folder not required by the catalog.
    """

    mq_id: str
    required_codes: list[str] = field(default_factory=list)
    matched_codes: list[str] = field(default_factory=list)
    missing_codes: list[str] = field(default_factory=list)
    extra_files: list[str] = field(default_factory=list)


class EvidenceValidator:
    """Compares required evidence codes against actual .docx files in a folder.

    Receives pre-loaded data and performs no file I/O beyond directory listing.
    """

    def validate(
        self,
        mq_id: str,
        evidence_items: list[dict[str, Any]],
        evidence_folder: Path,
    ) -> MQValidationResult:
        """Compare required codes with .docx files present in the evidence folder.

        The matching rule: evidence code "DC.M.1" must have a file named
        "DC.M.1.docx" in the folder (stem equals code, extension is .docx).

        Args:
            mq_id: Identifier of the MQ being validated.
            evidence_items: List of evidence item dicts, each containing "code".
            evidence_folder: Absolute path to the MQ evidence folder.

        Returns:
            An MQValidationResult describing matched, missing, and extra items.
        """
        required_codes = [item["code"] for item in evidence_items]
        required_set = set(required_codes)

        actual_stems = {
            path.stem
            for path in evidence_folder.glob("*.docx")
        }

        matched = [code for code in required_codes if code in actual_stems]
        missing = [code for code in required_codes if code not in actual_stems]
        extra = sorted(stem for stem in actual_stems if stem not in required_set)

        return MQValidationResult(
            mq_id=mq_id,
            required_codes=required_codes,
            matched_codes=matched,
            missing_codes=missing,
            extra_files=extra,
        )
