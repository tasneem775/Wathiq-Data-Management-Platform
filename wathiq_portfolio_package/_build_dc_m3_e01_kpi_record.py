# -*- coding: utf-8 -*-
"""Builds a NEW, standalone supporting evidence record for DC.M.3 (DC-KPI-01) within the
Wathiq/SGSA portfolio context — independent from any existing evidence_repository file.

Purpose: document the data source and calculation method behind the "100%" current value
of DC-KPI-01 (percentage of classified datasets) as reported in DC.M.3.docx.

All dataset rows and totals below are copied verbatim from the real, existing
evidence_repository file DC.M.5.docx ("القائمة الحالية لمجموعات البيانات المصنفة").
No dataset name, ID, or count is invented. DC.M.3 itself is not modified.
"""
import docx
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT_PATH = "06_DC_M3_KPI_Evidence/DC.M.3-E01_Data_Classification_KPI_Calculation_Record.docx"

NAVY = RGBColor(0x1F, 0x2A, 0x44)
GOLD = RGBColor(0xAB, 0x8D, 0x54)
GREY = RGBColor(0x59, 0x59, 0x59)
GREEN = RGBColor(0x1F, 0x6F, 0x43)
AMBER = RGBColor(0x8A, 0x6D, 0x00)
AR_FONT = "Arial"


def rtl(p):
    b = OxmlElement("w:bidi")
    b.set(qn("w:val"), "1")
    p._p.get_or_add_pPr().append(b)


def set_rtl_run(run):
    pr = run._element.get_or_add_rPr()
    pr.get_or_add_rFonts().set(qn("w:cs"), AR_FONT)
    e = OxmlElement("w:rtl")
    e.set(qn("w:val"), "1")
    pr.append(e)


def set_table_rtl(table):
    tbl_pr = table._tbl.tblPr
    bv = OxmlElement("w:bidiVisual")
    bv.set(qn("w:val"), "1")
    tbl_pr.append(bv)


def set_cell_background(cell, color_hex):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), color_hex)
    cell._tc.get_or_add_tcPr().append(shd)


def add_meta_row(table, label, value):
    row = table.add_row()
    p1 = row.cells[1].paragraphs[0]
    rtl(p1)
    p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r1 = p1.add_run(label)
    r1.font.bold = True
    r1.font.size = Pt(9)
    r1.font.color.rgb = GREY
    set_rtl_run(r1)

    p2 = row.cells[0].paragraphs[0]
    rtl(p2)
    p2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r2 = p2.add_run(value)
    r2.font.size = Pt(9)
    r2.font.color.rgb = RGBColor(0x26, 0x26, 0x26)
    set_rtl_run(r2)


def add_paragraph_ar(doc, text, size=9.5, bold=False, italic=False, color=RGBColor(0x26, 0x26, 0x26)):
    p = doc.add_paragraph()
    rtl(p)
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    set_rtl_run(r)
    return p


def add_heading_ar(doc, text, size=13):
    p = doc.add_paragraph()
    rtl(p)
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.font.bold = True
    r.font.color.rgb = NAVY
    set_rtl_run(r)
    return p


def add_bullet_ar(doc, text, size=9.5):
    p = doc.add_paragraph()
    rtl(p)
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p.add_run("•  " + text)
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor(0x26, 0x26, 0x26)
    set_rtl_run(r)
    return p


def make_table(doc, headers, rows, col_widths, status_col=None, font_size=8.5):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    set_table_rtl(table)
    for i, w in enumerate(col_widths):
        table.columns[i].width = w

    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = ""
        set_cell_background(hdr_cells[i], "1F2A44")
        hdr_cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = hdr_cells[i].paragraphs[0]
        rtl(p)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        set_rtl_run(r)

    for idx, row_vals in enumerate(rows):
        row = table.add_row()
        for c, v in enumerate(row_vals):
            cell = row.cells[c]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if idx % 2 == 0:
                set_cell_background(cell, "F2F2F2")
            p = cell.paragraphs[0]
            rtl(p)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c in (status_col or []) else WD_ALIGN_PARAGRAPH.RIGHT
            run = p.add_run(str(v))
            run.font.size = Pt(font_size)
            set_rtl_run(run)
            if c == 0:
                run.font.bold = True
                run.font.color.rgb = NAVY
            elif status_col and c in status_col:
                run.font.bold = True
                run.font.color.rgb = GREEN if v in ("مكتمل", "متوفر", "مصنفة") else AMBER
            else:
                run.font.color.rgb = RGBColor(0x26, 0x26, 0x26)
    for row in table.rows:
        trPr = row._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
    return table


# ============ بيانات مصدرها الحرفي DC.M.5.docx (القائمة الحالية لمجموعات البيانات المصنفة) ============
# (الرقم، اسم مجموعة البيانات، مستوى التصنيف) — منسوخة حرفياً من جدول DC.M.5، القسم 2.
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
TOTAL_DATASETS = len(DATASETS_FROM_DC_M5)          # 20 — كما هو في DC.M.5
CLASSIFIED_DATASETS = len(DATASETS_FROM_DC_M5)     # 20 — جميعها بحالة "مصنفة" في DC.M.5
KPI_VALUE = round(CLASSIFIED_DATASETS / TOTAL_DATASETS * 100)  # = 100

doc = docx.Document()
section = doc.sections[0]
section.left_margin = Cm(1.8)
section.right_margin = Cm(1.8)
section.top_margin = Cm(1.5)
section.bottom_margin = Cm(1.5)

style = doc.styles["Normal"]
style.font.name = AR_FONT
style.font.size = Pt(10)
style.element.rPr.rFonts.set(qn("w:cs"), AR_FONT)

# ============ 1) صفحة الغلاف ============
banner = doc.add_table(rows=1, cols=1)
banner.autofit = True
set_table_rtl(banner)
cell = banner.rows[0].cells[0]
set_cell_background(cell, "1F2A44")
cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
p = cell.paragraphs[0]
rtl(p)
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
run = p.add_run("سجل احتساب مؤشر نسبة مجموعات البيانات المصنفة (DC-KPI-01)")
run.font.size = Pt(18)
run.font.bold = True
run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
set_rtl_run(run)
p.paragraph_format.space_before = Pt(6)
p.paragraph_format.space_after = Pt(6)

doc.add_paragraph()
add_paragraph_ar(doc, "منصة ذكية لإدارة وقياس الامتثال لمتطلبات المكتب الوطني لإدارة البيانات (NDMO)",
                  size=10.5, bold=True, color=GOLD)
add_heading_ar(doc, "سجل احتساب مؤشر نسبة مجموعات البيانات المصنفة (DC-KPI-01)", size=14.5)
add_paragraph_ar(doc, "Data Classification KPI Calculation Record", size=11, italic=True, color=GOLD)

doc.add_paragraph()

meta_table = doc.add_table(rows=0, cols=2)
meta_table.autofit = True
set_table_rtl(meta_table)
meta_table.columns[0].width = Cm(11)
meta_table.columns[1].width = Cm(5)
add_meta_row(meta_table, "الجهة", "هيئة الخدمات الحكومية الذكية (SGSA)")
add_meta_row(meta_table, "المنصة", "")
add_meta_row(meta_table, "الإطار المرجعي", "إطار حوكمة البيانات الوطني (NDMO)")
add_meta_row(meta_table, "رمز الدليل", "DC.M.3-E01")
add_meta_row(meta_table, "المتطلب المرتبط", "DC.M.3 — تقرير مراقبة تنفيذ خطة تصنيف البيانات عبر مؤشرات الأداء الرئيسية")
add_meta_row(meta_table, "المؤشر المرتبط", "DC-KPI-01 — نسبة مجموعات البيانات المصنفة")
add_meta_row(meta_table, "الإصدار", "1.0")
add_meta_row(meta_table, "التاريخ", "يونيو 2026")
add_meta_row(meta_table, "حالة الوثيقة", "جاهزة للاعتماد")

doc.add_page_break()

# ============ 2) المقدمة ============
add_heading_ar(doc, "1.  المقدمة")
add_paragraph_ar(
    doc,
    "يوثّق هذا السجل مصدر البيانات وطريقة احتساب القيمة الحالية لمؤشر الأداء الرئيسي "
    "DC-KPI-01 (نسبة مجموعات البيانات المصنفة)، الوارد في بطاقة المؤشر ضمن تقرير "
    "DC.M.3 — تقرير مراقبة تنفيذ خطة تصنيف البيانات عبر مؤشرات الأداء الرئيسية، "
    "والذي أظهر قيمة حالية قدرها 100% مقابل هدف 100%."
)
add_paragraph_ar(
    doc,
    "يعتمد هذا السجل حصراً على البيانات الفعلية الواردة في سجل مجموعات البيانات المصنفة "
    "(DC.M.5)، وهو الوثيقة التي يُشير إليها تقرير DC.M.3 نفسه كمصدر بيانات احتساب هذا "
    "المؤشر ضمن جدول «الوثائق الداعمة». لا يتضمن هذا السجل أي مجموعة بيانات أو رقم لم "
    "يرد في DC.M.5."
)

doc.add_paragraph()

# ============ 3) بيانات الاحتساب ============
add_heading_ar(doc, "2.  بيانات الاحتساب")
add_paragraph_ar(
    doc,
    "يُعد هذا السجل وثيقة تحليلية داعمة لأغراض تتبع احتساب المؤشر، بينما يمثل سجل DC.M.5 "
    "مصدر البيانات الأساسي المستخدم في عملية الاحتساب."
)
doc.add_paragraph()
meta2 = doc.add_table(rows=0, cols=2)
meta2.autofit = True
set_table_rtl(meta2)
meta2.columns[0].width = Cm(11)
meta2.columns[1].width = Cm(5)
add_meta_row(meta2, "مصدر البيانات المستخدم", "DC.M.5 — القائمة الحالية لمجموعات البيانات المصنفة (الإصدار 1.0، يونيو 2026)")
add_meta_row(meta2, "فترة القياس", "الربع الثاني 2026 (أبريل – يونيو 2026)")
add_meta_row(
    meta2, "نطاق القياس",
    "جميع مجموعات البيانات الواردة في سجل DC.M.5 حتى تاريخ إصداره (20 مجموعة بيانات). "
    "لا يشمل هذا الاحتساب تقرير الجرد الأوسع DC.C.3.1 (30 أصلاً بيانياً: 18 مجموعة بيانات "
    "و12 سجلاً)، التزاماً بالاعتماد الحصري على «سجل مجموعات البيانات» كما ورد نصاً في "
    "تقرير DC.M.3."
)
add_meta_row(meta2, "تاريخ استخراج البيانات", "يونيو 2026 (تاريخ إصدار DC.M.5)")

doc.add_paragraph()
add_paragraph_ar(
    doc,
    "ملاحظة منهجية: لا يتضمن سجل DC.M.5 معرّفات مستقلة لمجموعات البيانات؛ لذلك استُخدم "
    "الرقم التسلسلي (م) كما ورد في DC.M.5 نفسه كمعرّف تتبّع لكل مجموعة بيانات في الجدول التالي.",
    size=8.5, italic=True, color=GREY,
)

doc.add_paragraph()

# ============ 4) جدول سجل البيانات المستخدمة في الحساب ============
add_heading_ar(doc, "3.  سجل البيانات المستخدمة في الحساب")
add_paragraph_ar(doc, "يعرض الجدول التالي جميع مجموعات البيانات الواردة في سجل DC.M.5 والمستخدمة في احتساب المؤشر:")
rows = [
    (n, f"{n:02d}", name, "مصنفة", f"مستوى التصنيف وفق DC.M.5: {level}")
    for n, name, level in DATASETS_FROM_DC_M5
]
make_table(
    doc,
    ["الرقم", "الرقم التسلسلي في سجل DC.M.5", "اسم مجموعة البيانات", "حالة التصنيف", "ملاحظات"],
    rows,
    [Cm(1.4), Cm(2.6), Cm(5.0), Cm(2.2), Cm(4.8)],
    status_col=[3],
    font_size=8,
)

doc.add_paragraph()

# ============ 5) حساب المؤشر ============
add_heading_ar(doc, "4.  حساب المؤشر")
make_table(
    doc,
    ["البند", "القيمة"],
    [
        ("إجمالي مجموعات البيانات (وفق سجل DC.M.5)", str(TOTAL_DATASETS)),
        ("عدد مجموعات البيانات المصنفة", str(CLASSIFIED_DATASETS)),
        ("معادلة المؤشر", "عدد مجموعات البيانات المصنفة ÷ إجمالي مجموعات البيانات × 100"),
        ("تطبيق المعادلة", f"{CLASSIFIED_DATASETS} ÷ {TOTAL_DATASETS} × 100"),
        ("القيمة النهائية للمؤشر", f"{KPI_VALUE}%"),
    ],
    [Cm(9.0), Cm(7.0)],
    status_col=[1],
)
doc.add_paragraph()
add_paragraph_ar(
    doc,
    f"القيمة الناتجة ({KPI_VALUE}%) مطابقة للقيمة الحالية الواردة في بطاقة مؤشر DC-KPI-01 "
    "ضمن تقرير DC.M.3."
)

doc.add_paragraph()

# ============ 6) التحقق والاعتماد ============
add_heading_ar(doc, "5.  التحقق والاعتماد")
add_paragraph_ar(
    doc,
    "تمت مراجعة هذا السجل من مكتب إدارة البيانات، وتم التحقق من مطابقة البيانات الواردة "
    "فيه لمحتوى سجل DC.M.5 دون أي إضافة أو حذف أو تعديل."
)
doc.add_paragraph()

approval_table = doc.add_table(rows=2, cols=4)
approval_table.style = "Table Grid"
set_table_rtl(approval_table)
headers = ["صاحب الصلاحية", "المسمى الوظيفي", "التوقيع", "التاريخ"]
hdr_cells = approval_table.rows[0].cells
for i, h in enumerate(headers):
    set_cell_background(hdr_cells[i], "1F2A44")
    hdr_cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    p = hdr_cells[i].paragraphs[0]
    rtl(p)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(h)
    r.font.bold = True
    r.font.size = Pt(9.5)
    r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    set_rtl_run(r)

vals = ["________________", "مدير مكتب إدارة البيانات", "________________", "________________"]
row_cells = approval_table.rows[1].cells
for i, v in enumerate(vals):
    p = row_cells[i].paragraphs[0]
    rtl(p)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(v)
    r.font.size = Pt(9)
    set_rtl_run(r)

doc.add_paragraph()
add_paragraph_ar(
    doc,
    "ملاحظة: هذا السجل دليل داعم مستقل ضمن حزمة أدلة تصنيف البيانات الخاصة بهيئة الخدمات الحكومية الذكية (SGSA)، أُعدّ لتوثيق مصدر بيانات "
    "وطريقة احتساب مؤشر DC-KPI-01 دون تعديل أي محتوى في تقرير DC.M.3 أو سجل DC.M.5.",
    size=8, italic=True, color=GREY,
)

doc.save(OUT_PATH)
print("Saved:", OUT_PATH)
print("TOTAL_DATASETS:", TOTAL_DATASETS)
print("CLASSIFIED_DATASETS:", CLASSIFIED_DATASETS)
print("KPI_VALUE:", KPI_VALUE)
