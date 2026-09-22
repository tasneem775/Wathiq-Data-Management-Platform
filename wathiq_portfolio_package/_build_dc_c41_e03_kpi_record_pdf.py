# -*- coding: utf-8 -*-
"""PDF twin of DC.C.4.1-E03_KPI-DC-03_Low_Impact_Data_Review_KPI_Calculation_Record.docx —
7-section compliance-audit template. Sourced exclusively from the real DC.C.3.2.docx and
DC.C.3.3.docx (Table 14)."""
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

OUT_PATH = "06_DC_C4_1_KPI_Evidence/DC.C.4.1-E03_KPI-DC-03_Low_Impact_Data_Review_KPI_Calculation_Record.pdf"

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
cell_style = ParagraphStyle("Cell", fontName="Arabic", fontSize=7.8, leading=11, alignment=2, textColor=colors.HexColor("#262626"))
cell_bold_navy = ParagraphStyle("CellBoldNavy", parent=cell_style, fontName="Arabic-Bold", textColor=NAVY, alignment=1)
head_cell_style = ParagraphStyle("HeadCell", fontName="Arabic-Bold", fontSize=8.4, alignment=1, textColor=colors.white)

DECISION_COLOR = {"الإبقاء كمقيّد": AMBER, "إعادة التصنيف إلى عام": GREEN}


def decision_style(v):
    return ParagraphStyle("Decision", parent=cell_style, fontName="Arabic-Bold", alignment=1, textColor=DECISION_COLOR.get(v, colors.HexColor("#262626")))


def rtl_table(headers_ar, rows, col_widths_ltr, status_col=None, first_center=True):
    header_row = [Paragraph(ar(h), head_cell_style) for h in reversed(headers_ar)]
    data = [header_row]
    for row_vals in rows:
        cells = []
        for i, v in enumerate(row_vals):
            if status_col is not None and i == status_col:
                cells.append(Paragraph(ar(str(v)), decision_style(str(v))))
            elif i == 0 and first_center:
                cells.append(Paragraph(ar(str(v)), cell_bold_navy))
            else:
                cells.append(Paragraph(ar(str(v)), cell_style))
        data.append(list(reversed(cells)))
    col_widths = list(reversed(col_widths_ltr))
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GREY))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


ASSETS = [
    (1, 9, "بيانات طلبات ومعاملات المستفيدين", "الإبقاء كمقيّد"),
    (2, 10, "بيانات الخدمات الحكومية الرقمية", "إعادة التصنيف إلى عام"),
    (3, 11, "بيانات الموردين والمتعاقدين", "الإبقاء كمقيّد"),
    (4, 14, "بيانات التدريب والتطوير الوظيفي", "الإبقاء كمقيّد"),
    (5, 16, "بيانات الحوادث التقنية وطلبات الدعم", "الإبقاء كمقيّد"),
    (6, 21, "سجلات المراسلات والخطابات الرسمية", "الإبقاء كمقيّد"),
    (7, 22, "سجلات الاجتماعات واللجان الحوكمية", "الإبقاء كمقيّد"),
    (8, 23, "سجلات التقارير الإدارية الدورية", "إعادة التصنيف إلى عام"),
    (9, 25, "سجلات الشكاوى والمقترحات", "الإبقاء كمقيّد"),
    (10, 27, "سجلات التراخيص والتصاريح القانونية", "إعادة التصنيف إلى عام"),
    (11, 29, "وثائق السياسات والإجراءات الداخلية", "الإبقاء كمقيّد"),
    (12, 30, "سجلات التغييرات والتحديثات التقنية", "الإبقاء كمقيّد"),
]
TOTAL_LOW_IMPACT = len(ASSETS)
REMAINED_RESTRICTED = sum(1 for *_, d in ASSETS if d == "الإبقاء كمقيّد")
RECLASSIFIED = sum(1 for *_, d in ASSETS if d == "إعادة التصنيف إلى عام")
KPI_VALUE = round(REMAINED_RESTRICTED / TOTAL_LOW_IMPACT * 100)

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
     [Paragraph(ar("سجل احتساب مؤشر مراجعة البيانات منخفضة الأثر (KPI-DC-03)"), title_style)]],
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
story.append(Paragraph(ar("سجل احتساب مؤشر مراجعة البيانات منخفضة الأثر (KPI-DC-03)"), report_title_style))
story.append(Paragraph(ar("Low-Impact Data Review KPI Calculation Record"), draft_style))
story.append(Spacer(1, 10))

story.append(Paragraph(ar("1.  بيانات الوثيقة"), section_style))
story.append(Spacer(1, 4))
story.append(meta_table_ar([
    ("الجهة", "هيئة الخدمات الحكومية الذكية (SGSA)"),
    ("المنصة", ""),
    ("الإطار المرجعي", "إطار حوكمة البيانات الوطني (NDMO)"),
    ("رمز الدليل", "DC.C.4.1-E03"),
    ("نوع الوثيقة", "Calculation Record"),
    ("المتطلب المرتبط", "DC.C.4.1 — تقرير مراقبة عمليات تصنيف البيانات عبر مؤشرات الأداء الرئيسية"),
    ("المؤشر المرتبط", "KPI-DC-03 — نسبة البيانات منخفضة الأثر المصنفة «مقيّد»"),
    ("الإصدار", "1.0"),
    ("التاريخ", "يونيو 2026"),
    ("حالة الوثيقة", "جاهزة للاعتماد"),
]))
story.append(PageBreak())

story.append(Paragraph(ar("2.  نطاق القياس"), section_style))
story.append(Spacer(1, 4))
story.append(meta_table_ar([
    ("نطاق الأصول محل المراجعة", "الأصول الاثنا عشر (12) المصنَّفة أصلاً «مقيّد» في تقرير تقييم الأثر (DC.C.3.2)، والتي خضعت جميعها دون استثناء لدراسة تفصيلية (تعارض نظامي + موازنة منافع/آثار) في تقرير DC.C.3.3."),
    ("فترة المراجعة", "الربع الثاني 2026 — كما ورد في تقرير DC.C.4.1"),
    ("تاريخ استخراج البيانات", "يونيو 2026 (تاريخ إصدار DC.C.3.2 وDC.C.3.3)"),
]))
story.append(Spacer(1, 10))

story.append(Paragraph(ar("3.  مصدر البيانات"), section_style))
story.append(Spacer(1, 4))
story.extend(bullets([
    "DC.C.3.2 — تقرير تقييم الأثر (تحديد الأصول الاثني عشر المصنَّفة أصلاً «مقيّد» ذات الأثر المنخفض).",
    "DC.C.3.3 — تقرير تقييم البيانات منخفضة الأثر (القرار النهائي لكل أصل من الأصول الاثني عشر).",
]))
story.append(PageBreak())

story.append(Paragraph(ar("4.  جدول البيانات المستخدمة"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p("يعرض الجدول التالي القرار النهائي لكل أصل من الأصول الاثني عشر، كما ورد حرفياً في تقرير DC.C.3.3:", body_style, FULL_W))
story.append(Spacer(1, 6))
asset_rows = [(a, b, name, decision) for a, b, name, decision in ASSETS]
story.append(rtl_table(
    ["م (DC.C.3.3)", "الرقم الأصلي", "اسم الأصل", "القرار النهائي"],
    asset_rows,
    [18 * mm, 18 * mm, 78 * mm, 46 * mm],
    status_col=3,
))
story.append(Spacer(1, 6))
story.append(ar_p(
    "ملاحظة تدقيق: لا يعرض هذا الجدول قائمة مستقلة «مُنشأة» للأصول التسعة الباقية على "
    "مقيّد؛ بل هو نسخ حرفي للجدول الكامل الوارد في DC.C.3.3 (القسم 7.2) لجميع الأصول "
    "الاثني عشر، والذي يتضمن أصلاً عمود القرار النهائي لكل صف. لم يُستخدم أي مصدر آخر "
    "غير DC.C.3.2 وDC.C.3.3 في هذا السجل.", note_style, FULL_W))
story.append(PageBreak())

story.append(Paragraph(ar("5.  تطبيق المعادلة"), section_style))
story.append(Spacer(1, 6))
story.append(rtl_table(
    ["البند", "القيمة"],
    [
        ("إجمالي الأصول منخفضة الأثر قبل المراجعة (DC.C.3.2)", str(TOTAL_LOW_IMPACT)),
        ("عدد الأصول التي بقيت مصنَّفة «مقيّد» بعد المراجعة (DC.C.3.3)", str(REMAINED_RESTRICTED)),
        ("عدد الأصول المُعاد تصنيفها إلى «عام» (DC.C.3.3)", str(RECLASSIFIED)),
        ("معادلة المؤشر", "عدد الأصول الباقية على مقيّد ÷ إجمالي الأصول منخفضة الأثر × 100"),
        ("تطبيق المعادلة", f"{REMAINED_RESTRICTED} ÷ {TOTAL_LOW_IMPACT} × 100"),
        ("القيمة النهائية للمؤشر", f"{KPI_VALUE}%"),
    ],
    [126 * mm, 48 * mm],
    first_center=False,
))
story.append(Spacer(1, 12))

story.append(Paragraph(ar("6.  النتيجة والتحقق مقابل DC.C.4.1"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p(
    f"القيمة الناتجة ({KPI_VALUE}%) مطابقة تماماً للقيمة المقيسة الواردة في بطاقة مؤشر "
    "KPI-DC-03 ضمن تقرير DC.C.4.1 (القسم 8 وبند 9.3: «75.0% (9 أصول بقيت مقيّدة من أصل "
    "12 أصلاً مقيّداً أولياً)»)، وللقيمة الواردة في جدول لوحة الأداء الإجمالية (القسم 10) "
    "وجدول التوافق مع متطلبات NDMO (القسم 14).", body_style, FULL_W))
story.append(Spacer(1, 6))
story.extend(bullets([
    "تم التحقق من أن الرقم التسلسلي الأصلي لكل أصل من الاثني عشر يطابق تصنيفه «مقيّد» الوارد في DC.C.3.2 (القسم 6.2)، دون أي أصل إضافي أو مفقود.",
    "الأصول الثلاثة المُعاد تصنيفها (الأرقام الأصلية 10 و23 و27) تطابق تماماً الأصول الثلاثة الواردة في سجل DC.C.5.1 كأصول «أُعيد تصنيفها من مقيّد إلى عام».",
]))
story.append(Spacer(1, 6))

story.append(Paragraph(ar("7.  الاعتماد والتوقيع"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p(
    "تمت مراجعة هذا السجل من مكتب إدارة البيانات، وتم التحقق من مطابقة البيانات الواردة "
    "فيه لمحتوى DC.C.3.2 وDC.C.3.3 دون أي إضافة أو حذف أو تعديل.", body_style, FULL_W))
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
