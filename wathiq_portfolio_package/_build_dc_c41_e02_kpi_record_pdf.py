# -*- coding: utf-8 -*-
"""PDF twin of DC.C.4.1-E02_KPI-DC-02_Classification_Distribution_KPI_Calculation_Record.docx
— 7-section compliance-audit template. Sourced exclusively from the real DC.C.3.2.docx and
DC.C.5.1.docx (Table 6)."""
import arabic_reshaper
from bidi.algorithm import get_display
from collections import Counter

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import stringWidth

OUT_PATH = "06_DC_C4_1_KPI_Evidence/DC.C.4.1-E02_KPI-DC-02_Classification_Distribution_KPI_Calculation_Record.pdf"

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
cell_style = ParagraphStyle("Cell", fontName="Arabic", fontSize=7.6, leading=10.5, alignment=2, textColor=colors.HexColor("#262626"))
cell_bold_navy = ParagraphStyle("CellBoldNavy", parent=cell_style, fontName="Arabic-Bold", textColor=NAVY, alignment=1)
head_cell_style = ParagraphStyle("HeadCell", fontName="Arabic-Bold", fontSize=8.6, alignment=1, textColor=colors.white)

CLASS_COLOR = {"سرّي للغاية": NAVY, "سرّي": AMBER, "مقيّد": AMBER, "عام": GREEN}


def class_style(v):
    return ParagraphStyle("Class", parent=cell_style, fontName="Arabic-Bold", alignment=1, textColor=CLASS_COLOR.get(v, colors.HexColor("#262626")))


def rtl_table(headers_ar, rows, col_widths_ltr, status_cols=None, font_size=None):
    hstyle, cstyle, bstyle = head_cell_style, cell_style, cell_bold_navy
    if font_size:
        hstyle = ParagraphStyle("HC2", parent=head_cell_style, fontSize=font_size + 0.8)
        cstyle = ParagraphStyle("C2", parent=cell_style, fontSize=font_size)
        bstyle = ParagraphStyle("B2", parent=cell_bold_navy, fontSize=font_size)
    status_cols = status_cols or []
    header_row = [Paragraph(ar(h), hstyle) for h in reversed(headers_ar)]
    data = [header_row]
    for row_vals in rows:
        cells = []
        for i, v in enumerate(row_vals):
            if i in status_cols:
                cells.append(Paragraph(ar(str(v)), class_style(str(v))))
            elif i == 0:
                cells.append(Paragraph(ar(str(v)), bstyle))
            else:
                cells.append(Paragraph(ar(str(v)), cstyle))
        data.append(list(reversed(cells)))
    col_widths = list(reversed(col_widths_ltr))
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GREY))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


ASSETS = [
    (1, "بيانات الهوية والتحقق الإلكتروني", "سرّي للغاية", "سرّي للغاية"),
    (2, "بيانات الأحداث والتنبيهات الأمنية", "سرّي للغاية", "سرّي للغاية"),
    (3, "بيانات الصلاحيات وإدارة الهوية", "سرّي للغاية", "سرّي للغاية"),
    (4, "بيانات التكامل مع الجهات الحكومية", "سرّي للغاية", "سرّي للغاية"),
    (5, "بيانات الرواتب والمزايا الوظيفية", "سرّي", "سرّي"),
    (6, "بيانات المدفوعات والمعاملات المالية", "سرّي", "سرّي"),
    (7, "بيانات الموظفين والملفات الوظيفية", "سرّي", "سرّي"),
    (8, "بيانات المستخدمين والمستفيدين", "سرّي", "سرّي"),
    (9, "بيانات طلبات ومعاملات المستفيدين", "مقيّد", "مقيّد"),
    (10, "بيانات الخدمات الحكومية الرقمية", "مقيّد", "عام"),
    (11, "بيانات الموردين والمتعاقدين", "مقيّد", "مقيّد"),
    (12, "بيانات الأصول والبنية التحتية التقنية", "سرّي", "سرّي"),
    (13, "بيانات الأهداف والخطط الاستراتيجية", "سرّي", "سرّي"),
    (14, "بيانات التدريب والتطوير الوظيفي", "مقيّد", "مقيّد"),
    (15, "بيانات استطلاعات رضا المستفيدين", "عام", "عام"),
    (16, "بيانات الحوادث التقنية وطلبات الدعم", "مقيّد", "مقيّد"),
    (17, "بيانات المحتوى الرقمي والموقع الإلكتروني", "عام", "عام"),
    (18, "بيانات التقارير والإحصاءات المنشورة", "عام", "عام"),
    (19, "سجلات العقود والاتفاقيات", "سرّي", "سرّي"),
    (20, "سجلات التدقيق الداخلي والرقابة", "سرّي", "سرّي"),
    (21, "سجلات المراسلات والخطابات الرسمية", "مقيّد", "مقيّد"),
    (22, "سجلات الاجتماعات واللجان الحوكمية", "مقيّد", "مقيّد"),
    (23, "سجلات التقارير الإدارية الدورية", "مقيّد", "عام"),
    (24, "سجلات فعاليات الهيئة وأحداثها", "عام", "عام"),
    (25, "سجلات الشكاوى والمقترحات", "مقيّد", "مقيّد"),
    (26, "سجلات قرارات وتوجيهات الإدارة العليا", "سرّي", "سرّي"),
    (27, "سجلات التراخيص والتصاريح القانونية", "مقيّد", "عام"),
    (28, "سجلات النسخ الاحتياطي واسترجاع البيانات", "سرّي", "سرّي"),
    (29, "وثائق السياسات والإجراءات الداخلية", "مقيّد", "مقيّد"),
    (30, "سجلات التغييرات والتحديثات التقنية", "مقيّد", "مقيّد"),
]
TOTAL_ASSETS = len(ASSETS)
dist = Counter(level_after for _, _, _, level_after in ASSETS)
DIST_ORDER = ["سرّي للغاية", "سرّي", "مقيّد", "عام"]


def pct(n):
    return round(n / TOTAL_ASSETS * 1000) / 10


doc = SimpleDocTemplate(
    OUT_PATH, pagesize=A4,
    leftMargin=16 * mm, rightMargin=16 * mm, topMargin=14 * mm, bottomMargin=14 * mm,
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


def bullets(items):
    out = []
    for it in items:
        out.append(ar_p("•  " + it, bullet_style, FULL_W - 10))
        out.append(Spacer(1, 3))
    return out


title_tbl = Table(
    [[Paragraph(ar("منصة ذكية لإدارة وقياس الامتثال لمتطلبات المكتب الوطني لإدارة البيانات (NDMO)"), subtitle_bar_style)],
     [Paragraph(ar("سجل احتساب توزيع الأصول حسب مستوى التصنيف (KPI-DC-02)"), title_style)]],
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
story.append(Paragraph(ar("سجل احتساب توزيع الأصول حسب مستوى التصنيف (KPI-DC-02)"), report_title_style))
story.append(Paragraph(ar("Classification Distribution KPI Calculation Record"), draft_style))
story.append(Spacer(1, 10))

story.append(Paragraph(ar("1.  بيانات الوثيقة"), section_style))
story.append(Spacer(1, 4))
story.append(meta_table_ar([
    ("الجهة", "هيئة الخدمات الحكومية الذكية (SGSA)"),
    ("المنصة", ""),
    ("الإطار المرجعي", "إطار حوكمة البيانات الوطني (NDMO)"),
    ("رمز الدليل", "DC.C.4.1-E02"),
    ("نوع الوثيقة", "Calculation Record"),
    ("المتطلب المرتبط", "DC.C.4.1 — تقرير مراقبة عمليات تصنيف البيانات عبر مؤشرات الأداء الرئيسية"),
    ("المؤشر المرتبط", "KPI-DC-02 — نسبة الأصول المصنفة بكل مستوى تصنيف"),
    ("الإصدار", "1.0"),
    ("التاريخ", "يونيو 2026"),
    ("حالة الوثيقة", "جاهزة للاعتماد"),
]))
story.append(PageBreak())

story.append(Paragraph(ar("2.  نطاق القياس"), section_style))
story.append(Spacer(1, 4))
story.append(meta_table_ar([
    ("فترة القياس", "الربع الثاني 2026 (أبريل – يونيو 2026) — كما ورد في تقرير DC.C.4.1"),
    ("نطاق القياس", "جميع الأصول البيانية الثلاثين (30) بمستوى تصنيفها النهائي (المعتمد أثناء المراجعة) كما ورد في سجل DC.C.5.1، وهو السجل الذي يدمج نتائج DC.C.3.2 مع قرارات إعادة التصنيف الواردة في DC.C.3.3."),
    ("تاريخ استخراج البيانات", "يونيو 2026 (تاريخ إصدار DC.C.3.2 وDC.C.5.1)"),
]))
story.append(Spacer(1, 10))

story.append(Paragraph(ar("3.  مصدر البيانات"), section_style))
story.append(Spacer(1, 4))
story.extend(bullets([
    "DC.C.3.2 — تقرير تقييم الأثر (مستوى التصنيف الناتج/الممنوح أصلاً لكل أصل، قبل مراجعة إعادة التصنيف).",
    "DC.C.5.1 — سجل البيانات (السجل الموحّد الذي يثبت لكل أصل مستوى التصنيف الممنوح ومستوى التصنيف المعتمد أثناء المراجعة).",
    "لم تُستخدم بيانات DC.M.7 كمصدر لقيمة هذا المؤشر (انظر ملاحظة التدقيق في القسم 4)، رغم إشارة DC.C.4.1 إليه كمرجع عام.",
]))
story.append(PageBreak())

story.append(Paragraph(ar("4.  جدول البيانات المستخدمة"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p("يعرض الجدول التالي جميع الأصول البيانية الثلاثين مع مستوى التصنيف الممنوح أصلاً (DC.C.3.2) ومستوى التصنيف المعتمد أثناء المراجعة (DC.C.5.1)، مرتبة حسب الرقم التسلسلي (م):", body_style, FULL_W))
story.append(Spacer(1, 6))
asset_rows = [(n, name, granted, final) for n, name, granted, final in ASSETS]
story.append(rtl_table(
    ["م", "اسم الأصل", "التصنيف الممنوح", "التصنيف المعتمد"],
    asset_rows,
    [7 * mm, 62 * mm, 34 * mm, 34 * mm],
    status_cols=[2, 3],
))
story.append(Spacer(1, 6))
story.append(ar_p(
    "ملاحظة تدقيق: الأصول رقم 10 و23 و27 هي الأصول الثلاثة التي أُعيد تصنيفها من «مقيّد» "
    "إلى «عام» بموجب مراجعة DC.C.3.3. يعرض فهرس البيانات المؤسسي (DC.M.7) تصنيف هذه "
    "الأصول الثلاثة كما كانت قبل تلك المراجعة، لأن تحديث الفهرس لم يواكب تاريخ اعتماد "
    "إعادة التصنيف؛ لذلك اعتُمد عمود «مستوى التصنيف المعتمد أثناء المراجعة» في DC.C.5.1 "
    "حصراً كمصدر للقيمة النهائية، تفادياً للتعارض، وتماشياً مع التوضيح الوارد صراحة في "
    "تقرير DC.C.4.1 (بند 9.2).", note_style, FULL_W))
story.append(PageBreak())

story.append(Paragraph(ar("5.  تطبيق المعادلة"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p("معادلة كل مستوى: (عدد الأصول بمستوى X ÷ إجمالي الأصول المصنَّفة) × 100", body_style, FULL_W))
story.append(Spacer(1, 6))
calc_rows = []
for level in DIST_ORDER:
    n = dist.get(level, 0)
    calc_rows.append((level, str(n), f"{n} ÷ {TOTAL_ASSETS} × 100", f"{pct(n)}%"))
calc_rows.append(("الإجمالي", str(TOTAL_ASSETS), f"{TOTAL_ASSETS} ÷ {TOTAL_ASSETS} × 100", "100%"))
story.append(rtl_table(
    ["مستوى التصنيف", "عدد الأصول", "تطبيق المعادلة", "النسبة النهائية"],
    calc_rows,
    [32 * mm, 26 * mm, 62 * mm, 28 * mm],
    status_cols=[0, 3],
))
story.append(Spacer(1, 12))

story.append(Paragraph(ar("6.  النتيجة والتحقق مقابل DC.C.4.1"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p(
    "النسب الناتجة (سرّي للغاية 13.3%، سرّي 33.3%، مقيّد 30.0%، عام 23.3%) مطابقة تماماً "
    "للقيم الواردة في بطاقة مؤشر KPI-DC-02 ضمن تقرير DC.C.4.1 (القسم 8 وبند 9.2)، وللقيم "
    "الواردة في جدول توزيع مستويات التصنيف (القسم 9.2) وجدول لوحة الأداء الإجمالية (القسم 10).",
    body_style, FULL_W))
story.append(Spacer(1, 6))
story.extend(bullets([
    "تم التحقق من أن مجموع الأصول عبر المستويات الأربعة (4+10+9+7) يساوي 30، أي إجمالي عدد الأصول دون نقص أو زيادة.",
    "أي توزيع أولي (قبل مراجعة DC.C.3.3) لم يُستخدم كقيمة نهائية في هذا السجل؛ القيمة المعتمدة هي فقط التوزيع بعد المراجعة كما يطابق DC.C.4.1.",
]))
story.append(Spacer(1, 6))

story.append(Paragraph(ar("7.  الاعتماد والتوقيع"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p(
    "تمت مراجعة هذا السجل من مكتب إدارة البيانات، وتم التحقق من مطابقة البيانات الواردة "
    "فيه لمحتوى DC.C.3.2 وDC.C.5.1 دون أي إضافة أو حذف أو تعديل.", body_style, FULL_W))
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
