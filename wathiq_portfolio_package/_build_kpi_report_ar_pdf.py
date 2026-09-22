# -*- coding: utf-8 -*-
"""Builds the Arabic PDF companion to KPI_Supporting_Data_Report.xlsx (Wathiq identity).

Same content/sections as the Arabic Excel version, rendered as PDF with proper
Arabic shaping + right-to-left layout. Overwrites the existing PDF path in place.
No KPI values, calculations, or evidence sources changed from the Arabic Excel build.
"""
import arabic_reshaper
from bidi.algorithm import get_display

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUT_PATH = "01_KPI_Supporting_Data_Report/KPI_Supporting_Data_Report.pdf"

pdfmetrics.registerFont(TTFont("Arabic", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arabic-Bold", r"C:\Windows\Fonts\arialbd.ttf"))

NAVY = colors.HexColor("#1F2A44")
GOLD = colors.HexColor("#AB8654")
LIGHT_GREY = colors.HexColor("#F2F2F2")
GREEN = colors.HexColor("#1F6F43")


def ar(text):
    """Reshape + bidi-reorder Arabic (or mixed Arabic/Latin) text for PDF rendering."""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped, base_dir="R")


title_style = ParagraphStyle("TitleBar", fontName="Arabic-Bold", fontSize=17, leading=22,
                              textColor=colors.white, alignment=2)
subtitle_bar_style = ParagraphStyle("SubtitleBar", fontName="Arabic-Bold", fontSize=10.5, leading=15,
                                      textColor=colors.white, alignment=2)
report_title_style = ParagraphStyle("ReportTitle", fontName="Arabic-Bold", fontSize=13.5, leading=18,
                                      textColor=NAVY, alignment=2)
section_style = ParagraphStyle("Section", fontName="Arabic-Bold", fontSize=12, leading=16,
                                 textColor=NAVY, alignment=2)
meta_label_style = ParagraphStyle("MetaLabel", fontName="Arabic-Bold", fontSize=9.5,
                                    textColor=colors.HexColor("#595959"), alignment=2)
meta_value_style = ParagraphStyle("MetaValue", fontName="Arabic", fontSize=9.5,
                                    textColor=colors.HexColor("#262626"), alignment=2)
body_style = ParagraphStyle("Body", fontName="Arabic", fontSize=9.5, leading=15,
                              textColor=colors.HexColor("#262626"), alignment=2)
provenance_style = ParagraphStyle("Provenance", fontName="Arabic", fontSize=9, leading=14,
                                    textColor=colors.HexColor("#595959"), alignment=2)
cell_style = ParagraphStyle("Cell", fontName="Arabic", fontSize=8.6, leading=12, alignment=2,
                              textColor=colors.HexColor("#262626"))
cell_bold_navy = ParagraphStyle("CellBoldNavy", parent=cell_style, fontName="Arabic-Bold", textColor=NAVY)
cell_value_style = ParagraphStyle("CellValue", parent=cell_style, fontName="Arabic-Bold", textColor=GREEN,
                                    alignment=1)
head_cell_style = ParagraphStyle("HeadCell", fontName="Arabic-Bold", fontSize=10, alignment=1,
                                   textColor=colors.white)

# ---- Preserved KPI values (identical to the Arabic Excel build) ----
KPIS = [
    (
        "نسبة تغطية المراجعة",
        "نسبة مجموعات البيانات المصنفة التي شملتها دورة المراجعة الحالية من إجمالي الأصول المسجَّلة.",
        "DC.C.3.4 – تقرير مراجعة تصنيف البيانات",
        "(عدد الأصول التي تمت مراجعتها ÷ إجمالي عدد الأصول) × 100",
        "100%",
    ),
    (
        "الأصول التي تمت مراجعتها",
        "إجمالي عدد الأصول البيانية (مجموعات البيانات والسجلات) التي جرت مراجعتها ضمن دورة المراجعة.",
        "DC.C.3.4 – تقرير مراجعة تصنيف البيانات",
        "عدّ مباشر لعدد الأصول التي خضعت لدورة المراجعة",
        "30",
    ),
    (
        "تغييرات التصنيف",
        "عدد الأصول التي عُدِّل مستوى تصنيفها كنتيجة لعملية المراجعة.",
        "DC.C.3.4 – تقرير مراجعة تصنيف البيانات",
        "عدّ الأصول التي صدر بشأنها قرار تعديل/تخفيض ضمن نتائج المراجعة",
        "3",
    ),
    (
        "مدة المراجعة",
        "إجمالي الفترة الزمنية اللازمة لإنجاز دورة المراجعة الكاملة من بدايتها حتى إغلاقها.",
        "DC.C.3.4 – تقرير مراجعة تصنيف البيانات",
        "تاريخ إقفال الدورة (15 يونيو 2026) − تاريخ بدء الدورة (1 مايو 2026)",
        "6 أسابيع",
    ),
    (
        "مشاركة ملاك البيانات",
        "عدد ملاك البيانات الذين شاركوا فعلياً في دورة المراجعة عبر مختلف الإدارات.",
        "DC.C.3.4 – تقرير مراجعة تصنيف البيانات",
        "عدّ مباشر لعدد ملاك البيانات المشاركين فعلياً في الدورة",
        "12",
    ),
]

SOURCE_ROWS = [
    ("نسبة تغطية المراجعة", "100%", "DC.C.3.4 – تقرير مراجعة تصنيف البيانات"),
    ("الأصول التي تمت مراجعتها", "30", "DC.C.3.4 – تقرير مراجعة تصنيف البيانات"),
    ("تغييرات التصنيف", "3", "DC.C.3.4 – تقرير مراجعة تصنيف البيانات"),
    ("مدة المراجعة", "6 أسابيع", "DC.C.3.4 – تقرير مراجعة تصنيف البيانات"),
    ("مشاركة ملاك البيانات", "12", "DC.C.3.4 – تقرير مراجعة تصنيف البيانات"),
]

doc = SimpleDocTemplate(
    OUT_PATH, pagesize=landscape(A4),
    leftMargin=18 * mm, rightMargin=18 * mm, topMargin=14 * mm, bottomMargin=14 * mm,
)
story = []

# ---- Title banner ----
title_tbl = Table(
    [[Paragraph(ar("منصة ذكية لإدارة وقياس الامتثال لمتطلبات المكتب الوطني لإدارة البيانات (NDMO)"), subtitle_bar_style)],
     [Paragraph(ar("تقرير المؤشرات الداعم لإدارة ومراقبة تصنيف البيانات"), title_style)]],
    colWidths=[doc.width],
)
title_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), NAVY),
    ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ("TOPPADDING", (0, 0), (-1, 0), 4),
    ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
    ("TOPPADDING", (0, -1), (-1, -1), 2),
    ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
]))
story.append(title_tbl)
story.append(Spacer(1, 8))
story.append(Paragraph(ar("تقرير المؤشرات — البيانات الداعمة لتصنيف البيانات"), report_title_style))
story.append(Spacer(1, 10))

# ---- Meta block ----
meta_rows = [
    ("الجهة", "هيئة الخدمات الحكومية الذكية (SGSA)"),
    ("القسم", "مكتب إدارة البيانات"),
    ("النطاق", "تصنيف البيانات"),
    ("الإطار المرجعي", "إطار حوكمة البيانات الوطني (NDMO)"),
    ("المتطلبات المدعومة", "DC.M.2   •   DC.M.3   •   DC.C.4.1   •   DC.M.12"),
    ("دورة المراجعة", "1 مايو 2026 – 15 يونيو 2026 (6 أسابيع)"),
    ("مصدر البيانات", "DC.C.3.4 – تقرير مراجعة تصنيف البيانات"),
]
meta_data = [[Paragraph(ar(v), meta_value_style), Paragraph(ar(l), meta_label_style)] for l, v in meta_rows]
meta_tbl = Table(meta_data, colWidths=[doc.width - 45 * mm, 45 * mm])
meta_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
story.append(meta_tbl)
story.append(Spacer(1, 12))

# ---- الغرض من التقرير ----
story.append(Paragraph(ar("الغرض من التقرير"), section_style))
story.append(Spacer(1, 4))
purpose_text = (
    "يهدف هذا التقرير إلى تقديم بيانات المؤشرات الداعمة لعملية مراقبة تصنيف البيانات، "
    "استنادًا إلى نتائج دورة مراجعة تصنيف البيانات الموثقة، ويدعم بشكل "
    "مباشر متطلبات DC.M.2 وDC.M.3 وDC.C.4.1 وDC.M.12."
)
story.append(Paragraph(ar(purpose_text), body_style))
story.append(Spacer(1, 14))

# ---- KPI table (columns reversed for RTL visual order: rightmost = اسم المؤشر) ----
story.append(Paragraph(ar("تقرير المؤشرات (KPI)"), section_style))
story.append(Spacer(1, 6))

header_ar = ["اسم المؤشر", "الوصف", "مصدر البيانات", "طريقة الحساب", "القيمة"]
header_row = [Paragraph(ar(h), head_cell_style) for h in reversed(header_ar)]
data = [header_row]
for name, desc, source, calc, value in KPIS:
    row = [
        Paragraph(ar(value), cell_value_style),
        Paragraph(ar(calc), cell_style),
        Paragraph(ar(source), cell_style),
        Paragraph(ar(desc), cell_style),
        Paragraph(ar(name), cell_bold_navy),
    ]
    data.append(row)

col_widths = list(reversed([40 * mm, 90 * mm, 60 * mm, 70 * mm, 22 * mm]))
kpi_tbl = Table(data, colWidths=col_widths, repeatRows=1)
style_cmds = [
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
]
for i in range(1, len(data)):
    if i % 2 == 0:
        style_cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GREY))
kpi_tbl.setStyle(TableStyle(style_cmds))
story.append(kpi_tbl)
story.append(Spacer(1, 16))

# ---- مصادر بيانات المؤشرات ----
story.append(Paragraph(ar("مصادر بيانات المؤشرات"), section_style))
story.append(Spacer(1, 6))

src_header_ar = ["المؤشر", "القيمة", "مصدر البيانات"]
src_header_row = [Paragraph(ar(h), head_cell_style) for h in reversed(src_header_ar)]
src_data = [src_header_row]
for kpi_name, value, source in SOURCE_ROWS:
    src_data.append([
        Paragraph(ar(source), cell_style),
        Paragraph(ar(value), cell_value_style),
        Paragraph(ar(kpi_name), cell_bold_navy),
    ])
src_col_widths = list(reversed([60 * mm, 30 * mm, 60 * mm]))
src_tbl = Table(src_data, colWidths=src_col_widths, repeatRows=1)
src_style_cmds = [
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
]
for i in range(1, len(src_data)):
    if i % 2 == 0:
        src_style_cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GREY))
src_tbl.setStyle(TableStyle(src_style_cmds))
story.append(src_tbl)
story.append(Spacer(1, 16))

# ---- مرجعية البيانات ----
story.append(Paragraph(ar("مرجعية البيانات"), section_style))
story.append(Spacer(1, 4))
provenance_text = (
    "جميع قيم المؤشرات الواردة في هذا التقرير مستخرجة من النتائج الموثقة في تقرير مراجعة "
    "تصنيف البيانات (DC.C.3.4)، ولم يُستخدم أي مصدر بيانات آخر في إعداد هذا التقرير."
)
story.append(Paragraph(ar(provenance_text), provenance_style))

doc.build(story)
print("Saved (overwritten in place):", OUT_PATH)
