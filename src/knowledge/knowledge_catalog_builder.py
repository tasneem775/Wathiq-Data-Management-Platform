"""Knowledge catalog builder for the NDI-Sentinel project.

Builds the unified Data Classification (DC) knowledge catalog by joining two
source layers on `evidence_code`:

- `data/maturity_models/DC_MQ_*.json` is the source of truth for
  `domain_code`, `domain_name_ar`, `mq_id`, `question` (saved as
  `mq_question`), `level_number`, `level_name`, `description` (saved as
  `level_description`), `maturity_requirement`, `related_specifications` and
  `inherits_previous_level_requirements`.
- `data/evidence_catalog/DC_MQ_*_evidence.json` is the source of truth for
  `evidence_code`, `evidence_name` and `acceptance_criteria`.

`level_description`, `maturity_requirement` and `acceptance_criteria` are
three distinct fields and are never merged: `level_description` is the
maturity level's own description, `maturity_requirement` is the per-evidence
requirement text from the maturity model, and `acceptance_criteria` is the
document acceptance criteria from the evidence catalog.

The file pairing between the two layers is read from the manifest at
`data/evidence_catalog/dc_evidence_catalog.json`. No AI, no RAG, no PDF
parsing, and no source file is ever modified.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class KnowledgeCatalogBuildError(Exception):
    """Raised when a source file cannot be read or parsed."""


class KnowledgeCatalogBuilder:
    """Builds the DC knowledge catalog by joining maturity models with the
    evidence catalog on `evidence_code`.

    Attributes:
        warnings: Human-readable warnings collected during the last build,
            one per evidence_code that exists in only one of the two source
            layers. Mismatched entries are never dropped from the output.
    """

    _MANIFEST_RELATIVE_PATH: Path = (
        Path("data") / "evidence_catalog" / "dc_evidence_catalog.json"
    )
    _OUTPUT_RELATIVE_PATH: Path = (
        Path("data") / "knowledge_catalog" / "dc_knowledge_catalog.json"
    )

    def __init__(self, project_root: Path) -> None:
        """Args:
            project_root: Absolute path to the project root directory.
        """
        self._project_root = project_root
        self._manifest_path = project_root / self._MANIFEST_RELATIVE_PATH
        self._output_path = project_root / self._OUTPUT_RELATIVE_PATH
        self.warnings: list[str] = []

    @property
    def manifest_path(self) -> Path:
        """Absolute path to the evidence catalog manifest."""
        return self._manifest_path

    @property
    def output_path(self) -> Path:
        """Absolute path to the generated knowledge catalog file."""
        return self._output_path

    def _load_json(self, path: Path) -> Any:
        """Read and parse a single JSON source file.

        Args:
            path: Absolute path to the source file.

        Returns:
            Parsed JSON content.

        Raises:
            KnowledgeCatalogBuildError: If the file is missing or contains
                invalid JSON.
        """
        if not path.exists():
            raise KnowledgeCatalogBuildError(f"Source file not found: {path}")

        try:
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError as error:
            raise KnowledgeCatalogBuildError(
                f"Invalid JSON format: {path}"
            ) from error

    def _load_evidence_catalog(self, path: Path) -> dict[str, dict[str, Any]]:
        """Load an evidence_catalog file into a lookup keyed by evidence_code.

        Args:
            path: Absolute path to a `DC_MQ_*_evidence.json` file.

        Returns:
            Mapping of evidence_code to its `evidence_name` and
            `acceptance_criteria`, as authored in the evidence catalog.
        """
        data = self._load_json(path)
        lookup: dict[str, dict[str, Any]] = {}
        for item in data.get("evidence_items", []):
            code = item.get("code")
            lookup[code] = {
                "evidence_name": item.get("name"),
                "acceptance_criteria": item.get("acceptance_criteria"),
            }
        return lookup

    def _build_mq_records(self, mq_entry: dict[str, Any]) -> list[dict[str, Any]]:
        """Join one MQ's maturity model with its evidence catalog.

        Args:
            mq_entry: One entry from the manifest's `mq_catalogs` list,
                containing `mq_id`, `catalog_file` and `requirements_file`.

        Returns:
            The joined records for this MQ. Evidence codes present in only
            one of the two sources are still included, with a warning
            appended to `self.warnings`.
        """
        mq_id = mq_entry["mq_id"]
        maturity_data = self._load_json(self._project_root / mq_entry["requirements_file"])
        evidence_catalog = self._load_evidence_catalog(
            self._project_root / mq_entry["catalog_file"]
        )
        consumed_codes: set[str] = set()

        domain_code = maturity_data.get("domain_code")
        domain_name_ar = maturity_data.get("domain_name_ar")
        mq_question = maturity_data.get("question")

        records: list[dict[str, Any]] = []
        for level in maturity_data.get("levels", []):
            level_number = level.get("level_number")
            level_name = level.get("level_name")
            level_description = level.get("description")

            for evidence in level.get("evidence", []):
                code = evidence.get("evidence_code")
                catalog_entry = evidence_catalog.get(code)

                maturity_requirement = evidence.get("maturity_requirement")
                if not maturity_requirement:
                    self.warnings.append(
                        f"[{mq_id}] الدليل '{code}' لا يحتوي على maturity_requirement "
                        "في maturity_models."
                    )

                if catalog_entry is None:
                    self.warnings.append(
                        f"[{mq_id}] الدليل '{code}' موجود في maturity_models "
                        "ولا يوجد في evidence_catalog — تم إبقاؤه في الفهرس "
                        "بدون acceptance_criteria موثّقة."
                    )
                    evidence_name = evidence.get("evidence_name")
                    acceptance_criteria = None
                else:
                    consumed_codes.add(code)
                    evidence_name = catalog_entry["evidence_name"]
                    acceptance_criteria = catalog_entry["acceptance_criteria"]
                    if acceptance_criteria is not None and not isinstance(
                        acceptance_criteria, list
                    ):
                        self.warnings.append(
                            f"[{mq_id}] acceptance_criteria للدليل '{code}' "
                            "ليست list في evidence_catalog."
                        )

                records.append(
                    {
                        "domain_code": domain_code,
                        "domain_name_ar": domain_name_ar,
                        "mq_id": mq_id,
                        "mq_question": mq_question,
                        "level_number": level_number,
                        "level_name": level_name,
                        "level_description": level_description,
                        "evidence_code": code,
                        "evidence_name": evidence_name,
                        "maturity_requirement": maturity_requirement,
                        "acceptance_criteria": acceptance_criteria,
                        "related_specifications": evidence.get("related_specifications") or [],
                        "inherits_previous_level_requirements": evidence.get(
                            "inherits_previous_level_requirements"
                        ),
                    }
                )

        for code, entry in evidence_catalog.items():
            if code in consumed_codes:
                continue
            self.warnings.append(
                f"[{mq_id}] الدليل '{code}' موجود في evidence_catalog ولا يوجد "
                "في maturity_models — تم إبقاؤه في الفهرس بدون معلومات مستوى "
                "وبدون maturity_requirement."
            )
            acceptance_criteria = entry["acceptance_criteria"]
            if acceptance_criteria is not None and not isinstance(acceptance_criteria, list):
                self.warnings.append(
                    f"[{mq_id}] acceptance_criteria للدليل '{code}' ليست list "
                    "في evidence_catalog."
                )
            records.append(
                {
                    "domain_code": domain_code,
                    "domain_name_ar": domain_name_ar,
                    "mq_id": mq_id,
                    "mq_question": mq_question,
                    "level_number": None,
                    "level_name": None,
                    "level_description": None,
                    "evidence_code": code,
                    "evidence_name": entry["evidence_name"],
                    "maturity_requirement": None,
                    "acceptance_criteria": acceptance_criteria,
                    "related_specifications": [],
                    "inherits_previous_level_requirements": None,
                }
            )

        return records

    def build(self) -> list[dict[str, Any]]:
        """Read the manifest and join every MQ's two source layers.

        Returns:
            The full list of joined records across all MQs.

        Raises:
            KnowledgeCatalogBuildError: If the manifest or any source file
                referenced by it cannot be read or parsed.
        """
        self.warnings = []
        manifest = self._load_json(self._manifest_path)

        records: list[dict[str, Any]] = []
        for mq_entry in manifest.get("mq_catalogs", []):
            records.extend(self._build_mq_records(mq_entry))
        return records

    def save(self, records: list[dict[str, Any]]) -> Path:
        """Write the records list to the knowledge catalog output file.

        Args:
            records: The list of record dictionaries to persist.

        Returns:
            Absolute path to the written knowledge catalog file.
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


def _print_report(builder: KnowledgeCatalogBuilder, records: list[dict[str, Any]]) -> None:
    """Print the build summary report to stdout.

    Args:
        builder: The builder instance used to produce the records.
        records: The full list of generated record dictionaries.
    """
    mismatched_codes = {
        record["evidence_code"]
        for record in records
        if record["level_number"] is None or record["acceptance_criteria"] is None
    }
    linked_count = len(records) - len(mismatched_codes)

    example = next(
        (record for record in records if record["evidence_code"] == "DC.M.6"),
        None,
    )

    print("=== تقرير بناء الفهرس المعرفي (Knowledge Catalog) ===")
    print(f"1. عدد Records داخل Knowledge Catalog: {len(records)}")
    print(f"   عدد الأدلة التي تم ربطها بنجاح (موجودة في المصدرين): {linked_count}")

    print(f"\n2. عدد التحذيرات: {len(builder.warnings)}")
    if builder.warnings:
        for warning in builder.warnings:
            print(f"   - {warning}")
    else:
        print("   لا توجد تحذيرات — جميع الأدلة موجودة في المصدرين وتم ربطها بنجاح.")

    print("\n3. مثال كامل لـ DC.M.6:")
    print(json.dumps(example, ensure_ascii=False, indent=2))

    print("\n4. تأكيد مصادر الحقول:")
    print("   - level_description جاء من description في maturity_models.")
    print("   - maturity_requirement جاء من maturity_requirement في maturity_models (لكل evidence).")
    print("   - acceptance_criteria جاء من acceptance_criteria في evidence_catalog فقط.")

    if example is not None:
        level_description = example.get("level_description") or ""
        maturity_requirement = example.get("maturity_requirement") or ""
        contains_full_description = bool(level_description) and level_description in maturity_requirement
        print(
            "\n5. تأكيد أن DC.M.6 لا يحتوي على وصف المستوى كامل داخل maturity_requirement: "
            + ("لا (تحذير: النصان متطابقان)" if contains_full_description else "مؤكد — النصان مختلفان.")
        )

    print(f"\nمسار ملف dc_knowledge_catalog.json: {builder.output_path}")


def main() -> None:
    """Build the DC knowledge catalog and print a summary report."""
    project_root = Path(__file__).resolve().parents[2]
    builder = KnowledgeCatalogBuilder(project_root)
    records = builder.run()
    _print_report(builder, records)


if __name__ == "__main__":
    main()
