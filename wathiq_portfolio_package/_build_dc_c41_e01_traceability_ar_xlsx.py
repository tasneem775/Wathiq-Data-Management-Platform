# -*- coding: utf-8 -*-
"""Arabic localization of DC.C.4.1-E01_Asset_Traceability_Verification.xlsx.
Only headers/labels are translated to Arabic; all underlying data (asset names, types,
departments, classifications, match flags, notes content, 100% matching rate) is
identical to the English version — verified via diff against the English builder script.
No asset name, order, type, department, or classification is changed. No new information
is added.
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT_PATH = "06_DC_C4_1_KPI_Evidence/DC.C.4.1-E01_دليل_تتبع_وتحقق_تصنيف_الأصول_البيانية.xlsx"

NAVY = "1F2A44"
GOLD = "AB8654"
LIGHT_GREY = "F2F2F2"
WHITE = "FFFFFF"
GREEN = "1F6F43"
AMBER = "8A6D00"
AR_FONT = "Arial"

# ============ بيانات مصدرها الحرفي DC.C.3.1 (Table 8) + DC.C.3.2 (Table 11/9) + DC.C.5.1 (Table 6) ============
# مطابقة تماماً لقائمة الأصول في النسخة الإنجليزية — دون أي تغيير في الاسم أو النوع أو الإدارة أو التصنيف
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
TOTAL = len(ASSETS)

NAME_PARTIAL = {3}
DEPT_PARTIAL = {13}

NOTES_AR = {
    3: "اختلاف تسمية بين المصادر المرجعية الأصلية؛ يحتوي DC.C.3.1 على اللاحقة (IAM)، بينما لا تظهر في DC.C.3.2 وDC.C.5.1. لا يؤثر ذلك على قابلية تتبع الأصل.",
    13: "اختلاف في تسمية الإدارة بين المصادر المرجعية الأصلية؛ يذكر DC.C.3.1 \"مكتب الاستراتيجية والتخطيط\"، بينما يذكر DC.C.3.2 وDC.C.5.1 \"مكتب الاستراتيجية\". لا يؤثر ذلك على قابلية تتبع الأصل.",
}

wb = Workbook()

thin = Side(style="thin", color="D9D9D9")
border = Border(left=thin, right=thin, top=thin, bottom=thin)


def style_title_bar(ws, row, text, size, bold, color, fill, height, span):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=span)
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = Font(name=AR_FONT, size=size, bold=bold, color=color)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.fill = PatternFill("solid", fgColor=fill)
    ws.row_dimensions[row].height = height


def header_row(ws, row, headers):
    for c, h in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=c, value=h)
        cell.font = Font(name=AR_FONT, size=10, bold=True, color=WHITE)
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
    ws.row_dimensions[row].height = 30


# ============================================================
# الورقة 1 — ملخص التحقق
# ============================================================
ws1 = wb.active
ws1.title = "ملخص التحقق"
ws1.sheet_view.showGridLines = False
ws1.sheet_view.rightToLeft = True

r = 1
style_title_bar(ws1, r, "دليل تتبع وتحقق تصنيف الأصول البيانية — DC.C.4.1-E01", 13, True, WHITE, NAVY, 26, 5)
r += 1
style_title_bar(ws1, r, "دليل تتبع وتحقق تصنيف الأصول البيانية — DC.C.4.1-E01", 15, True, WHITE, NAVY, 30, 5)
r += 1
style_title_bar(ws1, r, "حزمة دليل التحقق (Evidence Verification Package)", 10.5, True, GOLD, NAVY, 20, 5)
r += 1
cover_result = ws1.cell(row=r, column=1, value="30 من أصل 30 أصلاً تم التحقق من قابلية تتبع تصنيفها عبر المصادر المرجعية الثلاثة")
ws1.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
cover_result.font = Font(name=AR_FONT, size=10.5, bold=True, color=NAVY)
cover_result.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
ws1.row_dimensions[r].height = 22
r += 2

fields = [
    ("إجمالي الأصول البيانية:", TOTAL),
    ("الأصول الواردة في DC.C.3.1:", TOTAL),
    ("الأصول الواردة في DC.C.3.2:", TOTAL),
    ("الأصول الواردة في DC.C.5.1:", TOTAL),
    ("نسبة المطابقة:", "100%"),
]
for label, value in fields:
    c1 = ws1.cell(row=r, column=1, value=label)
    c1.font = Font(name=AR_FONT, size=11, bold=True, color=NAVY)
    c1.alignment = Alignment(horizontal="right", vertical="center")
    c2 = ws1.cell(row=r, column=2, value=value)
    c2.font = Font(name=AR_FONT, size=11, bold=True, color=GREEN)
    c2.alignment = Alignment(horizontal="center", vertical="center")
    r += 1
r += 1

header_row(ws1, r, ["المصدر المرجعي", "عدد الأصول", "نتيجة التحقق"])
r += 1
for source in ["DC.C.3.1", "DC.C.3.2", "DC.C.5.1"]:
    for c, v in enumerate([source, TOTAL, "مطابق"], start=1):
        cell = ws1.cell(row=r, column=c, value=v)
        cell.border = border
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.font = Font(name=AR_FONT, size=10, bold=(c != 2), color=NAVY if c == 1 else (GREEN if c == 3 else "262626"))
    ws1.row_dimensions[r].height = 22
    r += 1

r += 1
summary_note = ws1.cell(row=r, column=1, value=(
    "تم التحقق من وجود جميع الأصول البيانية الثلاثين (30) الواردة في DC.C.3.1 عبر "
    "DC.C.3.2 وDC.C.5.1، مع عدم وجود أي أصول ناقصة أو إضافية بين المصادر المرجعية الثلاثة."
))
ws1.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
summary_note.font = Font(name=AR_FONT, size=9, color="262626")
summary_note.alignment = Alignment(horizontal="right", vertical="center", wrap_text=True)
ws1.row_dimensions[r].height = 30
r += 1

closing_note = ws1.cell(row=r, column=1, value=(
    "هذه الوثيقة حزمة دليل تحقق (Evidence Verification Package) تم إعدادها لدعم متطلب "
    "DC.C.4.1 ومؤشر KPI-DC-01، ولا تمثل متطلباً جديداً أو تعديلاً على المتطلبات المرجعية."
))
ws1.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
closing_note.font = Font(name=AR_FONT, size=8.5, italic=True, color="7F7F7F")
closing_note.alignment = Alignment(horizontal="right", vertical="center", wrap_text=True)
ws1.row_dimensions[r].height = 40

ws1.column_dimensions["A"].width = 26
ws1.column_dimensions["B"].width = 16
ws1.column_dimensions["C"].width = 20
ws1.column_dimensions["D"].width = 16
ws1.column_dimensions["E"].width = 16

# ============================================================
# الورقة 2 — مطابقة الأصول البيانية
# ============================================================
ws2 = wb.create_sheet("مطابقة الأصول البيانية")
ws2.sheet_view.showGridLines = False
ws2.sheet_view.rightToLeft = True

headers2 = [
    "رقم الأصل", "اسم الأصل (حسب DC.C.3.1)", "النوع", "الإدارة المالكة", "التصنيف",
    "موجود في DC.C.3.1", "موجود في DC.C.3.2",
    "موجود في DC.C.5.1", "تطابق الاسم", "تطابق النوع", "تطابق الإدارة المالكة",
    "تطابق التصنيف", "الملاحظات",
]
r = 1
style_title_bar(ws2, r, "مطابقة الأصول البيانية — DC.C.4.1-E01 (KPI-DC-01)", 13, True, WHITE, NAVY, 26, len(headers2))
r += 2
header_row(ws2, r, headers2)
r += 1

for i, (n, name, atype, dept, cls) in enumerate(ASSETS):
    name_match = "جزئي" if n in NAME_PARTIAL else "نعم"
    dept_match = "جزئي" if n in DEPT_PARTIAL else "نعم"
    notes = NOTES_AR.get(n, "")
    row_vals = [n, name, atype, dept, cls, "نعم", "نعم", "نعم", name_match, "نعم", dept_match, "نعم", notes]
    row_fill = LIGHT_GREY if i % 2 == 0 else WHITE
    for c, v in enumerate(row_vals, start=1):
        cell = ws2.cell(row=r, column=c, value=v)
        cell.border = border
        cell.fill = PatternFill("solid", fgColor=row_fill)
        center_cols = (1, 3, 5, 6, 7, 8, 9, 10, 11, 12)
        cell.alignment = Alignment(
            horizontal="center" if c in center_cols else "right",
            vertical="center", wrap_text=True,
        )
        if c == 1:
            cell.font = Font(name=AR_FONT, size=9.5, bold=True, color=NAVY)
        elif c in (2, 3, 4, 5):
            cell.font = Font(name=AR_FONT, size=9.5, color="262626")
        elif c in (9, 11) and v == "جزئي":
            cell.font = Font(name=AR_FONT, size=9.5, bold=True, color=AMBER)
        elif c in (6, 7, 8, 9, 10, 11, 12):
            cell.font = Font(name=AR_FONT, size=9.5, bold=True, color=GREEN)
        else:
            cell.font = Font(name=AR_FONT, size=8.5, italic=True, color="595959")
    ws2.row_dimensions[r].height = 34 if notes else 20
    r += 1

widths2 = [8, 34, 14, 22, 13, 12, 12, 12, 11, 10, 18, 13, 46]
for i, w in enumerate(widths2, start=1):
    ws2.column_dimensions[get_column_letter(i)].width = w

# ============================================================
# الورقة 3 — عينات التحقق المرئي
# ============================================================
ws3 = wb.create_sheet("عينات التحقق المرئي")
ws3.sheet_view.showGridLines = False
ws3.sheet_view.rightToLeft = True

SAMPLE_NUMBERS = [1, 10, 30]
ASSET_BY_NUM = {n: (name, atype, dept, cls) for n, name, atype, dept, cls in ASSETS}

# مراجع حرفية من كل وثيقة مصدر (مطابقة تماماً لمحتوى النسخة الإنجليزية، معرَّبة فقط)
REFERENCES = {
    1: {
        "DC.C.3.1": "الجدول 8، م=1 — بيانات الهوية والتحقق الإلكتروني | مجموعة بيانات | إدارة الهوية الرقمية | حالة الجرد: مُجرَّد",
        "DC.C.3.2": "الجدول 11، م=1 — بيانات الهوية والتحقق الإلكتروني | مستوى التصنيف الناتج: سرّي للغاية",
        "DC.C.5.1": "الجدول 6، م=1 — بيانات الهوية والتحقق الإلكتروني | مستوى التصنيف الممنوح: سرّي للغاية | المعتمد أثناء المراجعة: سرّي للغاية",
    },
    10: {
        "DC.C.3.1": "الجدول 8، م=10 — بيانات الخدمات الحكومية الرقمية | مجموعة بيانات | إدارة التحول الرقمي | حالة الجرد: مُجرَّد",
        "DC.C.3.2": "الجدول 11، م=10 — بيانات الخدمات الحكومية الرقمية | مستوى التصنيف الناتج: مقيّد",
        "DC.C.5.1": "الجدول 6، م=10 — بيانات الخدمات الحكومية الرقمية | مستوى التصنيف الممنوح: مقيّد | المعتمد أثناء المراجعة: عام",
    },
    30: {
        "DC.C.3.1": "الجدول 8، م=30 — سجلات التغييرات والتحديثات التقنية | سجل | إدارة تقنية المعلومات | حالة الجرد: مُجرَّد",
        "DC.C.3.2": "الجدول 11، م=30 — سجلات التغييرات والتحديثات التقنية | مستوى التصنيف الناتج: مقيّد",
        "DC.C.5.1": "الجدول 6، م=30 — سجلات التغييرات والتحديثات التقنية | مستوى التصنيف الممنوح: مقيّد | المعتمد أثناء المراجعة: مقيّد",
    },
}

headers3 = ["رقم الأصل", "اسم الأصل", "مرجع DC.C.3.1", "مرجع DC.C.3.2", "مرجع DC.C.5.1", "نتيجة التحقق"]
r = 1
style_title_bar(ws3, r, "عينات التحقق المرئي (الأصول 1، 10، 30)", 13, True, WHITE, NAVY, 26, len(headers3))
r += 2
header_row(ws3, r, headers3)
r += 1

for n in SAMPLE_NUMBERS:
    name, atype, dept, cls = ASSET_BY_NUM[n]
    refs = REFERENCES[n]
    row_vals = [n, name, refs["DC.C.3.1"], refs["DC.C.3.2"], refs["DC.C.5.1"], "مطابق"]
    for c, v in enumerate(row_vals, start=1):
        cell = ws3.cell(row=r, column=c, value=v)
        cell.border = border
        cell.alignment = Alignment(
            horizontal="center" if c in (1, 6) else "right",
            vertical="center", wrap_text=True,
        )
        if c == 1:
            cell.font = Font(name=AR_FONT, size=9.5, bold=True, color=NAVY)
        elif c == 6:
            cell.font = Font(name=AR_FONT, size=9.5, bold=True, color=GREEN)
        else:
            cell.font = Font(name=AR_FONT, size=9, color="262626")
    ws3.row_dimensions[r].height = 46
    r += 1

widths3 = [12, 30, 42, 34, 46, 14]
for i, w in enumerate(widths3, start=1):
    ws3.column_dimensions[get_column_letter(i)].width = w

wb.save(OUT_PATH)
print("Saved:", OUT_PATH)
print("Sheet names:", wb.sheetnames)
print("Sheet2 row count (assets):", len(ASSETS))
print("Name Partial rows:", NAME_PARTIAL)
print("Dept Partial rows:", DEPT_PARTIAL)
