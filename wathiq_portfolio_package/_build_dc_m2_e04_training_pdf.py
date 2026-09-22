# -*- coding: utf-8 -*-
"""PDF twin of DC.M.2-E04_Data_Classification_Awareness_and_Training_Record.docx.
Same content, Wathiq/SGSA identity, RTL. Independent file, no other file touched.
"""
import arabic_reshaper
from bidi.algorithm import get_display

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUT_PATH = "05_DC_M2_Draft_Evidence/DC.M.2-E04_Data_Classification_Awareness_and_Training_Record.pdf"

pdfmetrics.registerFont(TTFont("Arabic", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arabic-Bold", r"C:\Windows\Fonts\arialbd.ttf"))

NAVY = colors.HexColor("#1F2A44")
GOLD = colors.HexColor("#AB8654")
LIGHT_GREY = colors.HexColor("#F2F2F2")
GREEN = colors.HexColor("#1F6F43")
AMBER = colors.HexColor("#8A6D00")
GREY = colors.HexColor("#595959")


def ar(text):
    return get_display(arabic_reshaper.reshape(text), base_dir="R")


title_style = ParagraphStyle("TitleBar", fontName="Arabic-Bold", fontSize=17, leading=22, textColor=colors.white, alignment=2)
subtitle_bar_style = ParagraphStyle("SubtitleBar", fontName="Arabic-Bold", fontSize=10.5, leading=15, textColor=colors.white, alignment=2)
report_title_style = ParagraphStyle("ReportTitle", fontName="Arabic-Bold", fontSize=14.5, leading=19, textColor=NAVY, alignment=2)
draft_style = ParagraphStyle("Draft", fontName="Arabic", fontSize=10.5, leading=14, textColor=GOLD, alignment=2)
section_style = ParagraphStyle("Section", fontName="Arabic-Bold", fontSize=12.5, leading=16, textColor=NAVY, alignment=2, spaceBefore=6)
meta_label_style = ParagraphStyle("MetaLabel", fontName="Arabic-Bold", fontSize=9.5, textColor=GREY, alignment=2)
meta_value_style = ParagraphStyle("MetaValue", fontName="Arabic", fontSize=9.5, textColor=colors.HexColor("#262626"), alignment=2)
body_style = ParagraphStyle("Body", fontName="Arabic", fontSize=9.5, leading=15, textColor=colors.HexColor("#262626"), alignment=2)
bullet_style = ParagraphStyle("Bullet", fontName="Arabic", fontSize=9.3, leading=14, textColor=colors.HexColor("#262626"), alignment=2, spaceAfter=4)
note_style = ParagraphStyle("Note", fontName="Arabic", fontSize=8, leading=12, textColor=GREY, alignment=2)
cell_style = ParagraphStyle("Cell", fontName="Arabic", fontSize=8.6, leading=12, alignment=2, textColor=colors.HexColor("#262626"))
cell_center = ParagraphStyle("CellCenter", parent=cell_style, alignment=1)
cell_bold_navy = ParagraphStyle("CellBoldNavy", parent=cell_style, fontName="Arabic-Bold", textColor=NAVY, alignment=1)
head_cell_style = ParagraphStyle("HeadCell", fontName="Arabic-Bold", fontSize=9.5, alignment=1, textColor=colors.white)


def status_cell_style(v):
    color = GREEN if v == "مكتمل" else AMBER
    return ParagraphStyle("Status", parent=cell_style, fontName="Arabic-Bold", alignment=1, textColor=color)


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


def rtl_table(headers_ar, rows, col_widths_ltr, center_cols=None, status_col=None):
    center_cols = center_cols or []
    header_row = [Paragraph(ar(h), head_cell_style) for h in reversed(headers_ar)]
    data = [header_row]
    for row_vals in rows:
        cells = []
        for i, v in enumerate(row_vals):
            if status_col is not None and i == status_col:
                cells.append(Paragraph(ar(str(v)), status_cell_style(v)))
            elif i == 0:
                cells.append(Paragraph(ar(str(v)), cell_bold_navy))
            elif i in center_cols:
                cells.append(Paragraph(ar(str(v)), cell_center))
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
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GREY))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


doc = SimpleDocTemplate(
    OUT_PATH, pagesize=landscape(A4),
    leftMargin=18 * mm, rightMargin=18 * mm, topMargin=14 * mm, bottomMargin=14 * mm,
)
story = []

# ---- Cover / banner ----
title_tbl = Table(
    [[Paragraph(ar("منصة ذكية لإدارة وقياس الامتثال لمتطلبات المكتب الوطني لإدارة البيانات (NDMO)"), subtitle_bar_style)],
     [Paragraph(ar("سجل ورش التوعية والتدريب الخاصة بتصنيف البيانات"), title_style)]],
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
story.append(Paragraph(ar("سجل ورش التوعية والتدريب الخاصة بتصنيف البيانات"), report_title_style))
story.append(Paragraph(ar("دليل داعم — DC.M.2-E04"), draft_style))
story.append(Spacer(1, 10))

meta_rows = [
    ("الجهة", "هيئة الخدمات الحكومية الذكية (SGSA)"),
    ("القسم", "مكتب إدارة البيانات"),
    ("المنصة", ""),
    ("الإطار المرجعي", "إطار حوكمة البيانات الوطني (NDMO)"),
    ("رمز الدليل", "DC.M.2-E04"),
    ("المتطلب المرتبط", "DC.M.2 — تنفيذ خطة تصنيف البيانات وخارطة الطريق"),
    ("اسم الدليل", "سجل ورش التوعية والتدريب الخاصة بتصنيف البيانات"),
    ("الإصدار", "1.0"),
    ("التاريخ", "يونيو 2026"),
    ("حالة الوثيقة", "جاهزة للمراجعة"),
]
meta_data = [[Paragraph(ar(v), meta_value_style), Paragraph(ar(l), meta_label_style)] for l, v in meta_rows]
meta_tbl = Table(meta_data, colWidths=[doc.width - 45 * mm, 45 * mm])
meta_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
story.append(meta_tbl)
story.append(PageBreak())

# ---- القسم الأول ----
story.append(Paragraph(ar("القسم الأول: ملخص النشاط"), section_style))
story.append(Spacer(1, 4))
story.append(Paragraph(ar(
    "نفَّذت الهيئة برنامج توعية داخلياً لدعم تنفيذ خطة تصنيف البيانات ورفع مستوى الوعي "
    "المؤسسي بمتطلبات التصنيف لدى منسوبيها، ضمن أنشطة المرحلة الأولى من خطة تصنيف البيانات."
), body_style))
story.append(Spacer(1, 14))

# ---- القسم الثاني ----
story.append(Paragraph(ar("القسم الثاني: سجل ورش التوعية"), section_style))
story.append(Spacer(1, 6))
story.append(rtl_table(
    ["رقم الورشة", "اسم الورشة", "التاريخ", "الفئة المستهدفة", "عدد المشاركين", "الحالة"],
    WORKSHOPS,
    [16 * mm, 62 * mm, 24 * mm, 30 * mm, 24 * mm, 24 * mm],
    center_cols=[0, 4],
    status_col=5,
))
story.append(Spacer(1, 16))

# ---- القسم الثالث ----
story.append(Paragraph(ar("القسم الثالث: المواد التدريبية المستخدمة"), section_style))
story.append(Spacer(1, 6))
story.append(rtl_table(["اسم المادة", "الوصف"], MATERIALS, [40 * mm, 140 * mm]))
story.append(Spacer(1, 16))

# ---- القسم الرابع ----
story.append(Paragraph(ar("القسم الرابع: النتائج"), section_style))
story.append(Spacer(1, 4))
for r in RESULTS:
    story.append(Paragraph(ar("•  " + r), bullet_style))
story.append(Spacer(1, 16))

# ---- القسم الخامس ----
story.append(Paragraph(ar("القسم الخامس: الاعتماد"), section_style))
story.append(Spacer(1, 6))
approval_headers = ["المسمى الوظيفي", "الاسم", "التوقيع", "التاريخ"]
approval_row = ["مدير مكتب إدارة البيانات", "", "", ""]
approval_head_cells = [Paragraph(ar(h), head_cell_style) for h in reversed(approval_headers)]
approval_data_cells = [Paragraph(ar(v), ParagraphStyle("AppCell", fontName="Arabic", fontSize=9, alignment=1)) for v in reversed(approval_row)]
approval_tbl = Table([approval_head_cells, approval_data_cells], colWidths=[45 * mm] * 4)
approval_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 8),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
]))
story.append(approval_tbl)
story.append(Spacer(1, 14))
story.append(Paragraph(ar(
    "هذا الدليل مرفق تدقيق مستقل ضمن حزمة أدلة تصنيف البيانات الخاصة بهيئة الخدمات الحكومية الذكية (SGSA) الداعمة لمتطلب DC.M.2، ويستخدم "
    "لإثبات تنفيذ أنشطة التوعية والتدريب الخاصة بتصنيف البيانات."
), note_style))

doc.build(story)
print("Saved:", OUT_PATH)
