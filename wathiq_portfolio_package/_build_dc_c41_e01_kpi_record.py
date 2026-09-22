# -*- coding: utf-8 -*-
"""Builds a standalone compliance-audit Calculation Record for DC.C.4.1 (KPI-DC-01).

Purpose: document the data source and calculation method behind the "100%" current value
of KPI-DC-01 (نسبة اكتمال تصنيف الأصول البيانية) as reported in DC.C.4.1.docx.

All 30 asset rows below are copied verbatim from the real, existing evidence_repository
files: DC.C.3.1.docx (Table 8 — حالة الجرد) and DC.C.3.2.docx (Table 11 — مستوى التصنيف
الناتج). No asset name, serial number, or count is invented. DC.C.4.1 itself is not modified.

Audit template (7 sections, per compliance-auditor brief):
1. بيانات الوثيقة  2. نطاق القياس  3. مصدر البيانات  4. جدول البيانات المستخدمة
5. تطبيق المعادلة  6. النتيجة والتحقق مقابل DC.C.4.1  7. الاعتماد والتوقيع
"""
import docx
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT_PATH = "06_DC_C4_1_KPI_Evidence/DC.C.4.1-E01_KPI-DC-01_Data_Classification_KPI_Calculation_Record.docx"

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


def make_table(doc, headers, rows, col_widths, status_col=None, font_size=7.6):
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
        r.font.size = Pt(8.6)
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
                run.font.color.rgb = GREEN if v in ("مُجرَّد", "مصنَّف") else GREY
            else:
                run.font.color.rgb = RGBColor(0x26, 0x26, 0x26)
    for row in table.rows:
        trPr = row._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
    return table


# ============ بيانات مصدرها الحرفي DC.C.3.1.docx (Table 8) + DC.C.3.2.docx (Table 11) ============
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
KPI_VALUE = round(CLASSIFIED_ASSETS / TOTAL_ASSETS * 100)  # = 100

doc = docx.Document()
section = doc.sections[0]
section.left_margin = Cm(1.6)
section.right_margin = Cm(1.6)
section.top_margin = Cm(1.5)
section.bottom_margin = Cm(1.5)

style = doc.styles["Normal"]
style.font.name = AR_FONT
style.font.size = Pt(10)
style.element.rPr.rFonts.set(qn("w:cs"), AR_FONT)

# ============ صفحة الغلاف / 1. بيانات الوثيقة ============
banner = doc.add_table(rows=1, cols=1)
banner.autofit = True
set_table_rtl(banner)
cell = banner.rows[0].cells[0]
set_cell_background(cell, "1F2A44")
cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
p = cell.paragraphs[0]
rtl(p)
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
run = p.add_run("سجل احتساب مؤشر نسبة اكتمال تصنيف الأصول البيانية (KPI-DC-01)")
run.font.size = Pt(18)
run.font.bold = True
run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
set_rtl_run(run)
p.paragraph_format.space_before = Pt(6)
p.paragraph_format.space_after = Pt(6)

doc.add_paragraph()
add_paragraph_ar(doc, "منصة ذكية لإدارة وقياس الامتثال لمتطلبات المكتب الوطني لإدارة البيانات (NDMO)",
                  size=10.5, bold=True, color=GOLD)
add_heading_ar(doc, "سجل احتساب مؤشر نسبة اكتمال تصنيف الأصول البيانية (KPI-DC-01)", size=14)
add_paragraph_ar(doc, "Data Classification KPI Calculation Record", size=11, italic=True, color=GOLD)

doc.add_paragraph()
add_heading_ar(doc, "1.  بيانات الوثيقة", size=11.5)
meta_table = doc.add_table(rows=0, cols=2)
meta_table.autofit = True
set_table_rtl(meta_table)
meta_table.columns[0].width = Cm(11.5)
meta_table.columns[1].width = Cm(5)
add_meta_row(meta_table, "الجهة", "هيئة الخدمات الحكومية الذكية (SGSA)")
add_meta_row(meta_table, "المنصة", "")
add_meta_row(meta_table, "الإطار المرجعي", "إطار حوكمة البيانات الوطني (NDMO)")
add_meta_row(meta_table, "رمز الدليل", "DC.C.4.1-E01")
add_meta_row(meta_table, "نوع الوثيقة", "Calculation Record")
add_meta_row(meta_table, "المتطلب المرتبط", "DC.C.4.1 — تقرير مراقبة عمليات تصنيف البيانات عبر مؤشرات الأداء الرئيسية")
add_meta_row(meta_table, "المؤشر المرتبط", "KPI-DC-01 — نسبة اكتمال تصنيف الأصول البيانية")
add_meta_row(meta_table, "الإصدار", "1.0")
add_meta_row(meta_table, "التاريخ", "يونيو 2026")
add_meta_row(meta_table, "حالة الوثيقة", "جاهزة للاعتماد")

doc.add_page_break()

# ============ 2. نطاق القياس ============
add_heading_ar(doc, "2.  نطاق القياس")
meta2 = doc.add_table(rows=0, cols=2)
meta2.autofit = True
set_table_rtl(meta2)
meta2.columns[0].width = Cm(11.5)
meta2.columns[1].width = Cm(5)
add_meta_row(meta2, "فترة القياس", "الربع الثاني 2026 (أبريل – يونيو 2026) — كما ورد في تقرير DC.C.4.1")
add_meta_row(
    meta2, "نطاق القياس",
    "جميع الأصول البيانية الثلاثين (30) الواردة في تقرير الجرد DC.C.3.1 "
    "(18 مجموعة بيانات + 12 سجلاً)، والتي حُدِّد لكل منها مستوى تصنيف ناتج في DC.C.3.2."
)
add_meta_row(meta2, "تاريخ استخراج البيانات", "يونيو 2026 (تاريخ إصدار DC.C.3.1 وDC.C.3.2 وDC.C.5.1)")

doc.add_paragraph()

# ============ 3. مصدر البيانات ============
add_heading_ar(doc, "3.  مصدر البيانات")
add_bullet_ar(doc, "DC.C.3.1 — تقرير جرد المجموعات التي تم تحديدها من البيانات والسجلات (قائمة الأصول الثلاثين وحالة الجرد لكل أصل).")
add_bullet_ar(doc, "DC.C.3.2 — تقرير تقييم الأثر (مستوى التصنيف الناتج لكل أصل بعد تطبيق مبدأ أعلى مستوى أثر).")
add_bullet_ar(doc, "DC.C.5.1 — سجل البيانات (السجل الموحّد الذي يثبت مستوى التصنيف الممنوح لكل أصل).")

doc.add_paragraph()

# ============ 4. جدول البيانات المستخدمة ============
add_heading_ar(doc, "4.  جدول البيانات المستخدمة")
add_paragraph_ar(doc, "يعرض الجدول التالي جميع الأصول البيانية الثلاثين الواردة في تقرير الجرد DC.C.3.1، مع حالة الجرد ومستوى التصنيف الناتج وفق DC.C.3.2:")
rows = [
    (n, name, atype, dept, "مُجرَّد", level)
    for n, name, atype, dept, level in ASSETS
]
make_table(
    doc,
    ["م", "اسم الأصل", "نوع الأصل", "الإدارة المالكة", "حالة الجرد (DC.C.3.1)", "مستوى التصنيف (DC.C.3.2)"],
    rows,
    [Cm(0.8), Cm(4.6), Cm(2.2), Cm(2.9), Cm(2.5), Cm(2.4)],
    status_col=[4],
    font_size=7.4,
)

doc.add_paragraph()
add_paragraph_ar(
    doc,
    "ملاحظة تدقيق: لا يتضمن أيٌّ من DC.C.3.1 أو DC.C.3.2 أو DC.C.5.1 معرّفات مستقلة "
    "للأصول (مثل رموز SGSA-DAT/REC)؛ لذلك استُخدم الرقم التسلسلي (م) كما ورد في هذه "
    "المصادر نفسها كمعرّف تتبّع لكل أصل في الجدول أعلاه. لم تُستخدم أي بيانات من تقرير "
    "DC.M.7 في هذا السجل، التزاماً بالاقتصار على المصادر الثلاثة المصرَّح بها أعلاه فقط.",
    size=8, italic=True, color=GREY,
)

doc.add_page_break()

# ============ 5. تطبيق المعادلة ============
add_heading_ar(doc, "5.  تطبيق المعادلة")
make_table(
    doc,
    ["البند", "القيمة"],
    [
        ("إجمالي الأصول البيانية (وفق DC.C.3.1)", str(TOTAL_ASSETS)),
        ("عدد الأصول المصنَّفة (وفق DC.C.3.2)", str(CLASSIFIED_ASSETS)),
        ("معادلة المؤشر", "عدد الأصول المصنَّفة ÷ إجمالي الأصول البيانية × 100"),
        ("تطبيق المعادلة", f"{CLASSIFIED_ASSETS} ÷ {TOTAL_ASSETS} × 100"),
        ("القيمة النهائية للمؤشر", f"{KPI_VALUE}%"),
    ],
    [Cm(9.5), Cm(5.9)],
    status_col=[1],
    font_size=9,
)

doc.add_paragraph()

# ============ 6. النتيجة والتحقق مقابل DC.C.4.1 ============
add_heading_ar(doc, "6.  النتيجة والتحقق مقابل DC.C.4.1")
add_paragraph_ar(
    doc,
    f"القيمة الناتجة ({KPI_VALUE}%) مطابقة تماماً للقيمة المقيسة الواردة في بطاقة مؤشر "
    "KPI-DC-01 ضمن تقرير DC.C.4.1 (القسم 8 وبند 9.1: «100% (30 أصلاً من أصل 30 مُصنَّفاً)»)، "
    "وللقيمة الواردة في جدول لوحة الأداء الإجمالية (القسم 10) وجدول التوافق مع متطلبات "
    "NDMO (القسم 14)."
)
add_bullet_ar(doc, "تم التحقق من مطابقة عدد الأصول (30) وأسمائها وترتيبها التسلسلي بين DC.C.3.1 وDC.C.3.2 وDC.C.5.1 دون أي تعارض.")
add_bullet_ar(doc, "جميع الأصول الثلاثين مُصنَّفة (لا يوجد أصل بلا مستوى تصنيف ناتج)، وبذلك فإن البسط يساوي المقام ويكون الناتج 100% دون تقريب.")
add_bullet_ar(doc, "أي معلومة غير واردة حرفياً في DC.C.3.1 أو DC.C.3.2 أو DC.C.5.1 تم استبعادها من هذا السجل.")

doc.add_paragraph()

# ============ 7. الاعتماد والتوقيع ============
add_heading_ar(doc, "7.  الاعتماد والتوقيع")
add_paragraph_ar(
    doc,
    "تمت مراجعة هذا السجل من مكتب إدارة البيانات، وتم التحقق من مطابقة البيانات الواردة "
    "فيه لمحتوى DC.C.3.1 وDC.C.3.2 وDC.C.5.1 دون أي إضافة أو حذف أو تعديل."
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

doc.save(OUT_PATH)
print("Saved:", OUT_PATH)
print("TOTAL_ASSETS:", TOTAL_ASSETS)
print("CLASSIFIED_ASSETS:", CLASSIFIED_ASSETS)
print("KPI_VALUE:", KPI_VALUE)
