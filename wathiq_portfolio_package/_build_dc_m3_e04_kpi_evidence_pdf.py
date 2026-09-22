# -*- coding: utf-8 -*-
"""PDF twin of DC.M.3-E04_Compliance_Procedures_KPI_Evidence_Record.docx — same content,
same Wathiq/SGSA identity. Evidence Record (not a Calculation Record) for DC-KPI-04 (DC.M.3),
sourced exclusively from the real DC.M.4.docx follow-up report.

Long Arabic paragraphs are pre-wrapped manually (wrap_ar) before being handed to reportlab,
to avoid the reversed-line-order defect discovered and fixed in DC.M.3-E01/E02/E03.
"""
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

OUT_PATH = "06_DC_M3_KPI_Evidence/DC.M.3-E04_Compliance_Procedures_KPI_Evidence_Record.pdf"

pdfmetrics.registerFont(TTFont("Arabic", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arabic-Bold", r"C:\Windows\Fonts\arialbd.ttf"))

NAVY = colors.HexColor("#1F2A44")
GOLD = colors.HexColor("#AB8654")
LIGHT_GREY = colors.HexColor("#F2F2F2")
GREEN = colors.HexColor("#1F6F43")


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
report_title_style = ParagraphStyle("ReportTitle", fontName="Arabic-Bold", fontSize=13.5, leading=18, textColor=NAVY, alignment=2)
draft_style = ParagraphStyle("Draft", fontName="Arabic", fontSize=10, leading=13, textColor=GOLD, alignment=2)
section_style = ParagraphStyle("Section", fontName="Arabic-Bold", fontSize=12, leading=15, textColor=NAVY, alignment=2, spaceBefore=6)
meta_label_style = ParagraphStyle("MetaLabel", fontName="Arabic-Bold", fontSize=9, textColor=colors.HexColor("#595959"), alignment=2)
meta_value_style = ParagraphStyle("MetaValue", fontName="Arabic", fontSize=9, leading=13, textColor=colors.HexColor("#262626"), alignment=2)
body_style = ParagraphStyle("Body", fontName="Arabic", fontSize=9.5, leading=15, textColor=colors.HexColor("#262626"), alignment=2)
note_style = ParagraphStyle("Note", fontName="Arabic", fontSize=8, leading=12, textColor=colors.HexColor("#595959"), alignment=2, italic=1)
cell_style = ParagraphStyle("Cell", fontName="Arabic", fontSize=9, leading=12, alignment=2, textColor=colors.HexColor("#262626"))
cell_bold_navy = ParagraphStyle("CellBoldNavy", parent=cell_style, fontName="Arabic-Bold", textColor=NAVY)
cell_bold_green = ParagraphStyle("CellBoldGreen", parent=cell_style, fontName="Arabic-Bold", textColor=GREEN)
head_cell_style = ParagraphStyle("HeadCell", fontName="Arabic-Bold", fontSize=8.6, alignment=1, textColor=colors.white)


def rtl_table(headers_ar, rows, col_widths_ltr):
    header_row = [Paragraph(ar(h), head_cell_style) for h in reversed(headers_ar)]
    data = [header_row]
    for row_vals in rows:
        cells = []
        n = len(row_vals)
        for i, v in enumerate(row_vals):
            if i == 0:
                cells.append(Paragraph(ar(str(v)), cell_bold_navy))
            elif i == n - 1:
                st = ParagraphStyle("Src", parent=cell_style, italic=True)
                cells.append(Paragraph(ar(str(v)), st))
            else:
                cells.append(Paragraph(ar(str(v)), cell_bold_green))
        data.append(list(reversed(cells)))
    col_widths = list(reversed(col_widths_ltr))
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GREY))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


doc = SimpleDocTemplate(
    OUT_PATH, pagesize=A4,
    leftMargin=18 * mm, rightMargin=18 * mm, topMargin=14 * mm, bottomMargin=14 * mm,
)
story = []
FULL_W = doc.width


def meta_table_ar(rows, col_w=42 * mm):
    data = [
        [ar_p(v, meta_value_style, doc.width - col_w - 12), Paragraph(ar(l), meta_label_style)]
        for l, v in rows
    ]
    tbl = Table(data, colWidths=[doc.width - col_w, col_w])
    tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return tbl


# ---- Cover / banner ----
title_tbl = Table(
    [[Paragraph(ar("منصة ذكية لإدارة وقياس الامتثال لمتطلبات المكتب الوطني لإدارة البيانات (NDMO)"), subtitle_bar_style)],
     [Paragraph(ar("سجل إثبات مؤشر الالتزام بإجراءات تصنيف البيانات (DC-KPI-04)"), title_style)]],
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
story.append(Paragraph(ar("سجل إثبات مؤشر الالتزام بإجراءات تصنيف البيانات (DC-KPI-04)"), report_title_style))
story.append(Paragraph(ar("Compliance Procedures KPI Evidence Record"), draft_style))
story.append(Spacer(1, 10))

story.append(meta_table_ar([
    ("الجهة", "هيئة الخدمات الحكومية الذكية (SGSA)"),
    ("المنصة", ""),
    ("الإطار المرجعي", "إطار حوكمة البيانات الوطني (NDMO)"),
    ("رمز الدليل", "DC.M.3-E04"),
    ("المتطلب المرتبط", "DC.M.3 — تقرير مراقبة تنفيذ خطة تصنيف البيانات عبر مؤشرات الأداء الرئيسية"),
    ("المؤشر المرتبط", "DC-KPI-04 — نسبة الالتزام بإجراءات تصنيف البيانات"),
    ("الإصدار", "1.0"),
    ("التاريخ", "يونيو 2026"),
    ("حالة الوثيقة", "جاهزة للاعتماد"),
]))
story.append(PageBreak())

# ---- 1. المقدمة ----
story.append(Paragraph(ar("1.  المقدمة"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p(
    "يوثّق هذا السجل مصدر وقابلية تتبع القيمة الحالية لمؤشر الأداء الرئيسي DC-KPI-04 "
    "(نسبة الالتزام بإجراءات تصنيف البيانات)، حيث يذكر تقرير DC.M.3 — تقرير مراقبة "
    "تنفيذ خطة تصنيف البيانات عبر مؤشرات الأداء الرئيسية — أن القيمة الحالية لهذا "
    "المؤشر هي 88%.",
    body_style, FULL_W,
))
story.append(Spacer(1, 6))
story.append(ar_p(
    "المصدر المستخدم للتحقق من هذه القيمة هو DC.M.4 — تقرير متابعة تنفيذ خطة تصنيف "
    "البيانات، وهو تقرير رسمي ضمن مستودع الأدلة يحمل في بياناته حقلاً صريحاً – "
    "«مرجع مؤشرات الأداء: DC.M.3» – يربطه مباشرة بتقرير DC.M.3. لا يُعيد هذا "
    "السجل احتساب النسبة الواردة، بل يوثّق وجودها في المصدر الرسمي المذكور.",
    body_style, FULL_W,
))
story.append(Spacer(1, 14))

# ---- 2. بيانات المصدر ----
story.append(Paragraph(ar("2.  بيانات المصدر"), section_style))
story.append(Spacer(1, 4))
story.append(meta_table_ar([
    ("المصدر", "DC.M.4 — تقرير متابعة تنفيذ خطة تصنيف البيانات"),
    ("مرجع المؤشرات", "DC.M.3"),
    ("فترة القياس", "حسب دورة التقرير"),
    ("خط الأساس", "65%"),
    ("القيمة الحالية", "88%"),
]))
story.append(Spacer(1, 14))

# ---- 3. إثبات القيمة ----
story.append(Paragraph(ar("3.  إثبات القيمة"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p("يعرض الجدول التالي البيانات كما وردت حرفياً في DC.M.4:", body_style, FULL_W))
story.append(Spacer(1, 6))
story.append(rtl_table(
    ["البند", "القيمة", "المصدر"],
    [
        ("اسم المؤشر", "نسبة الالتزام بإجراءات تصنيف البيانات", "DC.M.4"),
        ("خط الأساس", "65%", "DC.M.4"),
        ("القيمة الحالية", "88%", "DC.M.4"),
        ("حالة المؤشر", "قريب من التحقيق", "DC.M.4"),
    ],
    [60 * mm, 65 * mm, 35 * mm],
))
story.append(Spacer(1, 16))

# ---- 4. حدود إعادة الاحتساب ----
story.append(Paragraph(ar("4.  حدود إعادة الاحتساب"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p(
    "لا يتضمن المصدر DC.M.4 عدد الحالات المفحوصة وعدد الحالات الملتزمة اللازمة لإعادة "
    "تطبيق معادلة المؤشر: عدد الحالات الملتزمة ÷ إجمالي الحالات المفحوصة × 100. لذلك "
    "يقتصر هذا السجل على إثبات القيمة الواردة وتتبع مصدرها الرسمي، ولا يقدم احتساباً "
    "مستقلاً للمؤشر.",
    body_style, FULL_W,
))
story.append(Spacer(1, 16))

# ---- 5. التحقق من المصادر ----
story.append(Paragraph(ar("5.  التحقق من المصادر"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p(
    "تمت مراجعة DC.M.12 للتحقق من إمكانية استخدامه كمصدر بديل، ولم يتم اعتماده لعدم "
    "ارتباطه بـ DC-KPI-04، حيث يخص مؤشرات مراجعة تصنيف مختلفة تحت DC.MQ.3.",
    body_style, FULL_W,
))
story.append(Spacer(1, 16))

# ---- 6. التحقق والاعتماد ----
story.append(Paragraph(ar("6.  التحقق والاعتماد"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p(
    "تمت مراجعة هذا السجل والتحقق من مطابقة البيانات الواردة فيه لمحتوى DC.M.4 دون "
    "إضافة أو حذف أو تعديل.",
    body_style, FULL_W,
))
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
story.append(Spacer(1, 12))
story.append(ar_p(
    "ملاحظة: هذا السجل دليل داعم مستقل ضمن حزمة أدلة تصنيف البيانات الخاصة بهيئة الخدمات الحكومية الذكية (SGSA)، أُعدّ لتوثيق مصدر "
    "وقابلية تتبع قيمة مؤشر DC-KPI-04 دون تعديل أي محتوى في تقرير DC.M.3 أو تقرير DC.M.4.",
    note_style, FULL_W,
))

doc.build(story)
print("Saved:", OUT_PATH)
