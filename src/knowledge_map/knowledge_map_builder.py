"""Knowledge map builder for the NDI-Sentinel project.

Builds the Data Classification (DC) knowledge map by reading the generated
knowledge catalog exclusively through `KnowledgeCatalogService`
(`data/knowledge_catalog/dc_knowledge_catalog.json`) and attaching, to each
evidence record, the reference PDF from `knowledge_base/ndi_framework/` that
governs it.

The reference is decided with three fixed rules, applied in order:

1. If `evidence_name` contains "سياسة تصنيف البيانات" -> "سياسة تصنيف البيانات.pdf".
2. Otherwise, if `evidence_code` starts with "DC.C" -> "ضوابط ومواصفات إدارة البيانات الوطنية.pdf".
3. Otherwise, if `evidence_code` starts with "DC.M" -> "المؤشر الوطني للبيانات.pdf".

No AI, no RAG, no PDF parsing. `maturity_models`, `evidence_catalog` and the
knowledge catalog source file are never read or modified directly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.knowledge.knowledge_catalog_service import KnowledgeCatalogService

_POLICY_NAME_MARKER = "سياسة تصنيف البيانات"
_REFERENCE_CLASSIFICATION_POLICY = "سياسة تصنيف البيانات.pdf"
_REFERENCE_DATA_STANDARDS = "ضوابط ومواصفات إدارة البيانات الوطنية.pdf"
_REFERENCE_NDI_INDICATOR = "المؤشر الوطني للبيانات.pdf"


def _resolve_reference(evidence_code: str, evidence_name: str) -> tuple[str | None, str | None]:
    """Decide the reference PDF and the reason for a single evidence record.

    Args:
        evidence_code: The evidence identifier, e.g. "DC.C.2.1".
        evidence_name: The evidence's Arabic display name.

    Returns:
        A `(reference_pdf, reference_reason)` tuple. Both are `None` when the
        evidence code matches none of the three fixed rules.
    """
    if evidence_name and _POLICY_NAME_MARKER in evidence_name:
        return (
            _REFERENCE_CLASSIFICATION_POLICY,
            f"اسم الدليل يحتوي على '{_POLICY_NAME_MARKER}'.",
        )
    if evidence_code.startswith("DC.C"):
        return _REFERENCE_DATA_STANDARDS, "كود الدليل يبدأ بـ DC.C."
    if evidence_code.startswith("DC.M"):
        return (
            _REFERENCE_NDI_INDICATOR,
            "كود الدليل يبدأ بـ DC.M ولا يشير اسمه إلى سياسة تصنيف البيانات.",
        )
    return None, None


class KnowledgeMapBuilder:
    """Builds the DC knowledge map by attaching a reference PDF to each
    evidence record of the knowledge catalog.

    Attributes:
        warnings: Human-readable warnings collected during the last build,
            one per evidence_code that matched none of the three fixed
            reference rules. Such records are still included in the output,
            with `reference_pdf` and `reference_reason` set to `None`.
    """

    _OUTPUT_RELATIVE_PATH: Path = Path("data") / "knowledge_map" / "dc_knowledge_map.json"

    def __init__(self, project_root: Path) -> None:
        """Args:
            project_root: Absolute path to the project root directory.
        """
        self._project_root = project_root
        self._catalog_service = KnowledgeCatalogService(project_root)
        self._output_path = project_root / self._OUTPUT_RELATIVE_PATH
        self.warnings: list[str] = []

    @property
    def output_path(self) -> Path:
        """Absolute path to the generated knowledge map file."""
        return self._output_path

    def build(self) -> list[dict[str, Any]]:
        """Read the knowledge catalog and attach a reference PDF to each record.

        Returns:
            The full list of knowledge map records.
        """
        self.warnings = []
        catalog_records = self._catalog_service.load()

        records: list[dict[str, Any]] = []
        for entry in catalog_records:
            evidence_code = entry.get("evidence_code")
            evidence_name = entry.get("evidence_name")
            reference_pdf, reference_reason = _resolve_reference(evidence_code, evidence_name)

            if reference_pdf is None:
                self.warnings.append(
                    f"الدليل '{evidence_code}' لا يطابق أي قاعدة ربط معروفة "
                    "(لا DC.M ولا DC.C) — تم إبقاؤه في الخريطة بدون reference_pdf."
                )

            records.append(
                {
                    "evidence_code": evidence_code,
                    "evidence_name": evidence_name,
                    "mq_id": entry.get("mq_id"),
                    "level_number": entry.get("level_number"),
                    "level_name": entry.get("level_name"),
                    "reference_pdf": reference_pdf,
                    "reference_reason": reference_reason,
                }
            )
        return records

    def save(self, records: list[dict[str, Any]]) -> Path:
        """Write the records list to the knowledge map output file.

        Args:
            records: The list of record dictionaries to persist.

        Returns:
            Absolute path to the written knowledge map file.
        """
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        with self._output_path.open("w", encoding="utf-8") as file:
            json.dump(records, file, ensure_ascii=False, indent=2)
        return self._output_path

    def run(self) -> list[dict[str, Any]]:
        """Build the records list and persist it to disk.

        Returns:
            The list of record dictionaries that was written to disk.
        """
        records = self.build()
        self.save(records)
        return records


def _print_report(builder: KnowledgeMapBuilder, records: list[dict[str, Any]]) -> None:
    """Print the build summary report to stdout.

    Args:
        builder: The builder instance used to produce the records.
        records: The full list of generated record dictionaries.
    """
    counts_by_pdf: dict[str, int] = {}
    for record in records:
        pdf = record["reference_pdf"] or "بدون مرجع"
        counts_by_pdf[pdf] = counts_by_pdf.get(pdf, 0) + 1

    example_m6 = next(
        (record for record in records if record["evidence_code"] == "DC.M.6"), None
    )
    example_c21 = next(
        (record for record in records if record["evidence_code"] == "DC.C.2.1"), None
    )

    print("=== تقرير بناء الخريطة المعرفية (Knowledge Map) ===")
    print(f"1. عدد Records داخل Knowledge Map: {len(records)}")

    print("\n2. عدد الأدلة المرتبطة بكل PDF:")
    for pdf, count in counts_by_pdf.items():
        print(f"   - {pdf}: {count}")

    print("\n3. مثال كامل لـ DC.M.6:")
    print(json.dumps(example_m6, ensure_ascii=False, indent=2))

    print("\n4. مثال كامل لـ DC.C.2.1:")
    print(json.dumps(example_c21, ensure_ascii=False, indent=2))

    print(f"\n5. عدد التحذيرات: {len(builder.warnings)}")
    if builder.warnings:
        for warning in builder.warnings:
            print(f"   - {warning}")
    else:
        print("   لا توجد تحذيرات — كل الأدلة طابقت إحدى قواعد الربط الثلاث.")

    print(f"\nمسار ملف dc_knowledge_map.json: {builder.output_path}")


def main() -> None:
    """Build the DC knowledge map and print a summary report."""
    project_root = Path(__file__).resolve().parents[2]
    builder = KnowledgeMapBuilder(project_root)
    records = builder.run()
    _print_report(builder, records)


if __name__ == "__main__":
    main()
