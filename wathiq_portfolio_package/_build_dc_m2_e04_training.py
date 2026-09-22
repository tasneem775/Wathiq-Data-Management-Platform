# -*- coding: utf-8 -*-
"""Builds a NEW, standalone evidence artifact: DC.M.2-E04 Awareness & Training Record (Word).

Independent file — does not modify DC_M2_Implementation_Status_Report.*, E01, E02, E03,
or any other file. Wathiq/SGSA identity, RTL Arabic. All numbers strictly consistent
with the main report: 3 of 4 workshops executed, 47 participants total, 90% completion,
activity status "قيد التنفيذ".
"""
import docx
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT_PATH = "05_DC_M2_Draft_Evidence/DC.M.2-E04_Data_Classification_Awareness_and_Training_Record.docx"

NAVY = RGBColor(0x1F, 0x2A, 0x44)
GOLD = RGBColor(0xAB, 0x8D, 0x54)
GREY = RGBColor(0x59, 0x59, 0x59)
GREEN = RGBColor(0x1F, 0x6F, 0x43)
AMBER = RGBColor(0x8A, 0x6D, 0x00)
AR_FONT = "Arial"

# Sum of the three executed workshops MUST equal 47 (matches the main report exactly).
WORKSHOPS = [
    (1, "ورشة التوعية الأولى: مفاهيم تصنيف البيانات", "مايو 2026", "منسوبو الهيئة", 16, "مكتمل"),
    (2, "ورشة التوعية الثانية: مستويات التصنيف ومتطلباته", "مايو 2026", "منسوبو الهيئة", 16, "مكتمل"),
    (3, "ورشة التوعية الثالثة: آليات التطبيق العملي", "يونيو 2026", "منسوبو الهيئة", 15, "مكتمل"),
    (4, "ورشة التوعية الرابعة", "لم تُحدَّد بعد", "منسوبو الهيئة", "لم تُعقد بعد", "قيد التنفيذ"),
]

MATERIALS = [
    ("عرض تدريبي", "عرض تقديمي يشرح مفاهيم ومستويات تصنيف البيانات المعتمدة."),
    ("دليل المتدرب", "دليل مرجعي مختصر لمنسوبي الهيئة يوضح خطوات تصنيف البيانات."),
    ("مادة توعوية", "مادة موجزة لرفع الوعي العام بأهمية تصنيف البيانات ومتطلباته."),
    ("ورقة عمل", "ورقة عمل تطبيقية تُستخدم أثناء الورشة لتمرين المشاركين."),
]

RESULTS = [
    "تنفيذ 3 من أصل 4 ورش مخططة.",
    "مشاركة 47 موظفاً.",
    "استمرار استكمال البرنامج التدريبي.",
    "نسبة الإنجاز الحالية 90%.",
]


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


def make_table(doc, headers, rows, col_widths, center_cols=None, status_col=None):
    center_cols = center_cols or []
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
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c in center_cols else WD_ALIGN_PARAGRAPH.RIGHT
            run = p.add_run(str(v))
            run.font.size = Pt(8.5)
            set_rtl_run(run)
            if c == 0:
                run.font.bold = True
                run.font.color.rgb = NAVY
            elif status_col is not None and c == status_col:
                run.font.bold = True
                run.font.color.rgb = GREEN if v == "مكتمل" else AMBER
            else:
                run.font.color.rgb = RGBColor(0x26, 0x26, 0x26)
    for row in table.rows:
        trPr = row._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
    return table


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

# ============ Cover / banner ============
banner = doc.add_table(rows=1, cols=1)
banner.autofit = True
set_table_rtl(banner)
cell = banner.rows[0].cells[0]
set_cell_background(cell, "1F2A44")
cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
p = cell.paragraphs[0]
rtl(p)
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
run = p.add_run("سجل ورش التوعية والتدريب الخاصة بتصنيف البيانات")
run.font.size = Pt(18)
run.font.bold = True
run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
set_rtl_run(run)
p.paragraph_format.space_before = Pt(6)
p.paragraph_format.space_after = Pt(6)

doc.add_paragraph()
add_paragraph_ar(doc, "منصة ذكية لإدارة وقياس الامتثال لمتطلبات المكتب الوطني لإدارة البيانات (NDMO)",
                  size=10.5, bold=True, color=GOLD)
add_heading_ar(doc, "سجل ورش التوعية والتدريب الخاصة بتصنيف البيانات", size=15)
add_paragraph_ar(doc, "دليل داعم — DC.M.2-E04", size=11, italic=True, color=GOLD)

doc.add_paragraph()

meta_table = doc.add_table(rows=0, cols=2)
meta_table.autofit = True
set_table_rtl(meta_table)
meta_table.columns[0].width = Cm(11)
meta_table.columns[1].width = Cm(5)
add_meta_row(meta_table, "الجهة", "هيئة الخدمات الحكومية الذكية (SGSA)")
add_meta_row(meta_table, "القسم", "مكتب إدارة البيانات")
add_meta_row(meta_table, "المنصة", "")
add_meta_row(meta_table, "الإطار المرجعي", "إطار حوكمة البيانات الوطني (NDMO)")
add_meta_row(meta_table, "رمز الدليل", "DC.M.2-E04")
add_meta_row(meta_table, "المتطلب المرتبط", "DC.M.2 — تنفيذ خطة تصنيف البيانات وخارطة الطريق")
add_meta_row(meta_table, "اسم الدليل", "سجل ورش التوعية والتدريب الخاصة بتصنيف البيانات")
add_meta_row(meta_table, "الإصدار", "1.0")
add_meta_row(meta_table, "التاريخ", "يونيو 2026")
add_meta_row(meta_table, "حالة الوثيقة", "جاهزة للمراجعة")

doc.add_page_break()

# ============ القسم الأول: ملخص النشاط ============
add_heading_ar(doc, "القسم الأول: ملخص النشاط")
add_paragraph_ar(
    doc,
    "نفَّذت الهيئة برنامج توعية داخلياً لدعم تنفيذ خطة تصنيف البيانات ورفع مستوى الوعي "
    "المؤسسي بمتطلبات التصنيف لدى منسوبيها، ضمن أنشطة المرحلة الأولى من خطة تصنيف البيانات."
)
doc.add_paragraph()

# ============ القسم الثاني: سجل ورش التوعية ============
add_heading_ar(doc, "القسم الثاني: سجل ورش التوعية")
make_table(
    doc,
    ["رقم الورشة", "اسم الورشة", "التاريخ", "الفئة المستهدفة", "عدد المشاركين", "الحالة"],
    WORKSHOPS,
    [Cm(2.0), Cm(5.2), Cm(2.4), Cm(2.8), Cm(2.4), Cm(2.2)],
    center_cols=[0, 4, 5],
    status_col=5,
)
doc.add_paragraph()

# ============ القسم الثالث: المواد التدريبية المستخدمة ============
add_heading_ar(doc, "القسم الثالث: المواد التدريبية المستخدمة")
make_table(
    doc,
    ["اسم المادة", "الوصف"],
    MATERIALS,
    [Cm(4.0), Cm(13.0)],
)
doc.add_paragraph()

# ============ القسم الرابع: النتائج ============
add_heading_ar(doc, "القسم الرابع: النتائج")
for r in RESULTS:
    add_bullet_ar(doc, r)
doc.add_paragraph()
doc.add_paragraph()

# ============ القسم الخامس: الاعتماد ============
add_heading_ar(doc, "القسم الخامس: الاعتماد")
approval_table = doc.add_table(rows=2, cols=4)
approval_table.style = "Table Grid"
set_table_rtl(approval_table)
headers = ["المسمى الوظيفي", "الاسم", "التوقيع", "التاريخ"]
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

vals = ["مدير مكتب إدارة البيانات", "", "", ""]
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
    "هذا الدليل مرفق تدقيق مستقل ضمن حزمة أدلة تصنيف البيانات الخاصة بهيئة الخدمات الحكومية الذكية (SGSA) الداعمة لمتطلب DC.M.2، ويستخدم "
    "لإثبات تنفيذ أنشطة التوعية والتدريب الخاصة بتصنيف البيانات.",
    size=8, italic=True, color=GREY,
)

doc.save(OUT_PATH)
print("Saved:", OUT_PATH)
