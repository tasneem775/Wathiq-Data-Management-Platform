# -*- coding: utf-8 -*-
"""Builds the supporting Excel calculation sheet for DC.M.3-E01
(DC-KPI-01 — نسبة مجموعات البيانات المصنفة).

All per-dataset rows (identifier, name, classification level, classification status) are
copied verbatim from the real evidence_repository file DC.M.5.docx. No dataset name, level,
or count is invented. Saved alongside the DC.M.3-E01 docx/pdf, same folder, same file name
stem, .xlsx extension.
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT_PATH = "06_DC_M3_KPI_Evidence/DC.M.3-E01_Data_Classification_KPI_Calculation_Record.xlsx"

NAVY = "1F2A44"
GOLD = "AB8654"
LIGHT_GREY = "F2F2F2"
WHITE = "FFFFFF"
GREEN = "1F6F43"
AR_FONT = "Arial"

# ============ بيانات مصدرها الحرفي DC.M.5.docx ============
DATASETS_FROM_DC_M5 = [
    (1, "بيانات الخدمات الحكومية الرقمية", "عام"),
    (2, "بيانات التقارير التشغيلية", "عام"),
    (3, "بيانات استطلاعات رأي المستفيدين", "عام"),
    (4, "بيانات المستخدمين", "سرّي"),
    (5, "بيانات طلبات المستفيدين", "مقيّد"),
    (6, "بيانات البلاغات والشكاوى", "مقيّد"),
    (7, "بيانات الموردين", "مقيّد"),
    (8, "بيانات الأصول التقنية", "سرّي"),
    (9, "بيانات المراسلات الرسمية", "مقيّد"),
    (10, "بيانات الاجتماعات واللجان", "مقيّد"),
    (11, "بيانات الموظفين", "سرّي"),
    (12, "بيانات الرواتب والمزايا", "سرّي"),
    (13, "بيانات العقود والاتفاقيات", "سرّي"),
    (14, "بيانات الصلاحيات وإدارة الهوية", "سرّي"),
    (15, "بيانات المدفوعات المالية", "سرّي"),
    (16, "بيانات الميزانية التشغيلية", "سرّي"),
    (17, "بيانات التدقيق الداخلي", "سرّي"),
    (18, "بيانات الهوية والتحقق الإلكتروني", "سرّي للغاية"),
    (19, "بيانات التكامل مع الجهات الحكومية", "سرّي للغاية"),
    (20, "بيانات سجلات الأحداث الأمنية", "سرّي للغاية"),
]
TOTAL_RECORDS = len(DATASETS_FROM_DC_M5)          # 20 — كما هو في DC.M.5
CLASSIFIED_RECORDS = len(DATASETS_FROM_DC_M5)      # 20 — جميعها بحالة "مصنفة" في DC.M.5
FORMULA_TEXT = "عدد مجموعات البيانات المصنفة ÷ إجمالي مجموعات البيانات × 100"
FINAL_RESULT = f"{round(CLASSIFIED_RECORDS / TOTAL_RECORDS * 100)}%"  # "100%"

wb = Workbook()
ws = wb.active
ws.title = "احتساب DC-KPI-01"
ws.sheet_view.showGridLines = False
ws.sheet_view.rightToLeft = True

thin = Side(style="thin", color="D9D9D9")
border = Border(left=thin, right=thin, top=thin, bottom=thin)

N_COLS = 8
r = 1


def merged_text(row, text, size, bold, color, fill=None, height=None, italic=False, span=N_COLS):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=span)
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = Font(name=AR_FONT, size=size, bold=bold, italic=italic, color=color)
    cell.alignment = Alignment(horizontal="right", vertical="center", indent=1, wrap_text=True)
    if fill:
        cell.fill = PatternFill("solid", fgColor=fill)
    if height:
        ws.row_dimensions[row].height = height
    return row + 1


def section_heading(row, text, span=N_COLS):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=span)
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = Font(name=AR_FONT, size=12.5, bold=True, color=NAVY)
    cell.alignment = Alignment(horizontal="right", vertical="center", indent=1)
    cell.border = Border(bottom=Side(style="medium", color=GOLD))
    ws.row_dimensions[row].height = 22
    return row + 1


def spacer(row, h=10):
    ws.row_dimensions[row].height = h
    return row + 1


def meta_row(row, label, value):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
    c1 = ws.cell(row=row, column=1, value=label)
    c1.font = Font(name=AR_FONT, size=10, bold=True, color="595959")
    c1.alignment = Alignment(horizontal="right", vertical="center", indent=1)
    ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=N_COLS)
    c2 = ws.cell(row=row, column=3, value=value)
    c2.font = Font(name=AR_FONT, size=10, color="262626")
    c2.alignment = Alignment(horizontal="right", vertical="center", indent=1)
    return row + 1


# ============ Title banner ============
r = merged_text(r, "سجل احتساب مؤشر نسبة مجموعات البيانات المصنفة (DC-KPI-01)", 18, True, WHITE, fill=NAVY, height=32)
r = merged_text(r, "منصة ذكية لإدارة وقياس الامتثال لمتطلبات المكتب الوطني لإدارة البيانات (NDMO)", 10.5, True, WHITE, fill=NAVY, height=20)
r = spacer(r, 6)
r = merged_text(r, "سجل احتساب مؤشر نسبة مجموعات البيانات المصنفة (DC-KPI-01)", 14, True, NAVY, height=24)
r = merged_text(r, "دليل داعم — DC.M.3-E01", 11, True, GOLD, italic=True, height=18)
r = spacer(r, 10)

# ============ بيانات الوثيقة ============
r = section_heading(r, "بيانات الوثيقة")
r = spacer(r, 4)
r = meta_row(r, "الجهة", "هيئة الخدمات الحكومية الذكية (SGSA)")
r = meta_row(r, "المنصة", "")
r = meta_row(r, "الإطار المرجعي", "إطار حوكمة البيانات الوطني (NDMO)")
r = meta_row(r, "رمز الدليل", "DC.M.3-E01")
r = meta_row(r, "المتطلب المرتبط", "DC.M.3 — تقرير مراقبة تنفيذ خطة تصنيف البيانات عبر مؤشرات الأداء الرئيسية")
r = meta_row(r, "المؤشر المرتبط", "DC-KPI-01 — نسبة مجموعات البيانات المصنفة")
r = meta_row(r, "مصدر البيانات", "DC.M.5 — القائمة الحالية لمجموعات البيانات المصنفة")
r = meta_row(r, "الإصدار", "1.0")
r = meta_row(r, "التاريخ", "يونيو 2026")
r = meta_row(r, "حالة الوثيقة", "جاهزة للاعتماد")
r = spacer(r, 16)

# ============ جدول بيانات الاحتساب ============
r = section_heading(r, "بيانات الاحتساب (مصدرها سجل DC.M.5)")
r = spacer(r, 4)

headers = [
    "الرقم التسلسلي في سجل DC.M.5",
    "اسم مجموعة البيانات",
    "مستوى التصنيف",
    "حالة التصنيف",
    "إجمالي السجلات",
    "عدد السجلات المصنفة",
    "معادلة الحساب",
    "النتيجة النهائية",
]
header_row = r
for c, h in enumerate(headers, start=1):
    cell = ws.cell(row=header_row, column=c, value=h)
    cell.font = Font(name=AR_FONT, size=10, bold=True, color=WHITE)
    cell.fill = PatternFill("solid", fgColor=NAVY)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = border
ws.row_dimensions[header_row].height = 34
r += 1

for i, (n, name, level) in enumerate(DATASETS_FROM_DC_M5):
    row_fill = LIGHT_GREY if i % 2 == 0 else WHITE
    row_vals = [
        f"{n:02d}", name, level, "مصنفة",
        TOTAL_RECORDS, CLASSIFIED_RECORDS, FORMULA_TEXT, FINAL_RESULT,
    ]
    for c, v in enumerate(row_vals, start=1):
        cell = ws.cell(row=r, column=c, value=v)
        cell.border = border
        cell.fill = PatternFill("solid", fgColor=row_fill)
        center_cols = (1, 3, 4, 5, 6, 8)
        cell.alignment = Alignment(
            horizontal="center" if c in center_cols else "right",
            vertical="center", wrap_text=True,
            indent=0 if c in center_cols else 1,
        )
        if c == 1:
            cell.font = Font(name=AR_FONT, size=10, bold=True, color=NAVY)
        elif c == 4:
            cell.font = Font(name=AR_FONT, size=10, bold=True, color=GREEN)
        elif c == 8:
            cell.font = Font(name=AR_FONT, size=10, bold=True, color=GREEN)
        else:
            cell.font = Font(name=AR_FONT, size=9.5, color="262626")
    ws.row_dimensions[r].height = 28
    r += 1

r = spacer(r, 16)
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=N_COLS)
note1 = ws.cell(
    row=r, column=1,
    value=(
        "ملاحظة: أعمدة «إجمالي السجلات»، «عدد السجلات المصنفة»، «معادلة الحساب»، و«النتيجة النهائية» "
        "تمثل نتيجة الاحتساب الإجمالي الواحد (20 ÷ 20 × 100 = 100%)، وهي مكرَّرة عبر كل صف لتسهيل "
        "الفرز والتحقق الآلي؛ وليست قيماً مستقلة لكل مجموعة بيانات."
    ),
)
note1.font = Font(name=AR_FONT, size=8, italic=True, color="7F7F7F")
note1.alignment = Alignment(horizontal="right", vertical="center", wrap_text=True, indent=1)
ws.row_dimensions[r].height = 30
r += 1

r = spacer(r, 14)

# ============ الاعتماد ============
r = section_heading(r, "التحقق والاعتماد")
r = spacer(r, 4)
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=N_COLS)
review_cell = ws.cell(
    row=r, column=1,
    value="تمت مراجعة هذا السجل من مكتب إدارة البيانات، وتم التحقق من مطابقة البيانات الواردة فيه لمحتوى سجل DC.M.5 دون أي إضافة أو حذف أو تعديل.",
)
review_cell.font = Font(name=AR_FONT, size=10, color="262626")
review_cell.alignment = Alignment(horizontal="right", vertical="center", wrap_text=True, indent=1)
ws.row_dimensions[r].height = 26
r += 1
r = spacer(r, 6)

approval_headers = ["صاحب الصلاحية", "المسمى الوظيفي", "التوقيع", "التاريخ"]
col_spans = [(1, 2), (3, 4), (5, 6), (7, 8)]
approval_header_row = r
for (sc, ec), h in zip(col_spans, approval_headers):
    ws.merge_cells(start_row=approval_header_row, start_column=sc, end_row=approval_header_row, end_column=ec)
    cell = ws.cell(row=approval_header_row, column=sc, value=h)
    cell.font = Font(name=AR_FONT, size=10, bold=True, color=WHITE)
    cell.fill = PatternFill("solid", fgColor=NAVY)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    for cc in range(sc, ec + 1):
        ws.cell(row=approval_header_row, column=cc).border = border
ws.row_dimensions[approval_header_row].height = 20
r += 1

approval_values = ["____________", "مدير مكتب إدارة البيانات", "____________", "____________"]
for (sc, ec), v in zip(col_spans, approval_values):
    ws.merge_cells(start_row=r, start_column=sc, end_row=r, end_column=ec)
    cell = ws.cell(row=r, column=sc, value=v)
    cell.font = Font(name=AR_FONT, size=9.5, color="262626")
    cell.alignment = Alignment(horizontal="center", vertical="center")
    for cc in range(sc, ec + 1):
        ws.cell(row=r, column=cc).border = border
ws.row_dimensions[r].height = 26
r += 1

r = spacer(r, 14)
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=N_COLS)
note2 = ws.cell(
    row=r, column=1,
    value="ملاحظة: هذا الملف دليل داعم مستقل ضمن حزمة أدلة تصنيف البيانات الخاصة بهيئة الخدمات الحكومية الذكية (SGSA)، أُعدّ لتوثيق بيانات احتساب مؤشر DC-KPI-01 دون تعديل أي محتوى في تقرير DC.M.3 أو سجل DC.M.5.",
)
note2.font = Font(name=AR_FONT, size=8, italic=True, color="7F7F7F")
note2.alignment = Alignment(horizontal="right", vertical="center", wrap_text=True, indent=1)
ws.row_dimensions[r].height = 26

# ============ Column widths ============
widths = [14, 26, 12, 12, 10, 12, 40, 12]
for i, w in enumerate(widths, start=1):
    ws.column_dimensions[get_column_letter(i)].width = w

wb.save(OUT_PATH)
print("Saved:", OUT_PATH)
print("Rows:", len(DATASETS_FROM_DC_M5), "Total:", TOTAL_RECORDS, "Classified:", CLASSIFIED_RECORDS, "Result:", FINAL_RESULT)
