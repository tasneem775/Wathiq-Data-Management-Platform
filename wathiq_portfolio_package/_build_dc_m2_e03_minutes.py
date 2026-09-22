# -*- coding: utf-8 -*-
"""Builds a NEW, standalone evidence artifact: DC.M.2-E03 Follow-Up Meeting Minutes (Word).

Independent file — does not modify DC_M2_Implementation_Status_Report.*, E01, E02,
or any other file. Wathiq/SGSA identity, RTL Arabic. No classification levels.
No mention of DC.C.3.4.
"""
import docx
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT_PATH = "05_DC_M2_Draft_Evidence/DC.M.2-E03_Data_Classification_Follow_Up_Meeting_Minutes.docx"

NAVY = RGBColor(0x1F, 0x2A, 0x44)
GOLD = RGBColor(0xAB, 0x8D, 0x54)
GREY = RGBColor(0x59, 0x59, 0x59)
GREEN = RGBColor(0x1F, 0x6F, 0x43)
AR_FONT = "Arial"

MEETING1_ATTENDEES = [
    "مدير مكتب إدارة البيانات",
    "ممثل إدارة الموارد البشرية",
    "ممثل الإدارة المالية",
    "ممثل إدارة تقنية المعلومات",
    "ممثل إدارة الخدمات الرقمية",
]

MEETINGS = [
    {
        "title": "محضر اجتماع متابعة تنفيذ خطة تصنيف البيانات رقم (1)",
        "date": "01 مايو 2026",
        "objective": "متابعة بدء تنفيذ خطة تصنيف البيانات.",
        "attendees": MEETING1_ATTENDEES,
        "attendees_note": None,
        "topics": [
            "مراجعة خطة التنفيذ.",
            "متابعة حصر مجموعات البيانات والسجلات.",
            "متابعة تحديد ملاك البيانات.",
        ],
        "decisions": [
            "اعتماد بدء تنفيذ أنشطة الخطة.",
            "استكمال أعمال حصر البيانات.",
            "متابعة تحديث سجل ملاك البيانات.",
        ],
    },
    {
        "title": "محضر اجتماع متابعة تنفيذ خطة تصنيف البيانات رقم (2)",
        "date": "30 مايو 2026",
        "objective": "مراجعة مستوى التقدم في تنفيذ الخطة.",
        "attendees": MEETING1_ATTENDEES,
        "attendees_note": "نفس حضور الاجتماع رقم (1)",
        "topics": [
            "مراجعة حالة الأنشطة المنفذة.",
            "متابعة المبادرات قيد التنفيذ.",
        ],
        "decisions": [
            "تأكيد اكتمال حصر مجموعات البيانات.",
            "متابعة استكمال الأنشطة المتبقية.",
        ],
    },
    {
        "title": "محضر اجتماع متابعة تنفيذ خطة تصنيف البيانات رقم (3)",
        "date": "15 يونيو 2026",
        "objective": "مراجعة حالة الإنجاز النهائية للمرحلة الأولى.",
        "attendees": MEETING1_ATTENDEES,
        "attendees_note": "نفس حضور الاجتماع رقم (1)",
        "topics": [
            "مراجعة نسبة الإنجاز.",
            "توثيق الملاحظات النهائية.",
        ],
        "decisions": [
            "توثيق نتائج التنفيذ.",
            "رفع حالة التنفيذ ضمن تقرير المتابعة.",
        ],
    },
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


def make_table(doc, headers, rows, col_widths, center_cols=None):
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
run = p.add_run("محضر متابعة تنفيذ خطة تصنيف البيانات")
run.font.size = Pt(18)
run.font.bold = True
run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
set_rtl_run(run)
p.paragraph_format.space_before = Pt(6)
p.paragraph_format.space_after = Pt(6)

doc.add_paragraph()
add_paragraph_ar(doc, "منصة ذكية لإدارة وقياس الامتثال لمتطلبات المكتب الوطني لإدارة البيانات (NDMO)",
                  size=10.5, bold=True, color=GOLD)
add_heading_ar(doc, "محاضر اجتماعات متابعة تنفيذ خطة تصنيف البيانات", size=15)
add_paragraph_ar(doc, "دليل داعم — DC.M.2-E03", size=11, italic=True, color=GOLD)

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
add_meta_row(meta_table, "رمز الدليل", "DC.M.2-E03")
add_meta_row(meta_table, "المتطلب المرتبط", "DC.M.2 — تنفيذ خطة تصنيف البيانات وخارطة الطريق")
add_meta_row(meta_table, "اسم الدليل", "محاضر اجتماعات متابعة تنفيذ خطة تصنيف البيانات")
add_meta_row(meta_table, "الإصدار", "1.0")
add_meta_row(meta_table, "التاريخ", "يونيو 2026")
add_meta_row(meta_table, "حالة الوثيقة", "جاهزة للمراجعة")

doc.add_page_break()

# ============ Meeting minutes ============
for idx, m in enumerate(MEETINGS, start=1):
    add_heading_ar(doc, m["title"], size=14)
    add_paragraph_ar(doc, f"التاريخ: {m['date']}", size=9.5, bold=True, color=GREY)
    add_paragraph_ar(doc, f"الهدف: {m['objective']}", size=9.5)
    doc.add_paragraph()

    add_paragraph_ar(doc, "الحضور:", bold=True, size=10, color=NAVY)
    if m["attendees_note"]:
        add_paragraph_ar(doc, m["attendees_note"], italic=True, size=9, color=GREY)
    make_table(
        doc,
        ["المسمى الوظيفي"],
        [(a,) for a in m["attendees"]],
        [Cm(16.0)],
    )
    doc.add_paragraph()

    add_paragraph_ar(doc, "المواضيع:", bold=True, size=10, color=NAVY)
    for t in m["topics"]:
        add_bullet_ar(doc, t)
    doc.add_paragraph()

    add_paragraph_ar(doc, "القرارات:", bold=True, size=10, color=NAVY)
    make_table(
        doc,
        ["الرقم", "القرار"],
        [(i + 1, d) for i, d in enumerate(m["decisions"])],
        [Cm(2.0), Cm(14.0)],
        center_cols=[0],
    )
    doc.add_paragraph()

    add_paragraph_ar(doc, "التوقيعات:", bold=True, size=10, color=NAVY)
    make_table(
        doc,
        ["المسمى الوظيفي", "التوقيع"],
        [(a, "____________") for a in m["attendees"]],
        [Cm(11.0), Cm(5.0)],
        center_cols=[1],
    )

    if idx < len(MEETINGS):
        doc.add_page_break()

doc.add_paragraph()
doc.add_paragraph()

# ============ الاعتماد ============
add_heading_ar(doc, "الاعتماد")
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
    "لإثبات اجتماعات متابعة تنفيذ خطة تصنيف البيانات.",
    size=8, italic=True, color=GREY,
)

doc.save(OUT_PATH)
print("Saved:", OUT_PATH)
