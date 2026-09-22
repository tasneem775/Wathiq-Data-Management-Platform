# -*- coding: utf-8 -*-
"""Builds a NEW, standalone supporting EVIDENCE record for DC.M.3 (DC-KPI-03) within the
Wathiq/SGSA portfolio context — independent from any existing evidence_repository file.

IMPORTANT — this is an Evidence Record, NOT a Calculation Record: DC.M.2 (the sole approved
source used here) never states "إجمالي المستهدفين" (the KPI formula's denominator), so the
90% value cannot be independently recomputed. This document documents that 90% is stated
verbatim in DC.M.2 (a real, evidence_repository document explicitly referenced by DC.M.3's
own introduction: "يُكمل هذا التقرير تقرير حالة التنفيذ (DC.M.2)"), and does not claim to
recompute it. No Wathiq-package file (DC.M.2-E03/E04/etc.) is used. Neither DC.M.2 nor
DC.M.3 is modified.
"""
import docx
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT_PATH = "06_DC_M3_KPI_Evidence/DC.M.3-E03_Training_Awareness_KPI_Evidence_Record.docx"

NAVY = RGBColor(0x1F, 0x2A, 0x44)
GOLD = RGBColor(0xAB, 0x8D, 0x54)
GREY = RGBColor(0x59, 0x59, 0x59)
GREEN = RGBColor(0x1F, 0x6F, 0x43)
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


def make_table(doc, headers, rows, col_widths, font_size=9):
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
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            run = p.add_run(str(v))
            run.font.size = Pt(font_size)
            set_rtl_run(run)
            if c == 0:
                run.font.bold = True
                run.font.color.rgb = NAVY
            elif c == len(row_vals) - 1:
                run.font.color.rgb = RGBColor(0x26, 0x26, 0x26)
                run.font.italic = True
            else:
                run.font.bold = True
                run.font.color.rgb = GREEN
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
run = p.add_run("سجل إثبات مؤشر إكمال التوعية بتصنيف البيانات (DC-KPI-03)")
run.font.size = Pt(18)
run.font.bold = True
run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
set_rtl_run(run)
p.paragraph_format.space_before = Pt(6)
p.paragraph_format.space_after = Pt(6)

doc.add_paragraph()
add_paragraph_ar(doc, "منصة ذكية لإدارة وقياس الامتثال لمتطلبات المكتب الوطني لإدارة البيانات (NDMO)",
                  size=10.5, bold=True, color=GOLD)
add_heading_ar(doc, "سجل إثبات مؤشر إكمال التوعية بتصنيف البيانات (DC-KPI-03)", size=14.5)
add_paragraph_ar(doc, "Training Awareness KPI Evidence Record", size=11, italic=True, color=GOLD)

doc.add_paragraph()

meta_table = doc.add_table(rows=0, cols=2)
meta_table.autofit = True
set_table_rtl(meta_table)
meta_table.columns[0].width = Cm(11)
meta_table.columns[1].width = Cm(5)
add_meta_row(meta_table, "الجهة", "هيئة الخدمات الحكومية الذكية (SGSA)")
add_meta_row(meta_table, "المنصة", "")
add_meta_row(meta_table, "الإطار المرجعي", "إطار حوكمة البيانات الوطني (NDMO)")
add_meta_row(meta_table, "رمز الدليل", "DC.M.3-E03")
add_meta_row(meta_table, "المتطلب المرتبط", "DC.M.3 — تقرير مراقبة تنفيذ خطة تصنيف البيانات عبر مؤشرات الأداء الرئيسية")
add_meta_row(meta_table, "المؤشر المرتبط", "DC-KPI-03 — نسبة إكمال التوعية بتصنيف البيانات")
add_meta_row(meta_table, "الإصدار", "1.0")
add_meta_row(meta_table, "التاريخ", "يونيو 2026")
add_meta_row(meta_table, "حالة الوثيقة", "جاهزة للاعتماد")

doc.add_page_break()

# ============ 2) المقدمة ============
add_heading_ar(doc, "1.  المقدمة")
add_paragraph_ar(
    doc,
    "يوثّق هذا السجل مصدر وقابلية تتبع القيمة الحالية لمؤشر الأداء الرئيسي DC-KPI-03 "
    "(نسبة إكمال التوعية بتصنيف البيانات)، حيث يذكر تقرير DC.M.3 — تقرير مراقبة تنفيذ "
    "خطة تصنيف البيانات عبر مؤشرات الأداء الرئيسية — أن القيمة الحالية لهذا المؤشر "
    "هي 90%."
)
add_paragraph_ar(
    doc,
    "المصدر المستخدم للتحقق من هذه القيمة هو DC.M.2 — تقرير حالة تنفيذ خطة تصنيف "
    "البيانات، وهو تقرير رسمي ضمن مستودع الأدلة، أشار إليه تقرير DC.M.3 نفسه صراحةً "
    "في مقدمته بوصفه مكمِّلاً له. لا يُعيد هذا السجل احتساب النسبة الواردة، بل يوثّق "
    "وجودها في المصدر الرسمي المذكور."
)

doc.add_paragraph()

# ============ 3) بيانات المصدر ============
add_heading_ar(doc, "2.  بيانات المصدر")
meta2 = doc.add_table(rows=0, cols=2)
meta2.autofit = True
set_table_rtl(meta2)
meta2.columns[0].width = Cm(11)
meta2.columns[1].width = Cm(5)
add_meta_row(meta2, "المصدر", "DC.M.2 — تقرير حالة تنفيذ خطة تصنيف البيانات")
add_meta_row(meta2, "فترة التغطية", "حتى يونيو 2026")
add_meta_row(meta2, "القيمة الواردة", "90%")

doc.add_paragraph()
add_paragraph_ar(doc, "البيانات المتعلقة الواردة في DC.M.2:", bold=True, size=10)
add_bullet_ar(doc, "نسبة إنجاز برنامج التوعية والتدريب: 90%")
add_bullet_ar(doc, "عدد المشاركين: 47 موظفاً")
add_bullet_ar(doc, "تنفيذ 3 من أصل 4 ورش توعية مخططة")

doc.add_paragraph()

# ============ 4) إثبات القيمة ============
add_heading_ar(doc, "3.  إثبات القيمة")
add_paragraph_ar(doc, "يعرض الجدول التالي البيانات كما وردت حرفياً في DC.M.2:")
make_table(
    doc,
    ["البند", "القيمة", "المصدر"],
    [
        ("نسبة إنجاز برنامج التوعية والتدريب", "90%", "DC.M.2"),
        ("عدد المشاركين", "47 موظفاً", "DC.M.2"),
        ("الورش المنفذة", "3 من أصل 4", "DC.M.2"),
    ],
    [Cm(7.0), Cm(4.5), Cm(4.5)],
)

doc.add_paragraph()

# ============ 5) حدود إعادة الاحتساب ============
add_heading_ar(doc, "4.  حدود إعادة الاحتساب")
add_paragraph_ar(
    doc,
    "لا يتضمن المصدر DC.M.2 قيمة إجمالي الموظفين المستهدفين اللازمة لإعادة تطبيق "
    "معادلة المؤشر حرفياً، لذلك يقتصر هذا السجل على إثبات القيمة الواردة في المصدر "
    "الرسمي ولا يقدم احتساباً مستقلاً للمؤشر."
)

doc.add_paragraph()

# ============ 6) التسلسل الزمني ============
add_heading_ar(doc, "5.  التسلسل الزمني")
add_bullet_ar(doc, "DC.M.2 وDC.M.3 يعكسان دورة القياس حتى يونيو 2026، وكانت القيمة 90%.")
add_bullet_ar(doc, "DC.M.4 يمثل دورة قياس لاحقة بعد إجراءات تحسين، وذكر ارتفاع القيمة إلى 95%.")
add_bullet_ar(doc, "لا يوجد تعارض بين القيمتين لاختلاف فترة القياس.")

doc.add_paragraph()

# ============ 7) التحقق والاعتماد ============
add_heading_ar(doc, "6.  التحقق والاعتماد")
add_paragraph_ar(
    doc,
    "تمت مراجعة هذا السجل والتحقق من مطابقة البيانات الواردة فيه لمحتوى DC.M.2 دون "
    "إضافة أو حذف أو تعديل."
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
    "ملاحظة: هذا السجل دليل داعم مستقل ضمن حزمة أدلة تصنيف البيانات الخاصة بهيئة الخدمات الحكومية الذكية (SGSA)، أُعدّ لتوثيق مصدر "
    "وقابلية تتبع قيمة مؤشر DC-KPI-03 دون تعديل أي محتوى في تقرير DC.M.3 أو تقرير DC.M.2.",
    size=8, italic=True, color=GREY,
)

doc.save(OUT_PATH)
print("Saved:", OUT_PATH)
