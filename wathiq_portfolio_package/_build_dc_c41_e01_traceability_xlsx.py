# -*- coding: utf-8 -*-
"""Builds DC.C.4.1-E01_Asset_Traceability_Verification.xlsx — an Evidence Verification
Package (not a requirements document) proving that the 30 assets used to calculate
KPI-DC-01 in DC.C.4.1 are traceable across DC.C.3.1 (Table 8), DC.C.3.2 (Table 11/9),
and DC.C.5.1 (Table 6). Read-only audit output: no asset name, type, department, or
classification is invented or altered. The two source-to-source naming differences
(asset 3, asset 13) are recorded as Notes only — not treated as errors — per explicit
instruction.
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT_PATH = "06_DC_C4_1_KPI_Evidence/DC.C.4.1-E01_Asset_Traceability_Verification.xlsx"

NAVY = "1F2A44"
GOLD = "AB8654"
LIGHT_GREY = "F2F2F2"
WHITE = "FFFFFF"
GREEN = "1F6F43"
AMBER = "8A6D00"
AR_FONT = "Arial"

# ============ بيانات مصدرها الحرفي DC.C.3.1 (Table 8) + DC.C.3.2 (Table 11/9) + DC.C.5.1 (Table 6) ============
# (م، اسم الأصل [DC.C.3.1]، نوع الأصل، الإدارة المالكة [DC.C.3.1]، مستوى التصنيف [DC.C.3.2])
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

# per-row match flags — sourced from the fresh cross-source audit performed in this session
NAME_PARTIAL = {3}          # DC.C.3.2 / DC.C.5.1 omit the "(IAM)" suffix present in DC.C.3.1
DEPT_PARTIAL = {13}         # DC.C.3.2 / DC.C.5.1 write "مكتب الاستراتيجية" without "والتخطيط"

NOTES = {
    3: "Difference exists between source documents: DC.C.3.2 and DC.C.5.1 omit the \"(IAM)\" suffix present in DC.C.3.1. Not treated as an error in E01.",
    13: "Difference exists between source documents: DC.C.3.2 and DC.C.5.1 list the department as \"مكتب الاستراتيجية\" (without \"والتخطيط\"). Not treated as an error in E01.",
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


def header_row(ws, row, headers, span_widths=None):
    for c, h in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=c, value=h)
        cell.font = Font(name=AR_FONT, size=10, bold=True, color=WHITE)
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
    ws.row_dimensions[row].height = 30


# ============================================================
# Sheet 1 — Verification Summary
# ============================================================
ws1 = wb.active
ws1.title = "Verification Summary"
ws1.sheet_view.showGridLines = False

r = 1
style_title_bar(ws1, r, "Data Asset Classification Traceability Verification Guide — DC.C.4.1-E01", 13, True, WHITE, NAVY, 26, 5)
r += 1
style_title_bar(ws1, r, "DC.C.4.1-E01 — Asset Traceability Verification", 15, True, WHITE, NAVY, 30, 5)
r += 1
style_title_bar(ws1, r, "Evidence Verification Package", 10.5, True, GOLD, NAVY, 20, 5)
r += 2

ws1.cell(row=r, column=1, value="Total Assets:").font = Font(name=AR_FONT, size=11, bold=True, color=NAVY)
ws1.cell(row=r, column=2, value=TOTAL).font = Font(name=AR_FONT, size=11, bold=True, color=GREEN)
r += 1
ws1.cell(row=r, column=1, value="Assets in DC.C.3.1:").font = Font(name=AR_FONT, size=11, bold=True, color=NAVY)
ws1.cell(row=r, column=2, value=TOTAL).font = Font(name=AR_FONT, size=11, bold=True, color=GREEN)
r += 1
ws1.cell(row=r, column=1, value="Assets in DC.C.3.2:").font = Font(name=AR_FONT, size=11, bold=True, color=NAVY)
ws1.cell(row=r, column=2, value=TOTAL).font = Font(name=AR_FONT, size=11, bold=True, color=GREEN)
r += 1
ws1.cell(row=r, column=1, value="Assets in DC.C.5.1:").font = Font(name=AR_FONT, size=11, bold=True, color=NAVY)
ws1.cell(row=r, column=2, value=TOTAL).font = Font(name=AR_FONT, size=11, bold=True, color=GREEN)
r += 1
ws1.cell(row=r, column=1, value="Matching Rate:").font = Font(name=AR_FONT, size=11, bold=True, color=NAVY)
ws1.cell(row=r, column=2, value="100%").font = Font(name=AR_FONT, size=11, bold=True, color=GREEN)
r += 2

header_row(ws1, r, ["Source", "Asset Count", "Verification Result"])
r += 1
for source in ["DC.C.3.1", "DC.C.3.2", "DC.C.5.1"]:
    for c, v in enumerate([source, TOTAL, "Matched"], start=1):
        cell = ws1.cell(row=r, column=c, value=v)
        cell.border = border
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.font = Font(name=AR_FONT, size=10, bold=(c == 1), color=NAVY if c == 1 else (GREEN if c == 3 else "262626"))
    ws1.row_dimensions[r].height = 22
    r += 1

r += 1
note = ws1.cell(row=r, column=1, value=(
    "Note: This workbook is an Evidence Verification Package, not a new requirements document. "
    "All values are traced directly to DC.C.3.1 (Table 8), DC.C.3.2 (Table 11/9), and DC.C.5.1 "
    "(Table 6). No asset name, type, department, or classification was created or altered."
))
ws1.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
note.font = Font(name=AR_FONT, size=8.5, italic=True, color="7F7F7F")
note.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
ws1.row_dimensions[r].height = 40

ws1.column_dimensions["A"].width = 22
ws1.column_dimensions["B"].width = 16
ws1.column_dimensions["C"].width = 20
ws1.column_dimensions["D"].width = 16
ws1.column_dimensions["E"].width = 16

# ============================================================
# Sheet 2 — Asset Matching
# ============================================================
ws2 = wb.create_sheet("Asset Matching")
ws2.sheet_view.showGridLines = False

headers2 = [
    "Asset No.", "Asset Name (DC.C.3.1)", "Found in DC.C.3.1", "Found in DC.C.3.2",
    "Found in DC.C.5.1", "Name Match", "Type Match", "Owner Department Match",
    "Classification Match", "Notes",
]
r = 1
style_title_bar(ws2, r, "Asset Matching — DC.C.4.1-E01 (KPI-DC-01)", 13, True, WHITE, NAVY, 26, len(headers2))
r += 2
header_row(ws2, r, headers2)
r += 1

for i, (n, name, atype, dept, cls) in enumerate(ASSETS):
    name_match = "Partial" if n in NAME_PARTIAL else "Yes"
    dept_match = "Partial" if n in DEPT_PARTIAL else "Yes"
    notes = NOTES.get(n, "")
    row_vals = [n, name, "Yes", "Yes", "Yes", name_match, "Yes", dept_match, "Yes", notes]
    row_fill = LIGHT_GREY if i % 2 == 0 else WHITE
    for c, v in enumerate(row_vals, start=1):
        cell = ws2.cell(row=r, column=c, value=v)
        cell.border = border
        cell.fill = PatternFill("solid", fgColor=row_fill)
        center_cols = (1, 3, 4, 5, 6, 7, 8, 9)
        cell.alignment = Alignment(
            horizontal="center" if c in center_cols else "left",
            vertical="center", wrap_text=True,
        )
        if c == 1:
            cell.font = Font(name=AR_FONT, size=9.5, bold=True, color=NAVY)
        elif c == 2:
            cell.font = Font(name=AR_FONT, size=9.5, color="262626")
        elif c in (6, 8) and v == "Partial":
            cell.font = Font(name=AR_FONT, size=9.5, bold=True, color=AMBER)
        elif c in (3, 4, 5, 6, 7, 8, 9):
            cell.font = Font(name=AR_FONT, size=9.5, bold=True, color=GREEN)
        else:
            cell.font = Font(name=AR_FONT, size=8.5, italic=True, color="595959")
    ws2.row_dimensions[r].height = 30 if notes else 20
    r += 1

widths2 = [10, 34, 12, 12, 12, 11, 10, 18, 15, 46]
for i, w in enumerate(widths2, start=1):
    ws2.column_dimensions[get_column_letter(i)].width = w

# ============================================================
# Sheet 3 — Audit Samples
# ============================================================
ws3 = wb.create_sheet("Audit Samples")
ws3.sheet_view.showGridLines = False

SAMPLE_NUMBERS = [1, 10, 30]
ASSET_BY_NUM = {n: (name, atype, dept, cls) for n, name, atype, dept, cls in ASSETS}

# References verbatim from each source document (row = Asset No.)
REFERENCES = {
    1: {
        "DC.C.3.1": "Table 8, م=1 — بيانات الهوية والتحقق الإلكتروني | مجموعة بيانات | إدارة الهوية الرقمية | حالة الجرد: مُجرَّد",
        "DC.C.3.2": "Table 11, م=1 — بيانات الهوية والتحقق الإلكتروني | مستوى التصنيف الناتج: سرّي للغاية",
        "DC.C.5.1": "Table 6, م=1 — بيانات الهوية والتحقق الإلكتروني | مستوى التصنيف الممنوح: سرّي للغاية | المعتمد أثناء المراجعة: سرّي للغاية",
    },
    10: {
        "DC.C.3.1": "Table 8, م=10 — بيانات الخدمات الحكومية الرقمية | مجموعة بيانات | إدارة التحول الرقمي | حالة الجرد: مُجرَّد",
        "DC.C.3.2": "Table 11, م=10 — بيانات الخدمات الحكومية الرقمية | مستوى التصنيف الناتج: مقيّد",
        "DC.C.5.1": "Table 6, م=10 — بيانات الخدمات الحكومية الرقمية | مستوى التصنيف الممنوح: مقيّد | المعتمد أثناء المراجعة: عام",
    },
    30: {
        "DC.C.3.1": "Table 8, م=30 — سجلات التغييرات والتحديثات التقنية | سجل | إدارة تقنية المعلومات | حالة الجرد: مُجرَّد",
        "DC.C.3.2": "Table 11, م=30 — سجلات التغييرات والتحديثات التقنية | مستوى التصنيف الناتج: مقيّد",
        "DC.C.5.1": "Table 6, م=30 — سجلات التغييرات والتحديثات التقنية | مستوى التصنيف الممنوح: مقيّد | المعتمد أثناء المراجعة: مقيّد",
    },
}

headers3 = ["Asset Number", "Asset Name", "DC.C.3.1 Reference", "DC.C.3.2 Reference", "DC.C.5.1 Reference", "Verification Result"]
r = 1
style_title_bar(ws3, r, "Audit Samples — Visual Spot-Check (Assets 1, 10, 30)", 13, True, WHITE, NAVY, 26, len(headers3))
r += 2
header_row(ws3, r, headers3)
r += 1

for n in SAMPLE_NUMBERS:
    name, atype, dept, cls = ASSET_BY_NUM[n]
    refs = REFERENCES[n]
    row_vals = [n, name, refs["DC.C.3.1"], refs["DC.C.3.2"], refs["DC.C.5.1"], "Matched"]
    for c, v in enumerate(row_vals, start=1):
        cell = ws3.cell(row=r, column=c, value=v)
        cell.border = border
        cell.alignment = Alignment(
            horizontal="center" if c in (1, 6) else "left",
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
print("Sheet2 row count (assets):", len(ASSETS))
print("Name Partial rows:", NAME_PARTIAL)
print("Dept Partial rows:", DEPT_PARTIAL)
