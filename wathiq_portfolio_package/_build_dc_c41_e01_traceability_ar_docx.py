# -*- coding: utf-8 -*-
"""Word (docx) version of DC.C.4.1-E01_دليل_تتبع_وتحقق_تصنيف_الأصول_البيانية — matches
the content of the already-approved Arabic Excel and PDF exactly. Same 30-asset data
(name, type, department, classification), same 100% matching rate, same asset-3/asset-13
naming-difference notes. No new information added, no asset changed, order 1-30 preserved.
"""
import docx
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT_PATH = "06_DC_C4_1_KPI_Evidence/DC.C.4.1-E01_دليل_تتبع_وتحقق_تصنيف_الأصول_البيانية.docx"

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


def add_paragraph_ar(doc, text, size=10, bold=False, italic=False, color=RGBColor(0x26, 0x26, 0x26), align=WD_ALIGN_PARAGRAPH.RIGHT):
    p = doc.add_paragraph()
    rtl(p)
    p.alignment = align
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    set_rtl_run(r)
    return p


def add_heading_ar(doc, text, size=14, align=WD_ALIGN_PARAGRAPH.RIGHT):
    p = doc.add_paragraph()
    rtl(p)
    p.alignment = align
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.font.bold = True
    r.font.color.rgb = NAVY
    set_rtl_run(r)
    return p


def add_bullet_ar(doc, text, size=10):
    p = doc.add_paragraph()
    rtl(p)
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p.add_run("•  " + text)
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor(0x26, 0x26, 0x26)
    set_rtl_run(r)
    return p


RESULT_COLOR = {"مطابق": GREEN, "جزئي": AMBER}


def make_table(doc, headers, rows, col_widths, result_col=None, font_size=8.5):
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
        r.font.size = Pt(9)
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
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c != len(row_vals) - 1 and c != 1 else WD_ALIGN_PARAGRAPH.RIGHT
            run = p.add_run(str(v))
            run.font.size = Pt(font_size)
            set_rtl_run(run)
            if c == 0:
                run.font.bold = True
                run.font.color.rgb = NAVY
            elif result_col is not None and c == result_col:
                run.font.bold = True
                run.font.color.rgb = RESULT_COLOR.get(str(v), RGBColor(0x26, 0x26, 0x26))
            elif c == len(row_vals) - 1:
                run.font.color.rgb = GREY
                run.font.italic = True
                run.font.size = Pt(7.5)
            else:
                run.font.color.rgb = RGBColor(0x26, 0x26, 0x26)
    for row in table.rows:
        trPr = row._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
    return table


# ============ بيانات مصدرها الحرفي DC.C.3.1 (Table 8) + DC.C.3.2 (Table 11/9) + DC.C.5.1 (Table 6) ============
# مطابقة تماماً لقائمة الأصول في النسختين الإنجليزية والعربية (Excel/PDF) المعتمدتين
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

NOTES_AR = {
    3: "اختلاف تسمية بين المصادر المرجعية الأصلية؛ يحتوي DC.C.3.1 على اللاحقة (IAM)، بينما لا تظهر في DC.C.3.2 وDC.C.5.1. لا يؤثر ذلك على قابلية تتبع الأصل.",
    13: "اختلاف في تسمية الإدارة بين المصادر المرجعية الأصلية؛ يذكر DC.C.3.1 \"مكتب الاستراتيجية والتخطيط\"، بينما يذكر DC.C.3.2 وDC.C.5.1 \"مكتب الاستراتيجية\". لا يؤثر ذلك على قابلية تتبع الأصل.",
}

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

# ============================================================
# 1) صفحة الغلاف
# ============================================================
banner = doc.add_table(rows=1, cols=1)
banner.autofit = True
set_table_rtl(banner)
cell = banner.rows[0].cells[0]
set_cell_background(cell, "1F2A44")
cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
p = cell.paragraphs[0]
rtl(p)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("دليل التحقق من قابلية تتبع تصنيف الأصول البيانية")
run.font.size = Pt(20)
run.font.bold = True
run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
set_rtl_run(run)
p.paragraph_format.space_before = Pt(8)
p.paragraph_format.space_after = Pt(8)

doc.add_paragraph()
add_paragraph_ar(doc, "منصة ذكية لإدارة وقياس الامتثال لمتطلبات المكتب الوطني لإدارة البيانات (NDMO)",
                  size=11, bold=True, color=GOLD, align=WD_ALIGN_PARAGRAPH.CENTER)
doc.add_paragraph()
add_heading_ar(doc, "دليل التحقق من قابلية تتبع تصنيف الأصول البيانية", size=17, align=WD_ALIGN_PARAGRAPH.CENTER)
add_paragraph_ar(doc, "حزمة دليل التحقق DC.C.4.1-E01 (KPI-DC-01)", size=11.5, italic=True, color=GOLD, align=WD_ALIGN_PARAGRAPH.CENTER)

doc.add_paragraph()
doc.add_paragraph()

kpi_table = doc.add_table(rows=0, cols=1)
kpi_table.autofit = True
set_table_rtl(kpi_table)
row = kpi_table.add_row()
set_cell_background(row.cells[0], "1F2A44")
row.cells[0].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
p1 = row.cells[0].paragraphs[0]
rtl(p1)
p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
r1 = p1.add_run("المؤشر: نسبة اكتمال تصنيف الأصول البيانية")
r1.font.size = Pt(12.5)
r1.font.bold = True
r1.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
set_rtl_run(r1)
p1.paragraph_format.space_before = Pt(10)
p1.paragraph_format.space_after = Pt(2)

row2 = kpi_table.add_row()
set_cell_background(row2.cells[0], "1F2A44")
row2.cells[0].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
p2 = row2.cells[0].paragraphs[0]
rtl(p2)
p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
r2 = p2.add_run("النتيجة: 100%")
r2.font.size = Pt(28)
r2.font.bold = True
r2.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
set_rtl_run(r2)
p2.paragraph_format.space_before = Pt(4)
p2.paragraph_format.space_after = Pt(2)

row3 = kpi_table.add_row()
set_cell_background(row3.cells[0], "1F2A44")
row3.cells[0].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
p3 = row3.cells[0].paragraphs[0]
rtl(p3)
p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
r3 = p3.add_run("30 من أصل 30 أصلاً تم التحقق من قابلية تتبع تصنيفها عبر المصادر المرجعية الثلاثة")
r3.font.size = Pt(11)
r3.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
set_rtl_run(r3)
p3.paragraph_format.space_before = Pt(2)
p3.paragraph_format.space_after = Pt(10)

doc.add_page_break()

# ============================================================
# 2) ملخص التحقق من المصادر المرجعية
# ============================================================
add_heading_ar(doc, "ملخص التحقق من المصادر المرجعية", size=14)
doc.add_paragraph()
make_table(
    doc,
    ["المصدر المرجعي", "عدد الأصول", "نتيجة التحقق"],
    [
        ("DC.C.3.1", str(TOTAL), "مطابق"),
        ("DC.C.3.2", str(TOTAL), "مطابق"),
        ("DC.C.5.1", str(TOTAL), "مطابق"),
    ],
    [Cm(6.0), Cm(5.0), Cm(6.0)],
    result_col=2,
    font_size=10,
)

doc.add_paragraph()
add_paragraph_ar(
    doc,
    "تم التحقق من وجود جميع الأصول البيانية الثلاثين (30) الواردة في DC.C.3.1 عبر "
    "DC.C.3.2 وDC.C.5.1، مع عدم وجود أي أصول ناقصة أو إضافية بين المصادر المرجعية الثلاثة."
)

doc.add_page_break()

# ============================================================
# 3) جدول مطابقة الأصول البيانية الثلاثين
# ============================================================
add_heading_ar(doc, "جدول مطابقة الأصول البيانية الثلاثين", size=14)
doc.add_paragraph()

rows = []
for n, name, atype, dept, cls in ASSETS:
    result = "جزئي" if n in NOTES_AR else "مطابق"
    note = NOTES_AR.get(n, "—")
    rows.append((n, name, atype, dept, cls, result, note))

make_table(
    doc,
    ["رقم الأصل", "اسم الأصل", "النوع", "الإدارة المالكة", "التصنيف", "نتيجة المطابقة", "الملاحظات"],
    rows,
    [Cm(1.4), Cm(4.6), Cm(2.0), Cm(3.4), Cm(1.9), Cm(1.9), Cm(2.8)],
    result_col=5,
    font_size=7.6,
)

doc.add_page_break()

# ============================================================
# 5) قسم ملاحظات التحقق والتدقيق
# ============================================================
add_heading_ar(doc, "ملاحظات التحقق والتدقيق", size=14)
doc.add_paragraph()
add_bullet_ar(doc, "جميع الأصول البيانية الثلاثين موجودة في المصادر المرجعية الثلاثة.")
add_bullet_ar(doc, "لم يتم إنشاء أي أصول جديدة.")
add_bullet_ar(doc, "لم يتم تعديل أي اسم أصل أو نوع أصل أو إدارة مالكة أو تصنيف.")
add_bullet_ar(doc, "تم استخدام الرقم التسلسلي الوارد في الجداول المرجعية كمعرّف تتبع داخلي لعدم وجود معرّفات أصول مستقلة في المصادر.")
add_bullet_ar(doc, "الاختلافات في الأصل رقم (3) والأصل رقم (13) هي فروقات تسمية بين الوثائق المرجعية الأصلية فقط.")

doc.add_paragraph()
add_paragraph_ar(
    doc,
    "هذه الوثيقة حزمة دليل تحقق (Evidence Verification Package) تم إعدادها لدعم متطلب "
    "DC.C.4.1 ومؤشر KPI-DC-01، ولا تمثل متطلباً جديداً أو تعديلاً على المتطلبات المرجعية.",
    size=8, italic=True, color=GREY,
)

doc.save(OUT_PATH)
print("Saved:", OUT_PATH)
print("Asset count:", TOTAL)
print("Notes rows:", list(NOTES_AR.keys()))
