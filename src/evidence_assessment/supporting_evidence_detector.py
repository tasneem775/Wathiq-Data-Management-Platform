"""Rule-based detector for supporting-evidence requirements.

Reads evidence metadata from data/evidence_catalog/*.json (Metadata Layer)
and decides, using keyword heuristics only (no OCR, no LLM, no external
service), whether an evidence code requires supporting evidence and whether
information extracted from a Word document (text/images/tables counts)
appears to satisfy that requirement.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


CATALOG_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "evidence_catalog"
)


# Keywords whose presence in acceptance_criteria marks the evidence code as
# requiring supporting evidence.

REQUIREMENT_TRIGGER_KEYWORDS: tuple[str, ...] = (
    "الأدلة الداعمة",
    "الوثائق الداعمة",
    "إثباتات",
    "إرفاق ما يثبت",
    "الصور",
    "المستندات",
    "محاضر الاجتماعات",
    "التقارير",
    "الخطابات",
    "لقطات الشاشة",
    "screenshots",
    "workflow",
    "سير العمل",
    "تدفق العمل",
)


# Ordered patterns -> canonical required supporting-type label.

TYPE_PATTERNS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("الصور", "صور"), "صور"),
    (("المستندات", "مستندات"), "مستندات"),
    (("محاضر الاجتماعات", "محاضر"), "محاضر اجتماعات"),
    (("التقارير", "تقارير"), "تقارير"),
    (("الخطابات", "خطاب"), "خطابات"),
    (("لقطات الشاشة", "screenshots"), "لقطات شاشة"),
    (("workflow", "سير العمل", "تدفق العمل"), "Workflow"),
    (("الوثائق الداعمة",), "وثائق داعمة"),
    (("الأدلة الداعمة",), "أدلة داعمة"),
    (("إثباتات", "إرفاق ما يثبت"), "إثباتات"),
)


# Required types that name no concrete artifact and therefore always need a
# human to confirm what was actually attached.

GENERIC_SUPPORTING_TYPES = frozenset(
    {
        "أدلة داعمة",
        "وثائق داعمة",
        "إثباتات",
    }
)


@lru_cache(maxsize=1)
def _load_catalog_items() -> tuple[dict[str, Any], ...]:
    """Load every evidence_items entry from data/evidence_catalog/*.json."""
    items: list[dict[str, Any]] = []

    for catalog_file in sorted(CATALOG_DIR.glob("*.json")):
        with catalog_file.open("r", encoding="utf-8") as fh:
            data = json.load(fh)

        items.extend(data.get("evidence_items", []))

    return tuple(items)


def _find_evidence_item(
    evidence_code: str,
) -> dict[str, Any] | None:
    for item in _load_catalog_items():
        if item.get("code") == evidence_code:
            return item

    return None


def _contains_any(
    text_lower: str,
    patterns: tuple[str, ...],
) -> bool:
    return any(
        pattern.lower() in text_lower
        for pattern in patterns
    )


def _extract_required_supporting_types(
    criteria_text: str,
) -> list[str]:
    text_lower = criteria_text.lower()
    required_types: list[str] = []

    for patterns, canonical_type in TYPE_PATTERNS:
        if (
            _contains_any(text_lower, patterns)
            and canonical_type not in required_types
        ):
            required_types.append(canonical_type)

    return required_types


def _is_alternative_supporting_requirement(
    criteria_text: str,
) -> bool:
    """Return True when supporting types are presented as examples/alternatives."""
    text_lower = criteria_text.lower()

    return (
        "مثل" in text_lower
        or "أو" in text_lower
    )


def _extract_detected_types(
    extracted_document_info: dict[str, Any],
) -> list[str]:
    """Detect only concrete evidence actually observable in the extracted file.

    IMPORTANT:
    Merely mentioning words such as 'تقرير', 'محضر', 'مستند', or 'خطاب'
    inside the evidence document does NOT prove that a supporting artifact
    of that type was attached.

    Therefore:
    - Embedded images are detected as actual image evidence.
    - Tables are reported as document structure only.
    - Textual mentions of reports/documents/minutes/letters/workflows are
      NOT treated as supporting evidence artifacts.
    """
    images_count = extracted_document_info.get("images_count") or 0
    tables_count = extracted_document_info.get("tables_count") or 0

    detected: list[str] = []

    # An actual embedded image is concrete evidence that can be observed
    # directly from the extracted Word document.
    if images_count > 0:
        detected.append("صور")

    # Tables are document structure, not automatically supporting evidence.
    # Keep them visible for diagnostics but do not treat them as a concrete
    # supporting-evidence artifact.
    if tables_count > 0:
        detected.append("جداول")

    return detected


def detect_supporting_evidence_requirements(
    evidence_code: str,
) -> dict[str, Any]:
    """Decide whether an evidence code's acceptance criteria require supporting evidence."""
    item = _find_evidence_item(evidence_code)

    if item is None:
        return {
            "evidence_code": evidence_code,
            "evidence_found": False,
            "supporting_evidence_required": False,
            "required_supporting_types": [],
            "matched_acceptance_criteria": [],
            "needs_human_review": True,
            "notes": [
                "لم يتم العثور على الكود ضمن ملفات كتالوج الأدلة "
                "(data/evidence_catalog)."
            ],
        }

    acceptance_criteria: list[str] = item.get(
        "acceptance_criteria",
        [],
    )

    matched_acceptance_criteria = [
        criterion
        for criterion in acceptance_criteria
        if _contains_any(
            criterion.lower(),
            REQUIREMENT_TRIGGER_KEYWORDS,
        )
    ]

    supporting_evidence_required = bool(
        matched_acceptance_criteria
    )

    required_supporting_types = (
        _extract_required_supporting_types(
            " ".join(acceptance_criteria)
        )
        if supporting_evidence_required
        else []
    )

    required_set = set(required_supporting_types)

    generic_present = (
        required_set & GENERIC_SUPPORTING_TYPES
    )

    specific_present = (
        required_set - GENERIC_SUPPORTING_TYPES
    )

    needs_human_review = (
        supporting_evidence_required
        and bool(generic_present)
        and not specific_present
    )

    notes: list[str] = []

    if not supporting_evidence_required:
        notes.append(
            "لا توجد كلمات مفتاحية تدل على الحاجة لأدلة داعمة "
            "ضمن متطلبات القبول."
        )
    else:
        notes.append(
            f"تم العثور على {len(matched_acceptance_criteria)} "
            "معيار قبول يشير إلى الحاجة لأدلة داعمة."
        )

        if needs_human_review:
            notes.append(
                "النوع المطلوب عام (أدلة/وثائق داعمة أو إثباتات) "
                "دون تحديد واضح - يلزم مراجعة بشرية."
            )

    return {
        "evidence_code": evidence_code,
        "evidence_found": True,
        "supporting_evidence_required": supporting_evidence_required,
        "required_supporting_types": required_supporting_types,
        "matched_acceptance_criteria": matched_acceptance_criteria,
        "needs_human_review": needs_human_review,
        "notes": notes,
    }


def check_detected_supporting_evidence(
    evidence_code: str,
    extracted_document_info: dict[str, Any],
) -> dict[str, Any]:
    """Compare required supporting-evidence types against actual extracted evidence.

    Textual mentions inside the main evidence document are not treated as
    proof that separate supporting artifacts exist.
    """
    detection = detect_supporting_evidence_requirements(
        evidence_code
    )

    notes = list(detection["notes"])

    if not detection["evidence_found"]:
        return {
            "evidence_code": evidence_code,
            "supporting_evidence_required": False,
            "required_supporting_types": [],
            "detected_supporting_types": [],
            "supporting_evidence_status": "UNKNOWN",
            "missing_supporting_types": [],
            "needs_human_review": True,
            "notes": notes,
        }

    detected_supporting_types = _extract_detected_types(
        extracted_document_info
    )

    required_supporting_types = detection[
        "required_supporting_types"
    ]

    if not detection["supporting_evidence_required"]:
        notes.append(
            "لا حاجة للتحقق من الأدلة الداعمة لهذا الكود."
        )

        return {
            "evidence_code": evidence_code,
            "supporting_evidence_required": False,
            "required_supporting_types": [],
            "detected_supporting_types": detected_supporting_types,
            "supporting_evidence_status": "NOT_REQUIRED",
            "missing_supporting_types": [],
            "needs_human_review": detection[
                "needs_human_review"
            ],
            "notes": notes,
        }

    required_set = set(required_supporting_types)
    detected_set = set(detected_supporting_types)

    generic_present = (
        required_set & GENERIC_SUPPORTING_TYPES
    )

    # "جداول" describe the structure of the main Word document.
    # They must never by themselves satisfy a supporting-evidence
    # requirement.
    concrete_detected_types = (
        detected_set - {"جداول"}
    )

    generic_requirement_satisfied = bool(
        generic_present
        and concrete_detected_types
    )

    # Supporting types can be presented as examples/alternatives.
    #
    # Example:
    # "مثل: التقارير، الصور، المستندات، أو محاضر الاجتماعات"
    #
    # These are acceptable alternatives, not mandatory types that
    # must all exist.
    alternative_requirement = (
        _is_alternative_supporting_requirement(
            " ".join(
                detection["matched_acceptance_criteria"]
            )
        )
    )

    specific_required_types = [
        supporting_type
        for supporting_type in required_supporting_types
        if supporting_type
        not in GENERIC_SUPPORTING_TYPES
    ]

    if alternative_requirement:
        detected_concrete_required_types = (
            detected_set
            & set(specific_required_types)
        )

        missing_specific_types: list[str] = []

        if (
            not detected_concrete_required_types
            and not generic_requirement_satisfied
        ):
            missing_specific_types = (
                specific_required_types
            )
    else:
        missing_specific_types = [
            supporting_type
            for supporting_type in specific_required_types
            if supporting_type not in detected_set
        ]

    missing_supporting_types = missing_specific_types

    needs_human_review = detection[
        "needs_human_review"
    ]

    if not detected_set:
        status = "MISSING"

        # A supporting-evidence requirement exists, but the current
        # extraction contains no concrete supporting artifact.
        needs_human_review = True

        notes.append(
            "لم يتم رصد أي أدلة داعمة فعلية ضمن محتوى الوثيقة "
            "المستخرج. لا يتم اعتبار مجرد ذكر كلمات مثل "
            "'تقرير' أو 'مستند' أو 'محضر' دليلاً على وجود "
            "مرفق داعم."
        )

    elif alternative_requirement:
        detected_concrete_required_types = (
            detected_set
            & set(specific_required_types)
        )

        if (
            detected_concrete_required_types
            or generic_requirement_satisfied
        ):
            status = "SATISFIED"
            needs_human_review = False

            notes.append(
                "تم رصد نوع ملموس من الأنواع المقبولة كدليل "
                "داعم؛ وبما أن المعيار يذكر الأنواع كأمثلة/بدائل، "
                "فلا يلزم توفر جميع الأنواع المذكورة."
            )
        else:
            status = "MISSING"
            needs_human_review = True

            notes.append(
                "تم تحديد أنواع بديلة للأدلة الداعمة، لكن لم يتم "
                "رصد أي نوع منها فعلياً ضمن محتوى الوثيقة المستخرج."
            )

    elif missing_specific_types:
        status = "PARTIAL"
        needs_human_review = True

        notes.append(
            "تم رصد بعض الأنواع المطلوبة فقط؛ الأنواع الناقصة: "
            f"{', '.join(missing_specific_types)}."
        )

    elif generic_requirement_satisfied:
        status = "SATISFIED"
        needs_human_review = False

        notes.append(
            "تم رصد نوع ملموس من الأدلة الداعمة، ويُعتبر مستوفياً "
            "لمتطلب الأدلة العامة."
        )

    else:
        status = "SATISFIED"

        notes.append(
            "تم رصد جميع أنواع الأدلة الداعمة المطلوبة."
        )

    return {
        "evidence_code": evidence_code,
        "supporting_evidence_required": True,
        "required_supporting_types": required_supporting_types,
        "detected_supporting_types": detected_supporting_types,
        "supporting_evidence_status": status,
        "missing_supporting_types": missing_supporting_types,
        "needs_human_review": needs_human_review,
        "notes": notes,
    }


def check_multiple_supporting_evidence(
    evidence_codes: list[str],
    extracted_documents_map: dict[
        str,
        dict[str, Any],
    ],
) -> dict[str, dict[str, Any]]:
    """Run check_detected_supporting_evidence for a batch of evidence codes."""
    empty_document_info: dict[str, Any] = {
        "text": "",
        "images_count": 0,
        "tables_count": 0,
    }

    return {
        evidence_code: check_detected_supporting_evidence(
            evidence_code,
            extracted_documents_map.get(
                evidence_code,
                empty_document_info,
            ),
        )
        for evidence_code in evidence_codes
    }


def _print_result(result: dict[str, Any]) -> None:
    print(
        f"evidence_code: "
        f"{result['evidence_code']}"
    )

    print(
        f"supporting_evidence_required: "
        f"{result['supporting_evidence_required']}"
    )

    print(
        f"required_supporting_types: "
        f"{result['required_supporting_types']}"
    )

    print(
        f"detected_supporting_types: "
        f"{result.get('detected_supporting_types', [])}"
    )

    print(
        f"supporting_evidence_status: "
        f"{result['supporting_evidence_status']}"
    )

    print(
        f"missing_supporting_types: "
        f"{result['missing_supporting_types']}"
    )

    print(
        f"needs_human_review: "
        f"{result['needs_human_review']}"
    )

    print("-" * 60)


if __name__ == "__main__":
    _print_result(
        check_detected_supporting_evidence(
            "DC.M.1",
            {
                "text": (
                    "تقرير يوضح الممارسات الحالية "
                    "المتعلقة بتصنيف البيانات"
                ),
                "images_count": 0,
                "tables_count": 0,
            },
        )
    )

    _print_result(
        check_detected_supporting_evidence(
            "DC.M.2",
            {
                "text": (
                    "تقرير حالة التنفيذ يتضمن محضر "
                    "اجتماع ونسب الإنجاز"
                ),
                "images_count": 2,
                "tables_count": 1,
            },
        )
    )

    _print_result(
        check_detected_supporting_evidence(
            "DC.M.2",
            {
                "text": (
                    "تقرير حالة تنفيذ الخطة ونسب الإنجاز"
                ),
                "images_count": 0,
                "tables_count": 0,
            },
        )
    )

    _print_result(
        check_detected_supporting_evidence(
            "DC.NOT.REAL",
            {
                "text": "",
                "images_count": 0,
                "tables_count": 0,
            },
        )
    )
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    