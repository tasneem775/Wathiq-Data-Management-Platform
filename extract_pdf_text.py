import fitz  # PyMuPDF
from pathlib import Path


INPUT_DIR = Path("knowledge_base/ndi_framework")
OUTPUT_DIR = Path("data/extracted_text")


def extract_text_from_pdf(pdf_path: Path) -> str:
    text_parts = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pdf_files = list(INPUT_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {INPUT_DIR}")
        return

    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")
        try:
            text = extract_text_from_pdf(pdf_path)
            output_path = OUTPUT_DIR / (pdf_path.stem + ".txt")
            output_path.write_text(text, encoding="utf-8")
            print(f"  Saved: {output_path}")
        except Exception as e:
            print(f"  Error processing {pdf_path.name}: {e}")

    print("\nDone.")


if __name__ == "__main__":
    main()
