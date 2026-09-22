"""Entry point for running a basic catalog validation check."""

from __future__ import annotations

from pathlib import Path

from src.catalog.catalog_loader import CatalogLoadError
from src.catalog.catalog_service import CatalogService


def main() -> None:
    """Run a basic catalog validation check."""
    project_root = Path(__file__).resolve().parents[2]
    service = CatalogService(project_root)

    try:
        catalog = service.get_catalog()
        path_errors = service.validate_referenced_paths()
    except CatalogLoadError as error:
        print(f"Catalog validation failed: {error}")
        return

    print("Catalog validation completed.")
    print(f"Catalog ID: {catalog['catalog_id']}")
    print(f"Domain: {catalog['domain']['name_ar']} ({catalog['domain']['code']})")
    print(f"MQ catalogs: {len(catalog['mq_catalogs'])}")

    if path_errors:
        print("Path validation errors:")
        for error in path_errors:
            print(f"- {error}")
    else:
        print("All referenced paths are valid.")


if __name__ == "__main__":
    main()
