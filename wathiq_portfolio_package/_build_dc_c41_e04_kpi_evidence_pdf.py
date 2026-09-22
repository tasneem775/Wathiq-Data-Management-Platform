# -*- coding: utf-8 -*-
"""PDF twin of DC.C.4.1-E04_KPI-DC-04_Review_Endorsement_Approval_KPI_Evidence_Record.docx —
6-section compliance-audit template (Evidence Record; "تطبيق المعادلة" omitted per brief).
Sourced exclusively from the aggregate 4-stage table already stated in DC.C.4.1.docx itself
(section 9.4). No per-asset recomputation is claimed."""
import arabic_reshaper
from bidi.algorithm import get_display

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import stringWidth

OUT_PATH = "06_DC_C4_1_KPI_Evidence/DC.C.4.1-E04_KPI-DC-04_Review_Endorsement_Approval_KPI_Evidence_Record.pdf"

pdfmetrics.registerFont(TTFont("Arabic", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arabic-Bold", r"C:\Windows\Fonts\arialbd.ttf"))

NAVY = colors.HexColor("#1F2A44")
GOLD = colors.HexColor("#AB8654")
LIGHT_GREY = colors.HexColor("#F2F2F2")
GREEN = colors.HexColor("#1F6F43")
GREY = colors.HexColor("#595959")


def ar(text):
    return get_display(arabic_reshaper.reshape(text), base_dir="R")


def wrap_ar(text, font_name, font_size, max_width):
    words = text.split(" ")
    lines, current = [], []
    for w in words:
        trial = current + [w]
        shaped = get_display(arabic_reshaper.reshape(" ".join(trial)), base_dir="R")
        if not current or stringWidth(shaped, font_name, font_size) <= max_width:
            current = trial
        else:
            lines.append(" ".join(current))
            current = [w]
    if current:
        lines.append(" ".join(current))
    return "<br/>".join(get_display(arabic_reshaper.reshape(l), base_dir="R") for l in lines)


def ar_p(text, style, max_width):
    return Paragraph(wrap_ar(text, style.fontName, style.fontSize, max_width), style)


title_style = ParagraphStyle("TitleBar", fontName="Arabic-Bold", fontSize=16, leading=21, textColor=colors.white, alignment=2)
subtitle_bar_style = ParagraphStyle("SubtitleBar", fontName="Arabic-Bold", fontSize=9.5, leading=14, textColor=colors.white, alignment=2)
report_title_style = ParagraphStyle("ReportTitle", fontName="Arabic-Bold", fontSize=13, leading=17, textColor=NAVY, alignment=2)
draft_style = ParagraphStyle("Draft", fontName="Arabic", fontSize=10, leading=13, textColor=GOLD, alignment=2)
section_style = ParagraphStyle("Section", fontName="Arabic-Bold", fontSize=12, leading=15, textColor=NAVY, alignment=2, spaceBefore=6)
meta_label_style = ParagraphStyle("MetaLabel", fontName="Arabic-Bold", fontSize=9, textColor=GREY, alignment=2)
meta_value_style = ParagraphStyle("MetaValue", fontName="Arabic", fontSize=9, leading=13, textColor=colors.HexColor("#262626"), alignment=2)
body_style = ParagraphStyle("Body", fontName="Arabic", fontSize=9.5, leading=15, textColor=colors.HexColor("#262626"), alignment=2)
note_style = ParagraphStyle("Note", fontName="Arabic", fontSize=8, leading=12, textColor=GREY, alignment=2, italic=1)
bullet_style = ParagraphStyle("Bullet", fontName="Arabic", fontSize=9.5, leading=14, textColor=colors.HexColor("#262626"), alignment=2)
cell_style = ParagraphStyle("Cell", fontName="Arabic", fontSize=8.4, leading=11.5, alignment=1, textColor=colors.HexColor("#262626"))
cell_bold_navy = ParagraphStyle("CellBoldNavy", parent=cell_style, fontName="Arabic-Bold", textColor=NAVY, alignment=1)
cell_bold_green = ParagraphStyle("CellBoldGreen", parent=cell_style, fontName="Arabic-Bold", textColor=GREEN, alignment=1)
head_cell_style = ParagraphStyle("HeadCell", fontName="Arabic-Bold", fontSize=8.8, alignment=1, textColor=colors.white)


def rtl_table(headers_ar, rows, col_widths_ltr):
    header_row = [Paragraph(ar(h), head_cell_style) for h in reversed(headers_ar)]
    data = [header_row]
    for row_vals in rows:
        cells = []
        for i, v in enumerate(row_vals):
            if i == 0:
                cells.append(Paragraph(ar(str(v)), cell_bold_navy))
            elif i == 1:
                cells.append(Paragraph(ar(str(v)), cell_bold_green))
            else:
                cells.append(Paragraph(ar(str(v)), cell_style))
        data.append(list(reversed(cells)))
    col_widths = list(reversed(col_widths_ltr))
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GREY))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


STAGES = [
    ("المراجعة الأولية من فريق التصنيف", 30, "100%", "مارس 2026", "فريق مكتب إدارة البيانات"),
    ("اعتماد لجنة حوكمة البيانات", 30, "100%", "أبريل 2026", "لجنة حوكمة البيانات"),
    ("التصديق من مدير مكتب إدارة البيانات", 30, "100%", "مايو 2026", "مدير مكتب إدارة البيانات"),
    ("الاعتماد النهائي من مدير عام الهيئة", 30, "100%", "يونيو 2026", "مدير عام الهيئة"),
]
KPI_VALUE = "100%"

doc = SimpleDocTemplate(
    OUT_PATH, pagesize=A4,
    leftMargin=18 * mm, rightMargin=18 * mm, topMargin=14 * mm, bottomMargin=14 * mm,
)
story = []
FULL_W = doc.width


def meta_table_ar(rows, col_w=48 * mm):
    data = [
        [ar_p(v, meta_value_style, doc.width - col_w - 12), Paragraph(ar(l), meta_label_style)]
        for l, v in rows
    ]
    tbl = Table(data, colWidths=[doc.width - col_w, col_w])
    tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return tbl


def bullets(items):
    out = []
    for it in items:
        out.append(ar_p("•  " + it, bullet_style, FULL_W - 10))
        out.append(Spacer(1, 3))
    return out


title_tbl = Table(
    [[Paragraph(ar("منصة ذكية لإدارة وقياس الامتثال لمتطلبات المكتب الوطني لإدارة البيانات (NDMO)"), subtitle_bar_style)],
     [Paragraph(ar("سجل إثبات مؤشر المراجعة والتعميد والتصديق (KPI-DC-04)"), title_style)]],
    colWidths=[doc.width],
)
title_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), NAVY),
    ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ("TOPPADDING", (0, 0), (-1, 0), 4), ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
    ("TOPPADDING", (0, -1), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
]))
story.append(title_tbl)
story.append(Spacer(1, 8))
story.append(Paragraph(ar("سجل إثبات مؤشر المراجعة والتعميد والتصديق (KPI-DC-04)"), report_title_style))
story.append(Paragraph(ar("Review, Endorsement & Approval KPI Evidence Record"), draft_style))
story.append(Spacer(1, 10))

story.append(Paragraph(ar("1.  بيانات الوثيقة"), section_style))
story.append(Spacer(1, 4))
story.append(meta_table_ar([
    ("الجهة", "هيئة الخدمات الحكومية الذكية (SGSA)"),
    ("المنصة", ""),
    ("الإطار المرجعي", "إطار حوكمة البيانات الوطني (NDMO)"),
    ("رمز الدليل", "DC.C.4.1-E04"),
    ("نوع الوثيقة", "Evidence Record"),
    ("المتطلب المرتبط", "DC.C.4.1 — تقرير مراقبة عمليات تصنيف البيانات عبر مؤشرات الأداء الرئيسية"),
    ("المؤشر المرتبط", "KPI-DC-04 — نسبة الأصول التي خضعت للمراجعة والتعميد والتصديق"),
    ("الإصدار", "1.0"),
    ("التاريخ", "يونيو 2026"),
    ("حالة الوثيقة", "جاهزة للاعتماد"),
]))
story.append(PageBreak())

story.append(Paragraph(ar("2.  نطاق القياس"), section_style))
story.append(Spacer(1, 4))
story.append(meta_table_ar([
    ("عدد الأصول", "30 أصلاً (إجمالي الأصول البيانية المصنَّفة وفق DC.C.3.1)"),
    ("فترة الاعتماد", "مارس 2026 – يونيو 2026 — أربع مراحل متتابعة كما ورد في DC.C.4.1"),
    ("تاريخ استخراج البيانات", "يونيو 2026 (تاريخ إصدار DC.C.4.1)"),
]))
story.append(Spacer(1, 10))

story.append(Paragraph(ar("3.  مصدر البيانات"), section_style))
story.append(Spacer(1, 4))
story.extend(bullets([
    "تقرير DC.C.4.1 نفسه (القسم 9.4 وجدول مراحل الاعتماد) — المصدر الوحيد المتاح لبيانات هذا المؤشر بمستوى المراحل الأربع.",
    "DC.C.5.1 — سجل البيانات، يثبت لكل أصل من الأصول الثلاثين تاريخ مراجعة تصنيف واحداً (يونيو 2026)، دون تفصيل مراحل التعميد والتصديق الأربع بشكل منفصل لكل أصل.",
]))
story.append(PageBreak())

story.append(Paragraph(ar("4.  جدول البيانات المستخدمة"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p("استُخدمت فقط البيانات الإجمالية التالية، كما وردت حرفياً في تقرير DC.C.4.1 (القسم 9.4):", body_style, FULL_W))
story.append(Spacer(1, 6))
stage_rows = [(stage, str(n), pct, date, entity) for stage, n, pct, date, entity in STAGES]
story.append(rtl_table(
    ["مرحلة الاعتماد", "عدد الأصول", "النسبة", "تاريخ الاكتمال", "الجهة المعتمِدة"],
    stage_rows,
    [60 * mm, 18 * mm, 14 * mm, 22 * mm, 40 * mm],
))
story.append(Spacer(1, 6))
story.append(ar_p(
    "ملاحظة تدقيق: لا يتضمن هذا السجل سجلاً فردياً لكل أصل من الأصول الثلاثين، ولا "
    "توقيعات فردية، ولا أسماء معتمدين لكل أصل على حدة، لأن هذا المستوى من التفصيل غير "
    "متوفر في أي مصدر رسمي ضمن مستودع الأدلة. لا ينطبق قسم «تطبيق المعادلة» على هذا "
    "السجل: لا يتوفر سجل فردي لكل أصل يتيح إعادة احتساب النسبة (100%) من بيانات خام؛ "
    "يقتصر هذا السجل على إثبات القيمة الإجمالية المذكورة في DC.C.4.1 دون إعادة اشتقاقها.",
    note_style, FULL_W))
story.append(PageBreak())

story.append(Paragraph(ar("5.  النتيجة والتحقق مقابل DC.C.4.1"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p(
    f"القيمة الموثَّقة ({KPI_VALUE}) مطابقة تماماً للقيمة الواردة في بطاقة مؤشر KPI-DC-04 "
    "ضمن تقرير DC.C.4.1 (القسم 8 وبند 9.4)، وللقيمة الواردة في جدول لوحة الأداء الإجمالية "
    "(القسم 10) وجدول التوافق مع متطلبات NDMO (القسم 14).", body_style, FULL_W))
story.append(Spacer(1, 6))
story.extend(bullets([
    "جدول مراحل الاعتماد الأربع (المراجعة الأولية، اعتماد اللجنة، التصديق، الاعتماد النهائي) هو نفسه الجدول الوارد حرفياً في تقرير DC.C.4.1، ولم تُضَف أو تُحذف أي مرحلة.",
    "لم تُخترع أي توقيعات فردية أو أسماء معتمدين لكل أصل؛ الجهات المعتمِدة الأربع المذكورة في الجدول هي نفسها المذكورة في مصدرها فقط بصفتها الوظيفية (لا بأسماء أشخاص).",
    "هذا السجل Evidence Record وليس Calculation Record، لأن البيانات المتاحة إجمالية فقط (مستوى المرحلة) ولا تتوفر بيانات خام فردية لكل أصل تتيح إعادة الاحتساب من الصفر.",
]))
story.append(Spacer(1, 6))

story.append(Paragraph(ar("6.  الاعتماد والتوقيع"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p(
    "تمت مراجعة هذا السجل من مكتب إدارة البيانات، وتم التحقق من مطابقة البيانات الواردة "
    "فيه لمحتوى تقرير DC.C.4.1 دون أي إضافة أو حذف أو تعديل.", body_style, FULL_W))
story.append(Spacer(1, 8))

approval_headers = ["صاحب الصلاحية", "المسمى الوظيفي", "التوقيع", "التاريخ"]
approval_row = ["________________", "مدير مكتب إدارة البيانات", "________________", "________________"]
approval_head_cells = [Paragraph(ar(h), head_cell_style) for h in reversed(approval_headers)]
approval_data_cells = [Paragraph(ar(v), ParagraphStyle("AppCell", fontName="Arabic", fontSize=9, alignment=1)) for v in reversed(approval_row)]
approval_tbl = Table([approval_head_cells, approval_data_cells], colWidths=[43.5 * mm] * 4)
approval_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 8),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
]))
story.append(approval_tbl)

doc.build(story)
print("Saved:", OUT_PATH)
