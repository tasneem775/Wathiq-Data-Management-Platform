"""Patch DC.C.1.2.docx — update DC.C.1.1 row in section 4 table."""
from docx import Document

PATH = (r"c:\Users\extra\Downloads\NDI-Sentinel"
        r"\evidence_repository\data_classification\MQ2\DC.C.1.2.docx")

doc = Document(PATH)

TARGET_CODE = "DC.C.1.1"
NEW_NAME    = "الخطة المعرفة والمعتمدة لتصنيف البيانات"
NEW_REL     = "المرجع التنفيذي لتطبيق برنامج تصنيف البيانات"

patched = False
for table in doc.tables:
    for row in table.rows:
        texts = [c.text.strip() for c in row.cells]
        if TARGET_CODE in texts:
            # Identify which cell index holds which column by position.
            # Table has 3 cols (visual RTL): رمز | اسم | علاقة
            # With bidiVisual: cells[0]=العلاقة, cells[1]=اسم الوثيقة, cells[2]=رمز الوثيقة
            for ci, cell in enumerate(row.cells):
                if cell.text.strip() == "DC.C.1.1":
                    # This is the رمز cell — leave unchanged
                    pass
                elif cell.text.strip() in ("نموذج طلب تصنيف البيانات",):
                    # Replace اسم الوثيقة
                    for para in cell.paragraphs:
                        for run in para.runs:
                            if "نموذج طلب تصنيف البيانات" in run.text:
                                run.text = run.text.replace(
                                    "نموذج طلب تصنيف البيانات", NEW_NAME)
                    patched = True
                elif cell.text.strip() in ("الأداة الرسمية لتقديم طلبات التصنيف",):
                    # Replace العلاقة
                    for para in cell.paragraphs:
                        for run in para.runs:
                            if "الأداة الرسمية لتقديم طلبات التصنيف" in run.text:
                                run.text = run.text.replace(
                                    "الأداة الرسمية لتقديم طلبات التصنيف", NEW_REL)
                    patched = True

if not patched:
    print("ERROR: target row not found")
else:
    doc.save(PATH)
    # Verify
    doc2 = Document(PATH)
    for table in doc2.tables:
        for row in table.rows:
            texts = [c.text.strip() for c in row.cells]
            if TARGET_CODE in texts:
                print("VERIFIED ROW:")
                for c in row.cells:
                    print(f"  [{c.text.strip()}]")
