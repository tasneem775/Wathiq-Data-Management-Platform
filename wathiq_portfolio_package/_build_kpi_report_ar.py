"""Localizes KPI_Supporting_Data_Report.xlsx into Arabic under the Wathiq governance
identity. Overwrites the SAME file path in place — no new file is created.

Controlled localization / compliance-formatting pass only:
  - No KPI values changed.
  - No calculation logic changed.
  - No evidence source invented — single source (DC.C.3.4) used throughout.
  - No new indicators added or removed.
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT_PATH = "01_KPI_Supporting_Data_Report/KPI_Supporting_Data_Report.xlsx"

NAVY = "1F2A44"
GOLD = "AB8654"
LIGHT_GREY = "F2F2F2"
WHITE = "FFFFFF"
GREEN = "1F6F43"
AR_FONT = "Arial"

# ---- Preserved KPI values (UNCHANGED from the original English version) ----
KPIS = [
    (
        "نسبة تغطية المراجعة",
        "نسبة مجموعات البيانات المصنفة التي شملتها دورة المراجعة الحالية من إجمالي الأصول المسجَّلة.",
        "DC.C.3.4 – تقرير مراجعة تصنيف البيانات",
        "(عدد الأصول التي تمت مراجعتها ÷ إجمالي عدد الأصول) × 100",
        "100%",
    ),
    (
        "الأصول التي تمت مراجعتها",
        "إجمالي عدد الأصول البيانية (مجموعات البيانات والسجلات) التي جرت مراجعتها ضمن دورة المراجعة.",
        "DC.C.3.4 – تقرير مراجعة تصنيف البيانات",
        "عدّ مباشر لعدد الأصول التي خضعت لدورة المراجعة",
        "30",
    ),
    (
        "تغييرات التصنيف",
        "عدد الأصول التي عُدِّل مستوى تصنيفها كنتيجة لعملية المراجعة.",
        "DC.C.3.4 – تقرير مراجعة تصنيف البيانات",
        "عدّ الأصول التي صدر بشأنها قرار تعديل/تخفيض ضمن نتائج المراجعة",
        "3",
    ),
    (
        "مدة المراجعة",
        "إجمالي الفترة الزمنية اللازمة لإنجاز دورة المراجعة الكاملة من بدايتها حتى إغلاقها.",
        "DC.C.3.4 – تقرير مراجعة تصنيف البيانات",
        "تاريخ إقفال الدورة (15 يونيو 2026) − تاريخ بدء الدورة (1 مايو 2026)",
        "6 أسابيع",
    ),
    (
        "مشاركة ملاك البيانات",
        "عدد ملاك البيانات الذين شاركوا فعلياً في دورة المراجعة عبر مختلف الإدارات.",
        "DC.C.3.4 – تقرير مراجعة تصنيف البيانات",
        "عدّ مباشر لعدد ملاك البيانات المشاركين فعلياً في الدورة",
        "12",
    ),
]

SOURCE_ROWS = [
    ("نسبة تغطية المراجعة", "100%", "DC.C.3.4 – تقرير مراجعة تصنيف البيانات"),
    ("الأصول التي تمت مراجعتها", "30", "DC.C.3.4 – تقرير مراجعة تصنيف البيانات"),
    ("تغييرات التصنيف", "3", "DC.C.3.4 – تقرير مراجعة تصنيف البيانات"),
    ("مدة المراجعة", "6 أسابيع", "DC.C.3.4 – تقرير مراجعة تصنيف البيانات"),
    ("مشاركة ملاك البيانات", "12", "DC.C.3.4 – تقرير مراجعة تصنيف البيانات"),
]

wb = Workbook()
ws = wb.active
ws.title = "تقرير المؤشرات"
ws.sheet_view.showGridLines = False
ws.sheet_view.rightToLeft = True

thin = Side(style="thin", color="D9D9D9")
border = Border(left=thin, right=thin, top=thin, bottom=thin)

r = 1

def merged_text(row, text, size, bold, color, fill=None, height=None, italic=False):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = Font(name=AR_FONT, size=size, bold=bold, italic=italic, color=color)
    cell.alignment = Alignment(horizontal="right", vertical="center", indent=1, wrap_text=True)
    if fill:
        cell.fill = PatternFill("solid", fgColor=fill)
    if height:
        ws.row_dimensions[row].height = height
    return row + 1

def section_heading(row, text):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = Font(name=AR_FONT, size=12.5, bold=True, color=NAVY)
    cell.alignment = Alignment(horizontal="right", vertical="center", indent=1)
    cell.border = Border(bottom=Side(style="medium", color=GOLD))
    ws.row_dimensions[row].height = 22
    return row + 1

def spacer(row, h=10):
    ws.row_dimensions[row].height = h
    return row + 1

# ---- Title banner ----
r = merged_text(r, "تقرير المؤشرات الداعم لإدارة ومراقبة تصنيف البيانات", 18, True, WHITE, fill=NAVY, height=32)
r = merged_text(r, "منصة ذكية لإدارة وقياس الامتثال لمتطلبات المكتب الوطني لإدارة البيانات (NDMO)", 10.5, True, WHITE, fill=NAVY, height=20)
r = spacer(r, 6)
r = merged_text(r, "تقرير المؤشرات — البيانات الداعمة لتصنيف البيانات", 13.5, True, NAVY, height=22)
r = spacer(r, 8)

# ---- Meta block ----
meta_rows = [
    ("الجهة", "هيئة الخدمات الحكومية الذكية (SGSA)"),
    ("القسم", "مكتب إدارة البيانات"),
    ("النطاق", "تصنيف البيانات"),
    ("الإطار المرجعي", "إطار حوكمة البيانات الوطني (NDMO)"),
    ("المتطلبات المدعومة", "DC.M.2   •   DC.M.3   •   DC.C.4.1   •   DC.M.12"),
    ("دورة المراجعة", "1 مايو 2026 – 15 يونيو 2026 (6 أسابيع)"),
    ("مصدر البيانات", "DC.C.3.4 – تقرير مراجعة تصنيف البيانات"),
]
for label, value in meta_rows:
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
    c1 = ws.cell(row=r, column=1, value=label)
    c1.font = Font(name=AR_FONT, size=10, bold=True, color="595959")
    c1.alignment = Alignment(horizontal="right", vertical="center", indent=1)
    ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=5)
    c2 = ws.cell(row=r, column=3, value=value)
    c2.font = Font(name=AR_FONT, size=10, color="262626")
    c2.alignment = Alignment(horizontal="right", vertical="center", indent=1)
    r += 1

r = spacer(r, 14)

# ---- الغرض من التقرير ----
r = section_heading(r, "الغرض من التقرير")
r = spacer(r, 4)
purpose_text = (
    "يهدف هذا التقرير إلى تقديم بيانات المؤشرات الداعمة لعملية مراقبة تصنيف البيانات، "
    "استنادًا إلى نتائج دورة مراجعة تصنيف البيانات الموثقة، ويدعم بشكل "
    "مباشر متطلبات DC.M.2 وDC.M.3 وDC.C.4.1 وDC.M.12."
)
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
c = ws.cell(row=r, column=1, value=purpose_text)
c.font = Font(name=AR_FONT, size=10, color="262626")
c.alignment = Alignment(horizontal="right", vertical="center", wrap_text=True, indent=1)
ws.row_dimensions[r].height = 40
r += 1
r = spacer(r, 14)

# ---- KPI table ----
r = section_heading(r, "تقرير المؤشرات (KPI)")
r = spacer(r, 4)

table_header_row = r
headers = ["اسم المؤشر", "الوصف", "مصدر البيانات", "طريقة الحساب", "القيمة"]
for c_idx, h in enumerate(headers, start=1):
    cell = ws.cell(row=table_header_row, column=c_idx, value=h)
    cell.font = Font(name=AR_FONT, size=11, bold=True, color=WHITE)
    cell.fill = PatternFill("solid", fgColor=NAVY)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = border
ws.row_dimensions[table_header_row].height = 22
r += 1

for i, (name, desc, source, calc, value) in enumerate(KPIS):
    row_fill = LIGHT_GREY if i % 2 == 0 else WHITE
    values = [name, desc, source, calc, value]
    for c_idx, v in enumerate(values, start=1):
        cell = ws.cell(row=r, column=c_idx, value=v)
        cell.border = border
        cell.alignment = Alignment(horizontal="center" if c_idx == 5 else "right", vertical="center", wrap_text=True, indent=1 if c_idx != 5 else 0)
        cell.fill = PatternFill("solid", fgColor=row_fill)
        if c_idx == 1:
            cell.font = Font(name=AR_FONT, size=10, bold=True, color=NAVY)
        elif c_idx == 5:
            cell.font = Font(name=AR_FONT, size=11, bold=True, color=GREEN)
        else:
            cell.font = Font(name=AR_FONT, size=10, color="262626")
    ws.row_dimensions[r].height = 44
    r += 1

r = spacer(r, 16)

# ---- مصادر بيانات المؤشرات ----
r = section_heading(r, "مصادر بيانات المؤشرات")
r = spacer(r, 4)

src_header_row = r
src_headers = ["المؤشر", "القيمة", "مصدر البيانات"]
src_widths_cols = [(1, 2), (3, 3), (4, 5)]  # merge spans across the 5 base columns
for (start_c, end_c), h in zip(src_widths_cols, src_headers):
    ws.merge_cells(start_row=src_header_row, start_column=start_c, end_row=src_header_row, end_column=end_c)
    cell = ws.cell(row=src_header_row, column=start_c, value=h)
    cell.font = Font(name=AR_FONT, size=10.5, bold=True, color=WHITE)
    cell.fill = PatternFill("solid", fgColor=NAVY)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = border
    for cc in range(start_c, end_c + 1):
        ws.cell(row=src_header_row, column=cc).border = border
ws.row_dimensions[src_header_row].height = 20
r += 1

for i, (kpi_name, value, source) in enumerate(SOURCE_ROWS):
    row_fill = LIGHT_GREY if i % 2 == 0 else WHITE
    for (start_c, end_c), v, bold, color in zip(
        src_widths_cols,
        [kpi_name, value, source],
        [True, True, False],
        [NAVY, GREEN, "262626"],
    ):
        ws.merge_cells(start_row=r, start_column=start_c, end_row=r, end_column=end_c)
        cell = ws.cell(row=r, column=start_c, value=v)
        cell.font = Font(name=AR_FONT, size=10, bold=bold, color=color)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.fill = PatternFill("solid", fgColor=row_fill)
        for cc in range(start_c, end_c + 1):
            ws.cell(row=r, column=cc).border = border
            ws.cell(row=r, column=cc).fill = PatternFill("solid", fgColor=row_fill)
    ws.row_dimensions[r].height = 20
    r += 1

r = spacer(r, 16)

# ---- مرجعية البيانات ----
r = section_heading(r, "مرجعية البيانات")
r = spacer(r, 4)
provenance_text = (
    "جميع قيم المؤشرات الواردة في هذا التقرير مستخرجة من النتائج الموثقة في تقرير مراجعة "
    "تصنيف البيانات (DC.C.3.4)، ولم يُستخدم أي مصدر بيانات آخر في إعداد هذا التقرير."
)
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
c = ws.cell(row=r, column=1, value=provenance_text)
c.font = Font(name=AR_FONT, size=10, italic=True, color="595959")
c.alignment = Alignment(horizontal="right", vertical="center", wrap_text=True, indent=1)
ws.row_dimensions[r].height = 34
r += 1

# ---- Column widths ----
widths = [22, 42, 30, 40, 14]
for i, w in enumerate(widths, start=1):
    ws.column_dimensions[get_column_letter(i)].width = w

wb.save(OUT_PATH)
print("Saved (overwritten in place):", OUT_PATH)
