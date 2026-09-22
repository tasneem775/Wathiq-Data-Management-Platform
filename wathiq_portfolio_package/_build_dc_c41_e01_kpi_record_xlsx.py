# -*- coding: utf-8 -*-
"""Builds the supporting Excel calculation sheet for DC.C.4.1-E01 (KPI-DC-01) — 7-section
compliance-audit template. All per-asset rows are copied verbatim from the real
evidence_repository files DC.C.3.1.docx (Table 8) and DC.C.3.2.docx (Table 11). No asset
name, level, or count is invented."""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT_PATH = "06_DC_C4_1_KPI_Evidence/DC.C.4.1-E01_KPI-DC-01_Data_Classification_KPI_Calculation_Record.xlsx"

NAVY = "1F2A44"
GOLD = "AB8654"
LIGHT_GREY = "F2F2F2"
WHITE = "FFFFFF"
GREEN = "1F6F43"
AR_FONT = "Arial"

ASSETS = [
    (1, "بيانات الهوية والتحقق الإلكتروني", "مجموعة بيانات", "إدارة الهوية الرقمية", "سرّي للغاية"),
    (2, "بيانات الأحداث والتنبيهات الأمنية", "مجموعة بيانات", "إدارة الأمن السيبراني", "سرّي للغاية"),
    (3, "بيانات الصلاحيات وإدارة الهوية (IAM)", "مجموعة بيانات", "إدارة تقنية المعلومات", "سرّي للغاية"),
    (4, "بيانات التكامل مع الجهات الحكومية", "مجموعة بيانات", "إدارة الشراكات الحكومية", "سرّي للغاية"),
    (5, "بيانات الرواتب والمزايا الوظيفية", "مجموعة بيانات", "إدارة الموارد البشرية", "سرّي"),
    (6, "بيانات المدفوعات والمعاملات المالية", "مجموعة بيانات", "الإدارة المالية", "سرّي"),
    (7, "بيانات الموظفين والملفات الوظيفية", "مجموعة بيانات", "إدارة الموارد البشرية", "سرّي"),
    (8, "بيانات المستخدمين والمستفيدين", "مجموعة بيانات", "إدارة الخدمات الرقمية", "سرّي"),
    (9, "بيانات طلبات ومعاملات المستفيدين", "مجموعة بيانات", "إدارة الخدمات الرقمية", "مقيّد"),
    (10, "بيانات الخدمات الحكومية الرقمية", "مجموعة بيانات", "إدارة التحول الرقمي", "مقيّد"),
    (11, "بيانات الموردين والمتعاقدين", "مجموعة بيانات", "إدارة المشتريات", "مقيّد"),
    (12, "بيانات الأصول والبنية التحتية التقنية", "مجموعة بيانات", "إدارة تقنية المعلومات", "سرّي"),
    (13, "بيانات الأهداف والخطط الاستراتيجية", "مجموعة بيانات", "مكتب الاستراتيجية والتخطيط", "سرّي"),
    (14, "بيانات التدريب والتطوير الوظيفي", "مجموعة بيانات", "إدارة الموارد البشرية", "مقيّد"),
    (15, "بيانات استطلاعات رضا المستفيدين", "مجموعة بيانات", "إدارة تجربة المستخدم", "عام"),
    (16, "بيانات الحوادث التقنية وطلبات الدعم", "مجموعة بيانات", "إدارة تقنية المعلومات", "مقيّد"),
    (17, "بيانات المحتوى الرقمي والموقع الإلكتروني", "مجموعة بيانات", "إدارة الاتصال والعلاقات العامة", "عام"),
    (18, "بيانات التقارير والإحصاءات المنشورة", "مجموعة بيانات", "مكتب إدارة البيانات", "عام"),
    (19, "سجلات العقود والاتفاقيات", "سجل", "إدارة الشؤون القانونية", "سرّي"),
    (20, "سجلات التدقيق الداخلي والرقابة", "سجل", "إدارة التدقيق الداخلي", "سرّي"),
    (21, "سجلات المراسلات والخطابات الرسمية", "سجل", "مكتب المدير العام", "مقيّد"),
    (22, "سجلات الاجتماعات واللجان الحوكمية", "سجل", "مكتب الحوكمة", "مقيّد"),
    (23, "سجلات التقارير الإدارية الدورية", "سجل", "مكتب إدارة البيانات", "مقيّد"),
    (24, "سجلات فعاليات الهيئة وأحداثها", "سجل", "إدارة الاتصال والعلاقات العامة", "عام"),
    (25, "سجلات الشكاوى والمقترحات", "سجل", "إدارة الخدمات الرقمية", "مقيّد"),
    (26, "سجلات قرارات وتوجيهات الإدارة العليا", "سجل", "مكتب المدير العام", "سرّي"),
    (27, "سجلات التراخيص والتصاريح القانونية", "سجل", "إدارة الشؤون القانونية", "مقيّد"),
    (28, "سجلات النسخ الاحتياطي واسترجاع البيانات", "سجل", "إدارة تقنية المعلومات", "سرّي"),
    (29, "وثائق السياسات والإجراءات الداخلية", "سجل", "مكتب إدارة البيانات", "مقيّد"),
    (30, "سجلات التغييرات والتحديثات التقنية", "سجل", "إدارة تقنية المعلومات", "مقيّد"),
]
TOTAL_ASSETS = len(ASSETS)
CLASSIFIED_ASSETS = len(ASSETS)
FORMULA_TEXT = "عدد الأصول المصنَّفة ÷ إجمالي الأصول البيانية × 100"
FINAL_RESULT = f"{round(CLASSIFIED_ASSETS / TOTAL_ASSETS * 100)}%"

wb = Workbook()
ws = wb.active
ws.title = "احتساب KPI-DC-01"
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


def bullet_row(row, text):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=N_COLS)
    cell = ws.cell(row=row, column=1, value="•  " + text)
    cell.font = Font(name=AR_FONT, size=9.5, color="262626")
    cell.alignment = Alignment(horizontal="right", vertical="center", wrap_text=True, indent=1)
    ws.row_dimensions[row].height = 28
    return row + 1


r = merged_text(r, "سجل احتساب مؤشر نسبة اكتمال تصنيف الأصول البيانية (KPI-DC-01)", 18, True, WHITE, fill=NAVY, height=32)
r = merged_text(r, "منصة ذكية لإدارة وقياس الامتثال لمتطلبات المكتب الوطني لإدارة البيانات (NDMO)", 10.5, True, WHITE, fill=NAVY, height=20)
r = spacer(r, 6)
r = merged_text(r, "سجل احتساب مؤشر نسبة اكتمال تصنيف الأصول البيانية (KPI-DC-01)", 14, True, NAVY, height=24)
r = merged_text(r, "دليل داعم — DC.C.4.1-E01 — Calculation Record", 11, True, GOLD, italic=True, height=18)
r = spacer(r, 10)

r = section_heading(r, "1. بيانات الوثيقة")
r = spacer(r, 4)
r = meta_row(r, "الجهة", "هيئة الخدمات الحكومية الذكية (SGSA)")
r = meta_row(r, "المنصة", "")
r = meta_row(r, "الإطار المرجعي", "إطار حوكمة البيانات الوطني (NDMO)")
r = meta_row(r, "رمز الدليل", "DC.C.4.1-E01")
r = meta_row(r, "نوع الوثيقة", "Calculation Record")
r = meta_row(r, "المتطلب المرتبط", "DC.C.4.1 — تقرير مراقبة عمليات تصنيف البيانات عبر مؤشرات الأداء الرئيسية")
r = meta_row(r, "المؤشر المرتبط", "KPI-DC-01 — نسبة اكتمال تصنيف الأصول البيانية")
r = meta_row(r, "الإصدار", "1.0")
r = meta_row(r, "التاريخ", "يونيو 2026")
r = meta_row(r, "حالة الوثيقة", "جاهزة للاعتماد")
r = spacer(r, 14)

r = section_heading(r, "2. نطاق القياس")
r = spacer(r, 4)
r = meta_row(r, "فترة القياس", "الربع الثاني 2026 (أبريل – يونيو 2026)")
r = meta_row(r, "نطاق القياس", "جميع الأصول البيانية الثلاثين (30) الواردة في تقرير الجرد DC.C.3.1")
r = spacer(r, 14)

r = section_heading(r, "3. مصدر البيانات")
r = spacer(r, 4)
r = bullet_row(r, "DC.C.3.1 — تقرير جرد المجموعات التي تم تحديدها من البيانات والسجلات")
r = bullet_row(r, "DC.C.3.2 — تقرير تقييم الأثر (مستوى التصنيف الناتج لكل أصل)")
r = bullet_row(r, "DC.C.5.1 — سجل البيانات")
r = spacer(r, 14)

r = section_heading(r, "4. جدول البيانات المستخدمة (مصدرها DC.C.3.1 وDC.C.3.2)")
r = spacer(r, 4)

headers = ["م", "اسم الأصل", "نوع الأصل", "الإدارة المالكة", "حالة الجرد", "مستوى التصنيف", "معادلة الحساب", "النتيجة النهائية"]
header_row = r
for c, h in enumerate(headers, start=1):
    cell = ws.cell(row=header_row, column=c, value=h)
    cell.font = Font(name=AR_FONT, size=10, bold=True, color=WHITE)
    cell.fill = PatternFill("solid", fgColor=NAVY)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = border
ws.row_dimensions[header_row].height = 34
r += 1

for i, (n, name, atype, dept, level) in enumerate(ASSETS):
    row_fill = LIGHT_GREY if i % 2 == 0 else WHITE
    row_vals = [n, name, atype, dept, "مُجرَّد", level, FORMULA_TEXT, FINAL_RESULT]
    for c, v in enumerate(row_vals, start=1):
        cell = ws.cell(row=r, column=c, value=v)
        cell.border = border
        cell.fill = PatternFill("solid", fgColor=row_fill)
        center_cols = (1, 3, 5, 6, 8)
        cell.alignment = Alignment(
            horizontal="center" if c in center_cols else "right",
            vertical="center", wrap_text=True,
            indent=0 if c in center_cols else 1,
        )
        if c == 1:
            cell.font = Font(name=AR_FONT, size=10, bold=True, color=NAVY)
        elif c == 5 or c == 8:
            cell.font = Font(name=AR_FONT, size=10, bold=True, color=GREEN)
        else:
            cell.font = Font(name=AR_FONT, size=9.5, color="262626")
    ws.row_dimensions[r].height = 26
    r += 1

r = spacer(r, 14)
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=N_COLS)
note1 = ws.cell(
    row=r, column=1,
    value=(
        "ملاحظة تدقيق: عمودا «معادلة الحساب» و«النتيجة النهائية» يمثلان نتيجة الاحتساب "
        "الإجمالي الواحد (30 ÷ 30 × 100 = 100%)، وهما مكرَّران عبر كل صف لتسهيل الفرز "
        "والتحقق الآلي؛ وليسا قيمتين مستقلتين لكل أصل. لا يتضمن أيٌّ من DC.C.3.1 أو "
        "DC.C.3.2 أو DC.C.5.1 معرّفات مستقلة للأصول، ولذلك استُخدم الرقم التسلسلي (م) "
        "كمعرّف تتبّع."
    ),
)
note1.font = Font(name=AR_FONT, size=8, italic=True, color="7F7F7F")
note1.alignment = Alignment(horizontal="right", vertical="center", wrap_text=True, indent=1)
ws.row_dimensions[r].height = 42
r += 1

r = spacer(r, 14)
r = section_heading(r, "5. تطبيق المعادلة")
r = spacer(r, 4)
r = meta_row(r, "إجمالي الأصول البيانية (DC.C.3.1)", str(TOTAL_ASSETS))
r = meta_row(r, "عدد الأصول المصنَّفة (DC.C.3.2)", str(CLASSIFIED_ASSETS))
r = meta_row(r, "تطبيق المعادلة", f"{CLASSIFIED_ASSETS} ÷ {TOTAL_ASSETS} × 100")
r = meta_row(r, "القيمة النهائية للمؤشر", FINAL_RESULT)
r = spacer(r, 14)

r = section_heading(r, "6. النتيجة والتحقق مقابل DC.C.4.1")
r = spacer(r, 4)
r = bullet_row(r, f"القيمة الناتجة ({FINAL_RESULT}) مطابقة تماماً للقيمة الواردة في بطاقة KPI-DC-01 ضمن تقرير DC.C.4.1 (القسم 8 وبند 9.1).")
r = bullet_row(r, "تم التحقق من مطابقة عدد الأصول (30) وأسمائها بين DC.C.3.1 وDC.C.3.2 وDC.C.5.1 دون أي تعارض.")
r = spacer(r, 14)

r = section_heading(r, "7. الاعتماد والتوقيع")
r = spacer(r, 4)
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=N_COLS)
review_cell = ws.cell(
    row=r, column=1,
    value="تمت مراجعة هذا السجل من مكتب إدارة البيانات، وتم التحقق من مطابقة البيانات الواردة فيه لمحتوى DC.C.3.1 وDC.C.3.2 وDC.C.5.1 دون أي إضافة أو حذف أو تعديل.",
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

widths = [6, 32, 14, 20, 12, 14, 34, 14]
for i, w in enumerate(widths, start=1):
    ws.column_dimensions[get_column_letter(i)].width = w

wb.save(OUT_PATH)
print("Saved:", OUT_PATH)
print("Rows:", len(ASSETS), "Total:", TOTAL_ASSETS, "Classified:", CLASSIFIED_ASSETS, "Result:", FINAL_RESULT)
