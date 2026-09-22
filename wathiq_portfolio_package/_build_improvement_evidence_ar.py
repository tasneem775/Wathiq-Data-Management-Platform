# -*- coding: utf-8 -*-
"""Localizes Data_Classification_Improvement_Evidence.docx into Arabic (Wathiq identity).

Overwrites the SAME file path in place — no new file is created.
Controlled localization / compliance-formatting pass only:
  - No improvement initiative, action, evidence link, implementation status,
    date, or number changed from the original English version.
  - No new improvement initiatives or corrective actions added.
  - DC.M.4 relationship and compliance scope unchanged.
"""
import docx
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT_PATH = "02_Improvement_Evidence/Data_Classification_Improvement_Evidence.docx"

NAVY = RGBColor(0x1F, 0x2A, 0x44)
GOLD = RGBColor(0xAB, 0x8D, 0x54)
GREY = RGBColor(0x59, 0x59, 0x59)
GREEN = RGBColor(0x1F, 0x6F, 0x43)
AR_FONT = "Arial"

# ---- Preserved rows (identical facts/dates/status — Arabic wording only) ----
ROWS = [
    (
        "جودة بيانات التصنيف",
        "كانت حقول البيانات الوصفية للأصول (المالك، النظام المصدر، تاريخ التصنيف) تُسجَّل بشكل "
        "غير متسق عبر الإدارات قبل دورة المراجعة.",
        "طُبِّق نموذج بيانات وصفية موحَّد بشكل متسق على جميع الأصول الـ30 التي روجعت خلال "
        "دورة المراجعة (1 مايو – 15 يونيو 2026).",
        "سجلات دورة المراجعة؛ تقرير بيانات المؤشرات الداعم (نسبة تغطية المراجعة: 100%)",
        "مكتمل",
    ),
    (
        "تحديث سجل التصنيف (DC.C.5.1)",
        "كان سجل التصنيف يعكس مستويات تصنيف الأصول كما كانت قبل نتيجة دورة المراجعة الحالية.",
        "حُدِّث السجل ليعكس التغييرات الثلاثة في التصنيف (تخفيض) وتثبيت حالة الأصول الـ26 "
        "المتبقية الناتجة عن دورة المراجعة.",
        "سجل قرارات المراجعة؛ قيود سجل التصنيف المُحدَّثة",
        "مكتمل",
    ),
    (
        "متابعة الامتثال",
        "كانت أنشطة المراجعة تُتابَع دون رؤية موحَّدة للمؤشرات تغطي التغطية وتغييرات التصنيف والمشاركة.",
        "أُدرِج تقرير موحَّد لبيانات المؤشرات الداعمة، يغطي نسبة تغطية المراجعة، والأصول التي "
        "تمت مراجعتها، وتغييرات التصنيف، ومدة المراجعة، ومشاركة ملاك البيانات.",
        "تقرير بيانات المؤشرات الداعم (يدعم DC.M.3 / DC.C.4.1 / DC.M.12)",
        "مكتمل",
    ),
    (
        "دورة المراجعة الدورية",
        "لم تكن أنشطة مراجعة التصنيف مُهيكَلة باستمرار ضمن دورة متكررة محدَّدة بتواريخ بدء وإغلاق واضحة.",
        "نُفِّذت دورة مراجعة مُهيكَلة مدتها 6 أسابيع (1 مايو – 15 يونيو 2026) من البداية حتى "
        "الإغلاق، بمشاركة 12 من ملاك البيانات عبر الإدارات، وشملت جميع الأصول الـ30 "
        "المصنفة (18 مجموعة بيانات، 12 سجلاً).",
        "جدول دورة المراجعة؛ سجل مشاركة ملاك البيانات",
        "مكتمل",
    ),
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

# ---- Title banner ----
banner = doc.add_table(rows=1, cols=1)
banner.autofit = True
set_table_rtl(banner)
cell = banner.rows[0].cells[0]
set_cell_background(cell, "1F2A44")
cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
p = cell.paragraphs[0]
rtl(p)
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
run = p.add_run("سجل أدلة التحسين المستمر لتصنيف البيانات")
run.font.size = Pt(18)
run.font.bold = True
run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
set_rtl_run(run)
p.paragraph_format.space_before = Pt(6)
p.paragraph_format.space_after = Pt(6)

doc.add_paragraph()

add_paragraph_ar(doc, "منصة ذكية لإدارة وقياس الامتثال لمتطلبات المكتب الوطني لإدارة البيانات (NDMO)",
                  size=10.5, bold=True, color=GOLD, italic=False)

sub = add_heading_ar(doc, "أدلة التحسين — تصنيف البيانات", size=14)
sub2 = add_paragraph_ar(doc, "سجل التحسين المستمر لحوكمة تصنيف البيانات", size=11, italic=True, color=GOLD)

doc.add_paragraph()

meta_table = doc.add_table(rows=0, cols=2)
meta_table.autofit = True
set_table_rtl(meta_table)
meta_table.columns[0].width = Cm(11)
meta_table.columns[1].width = Cm(5)
add_meta_row(meta_table, "الجهة", "هيئة الخدمات الحكومية الذكية (SGSA)")
add_meta_row(meta_table, "القسم", "مكتب إدارة البيانات")
add_meta_row(meta_table, "النطاق", "تصنيف البيانات (Data Classification)")
add_meta_row(meta_table, "الإطار المرجعي", "إطار حوكمة البيانات الوطني (NDMO)")
add_meta_row(meta_table, "المتطلب المدعوم", "DC.M.4 — تقرير مراجعة خطة تصنيف البيانات")
add_meta_row(meta_table, "مستوى النضج المرجعي", "DC.MQ.1 — التحسين المستمر لخطة التصنيف")
add_meta_row(meta_table, "دورة المراجعة المرجعية", "1 مايو 2026 – 15 يونيو 2026 (6 أسابيع)")

doc.add_paragraph()

# ---- الغرض من الوثيقة ----
add_heading_ar(doc, "الغرض من الوثيقة", size=12.5)
add_paragraph_ar(doc, "توثّق هذه الوثيقة التحسينات المنفذة لدعم المتطلب DC.M.4 ضمن مجال تصنيف البيانات.")
doc.add_paragraph()

# ---- نطاق التحسين ----
add_heading_ar(doc, "نطاق التحسين", size=12.5)
add_paragraph_ar(
    doc,
    "ترتبط جميع أنشطة التحسين الواردة في هذه الوثيقة بضوابط تصنيف البيانات ونتائج المراجعات ذات العلاقة."
)
doc.add_paragraph()

# ---- Preserved original intro paragraph (translated only, content unchanged) ----
add_paragraph_ar(
    doc,
    "يوثّق هذا السجل إجراءات التحسين المنفذة عقب دورة مراجعة التصنيف للفترة من 1 مايو إلى "
    "15 يونيو 2026، والتي شملت مراجعة جميع الأصول البيانية المصنفة الـ30 (18 مجموعة بيانات "
    "و12 سجلاً)، وأسفرت عن تثبيت تصنيف 26 أصلاً، وتعديل تصنيف 3 أصول (تخفيض)، وعدم حاجة أصل "
    "واحد لأي إجراء إضافي.",
    color=RGBColor(0x33, 0x33, 0x33),
)

doc.add_paragraph()

# ---- Improvement table (preserved rows, Arabic headers) ----
headers = ["مبادرة التحسين", "الوضع السابق", "إجراء التحسين المنفذ", "الأدلة الداعمة", "حالة التنفيذ"]
table = doc.add_table(rows=1, cols=5)
table.style = "Table Grid"
set_table_rtl(table)
widths = [Cm(3.2), Cm(4.3), Cm(4.8), Cm(4.0), Cm(1.8)]
for i, w in enumerate(widths):
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

for idx, (area, prev, impl, evidence, status) in enumerate(ROWS):
    row = table.add_row()
    values = [area, prev, impl, evidence, status]
    for c, v in enumerate(values):
        cell = row.cells[c]
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        if idx % 2 == 0:
            set_cell_background(cell, "F2F2F2")
        p = cell.paragraphs[0]
        rtl(p)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c == 4 else WD_ALIGN_PARAGRAPH.RIGHT
        run = p.add_run(v)
        run.font.size = Pt(8.5)
        set_rtl_run(run)
        if c == 0:
            run.font.bold = True
            run.font.color.rgb = NAVY
        elif c == 4:
            run.font.bold = True
            run.font.color.rgb = GREEN
        else:
            run.font.color.rgb = RGBColor(0x26, 0x26, 0x26)

for row in table.rows:
    tr = row._tr
    trPr = tr.get_or_add_trPr()
    cant_split = OxmlElement("w:cantSplit")
    trPr.append(cant_split)

doc.add_paragraph()
doc.add_paragraph()

# ---- مرجعية التحسينات (closing section) ----
add_heading_ar(doc, "مرجعية التحسينات", size=12.5)
add_paragraph_ar(
    doc,
    "تستند جميع التحسينات المذكورة في هذه الوثيقة إلى نتائج مراجعات موثقة وأدلة داعمة ضمن "
    "مجال تصنيف البيانات.",
    size=9,
    italic=True,
    color=GREY,
)

doc.save(OUT_PATH)
print("Saved (overwritten in place):", OUT_PATH)
