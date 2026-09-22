# -*- coding: utf-8 -*-
"""PDF twin of DC.M.3-E01_Data_Classification_KPI_Calculation_Record.docx — same content,
same Wathiq/SGSA identity. Standalone supporting evidence record for DC-KPI-01 (DC.M.3),
sourced exclusively from the real DC.M.5.docx dataset registry.

Note: long Arabic paragraphs are pre-wrapped manually (wrap_ar) before being handed to
reportlab. Pre-shaping+bidi-reordering a whole multi-line string and then letting
reportlab's Paragraph auto-wrap it reverses the visual line order (the bidi reorder is only
valid for a single line). Wrapping first, then reshaping each resulting line individually,
avoids that defect.
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

OUT_PATH = "06_DC_M3_KPI_Evidence/DC.M.3-E01_Data_Classification_KPI_Calculation_Record.pdf"

pdfmetrics.registerFont(TTFont("Arabic", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arabic-Bold", r"C:\Windows\Fonts\arialbd.ttf"))

NAVY = colors.HexColor("#1F2A44")
GOLD = colors.HexColor("#AB8654")
LIGHT_GREY = colors.HexColor("#F2F2F2")
GREEN = colors.HexColor("#1F6F43")
AMBER = colors.HexColor("#8A6D00")


def ar(text):
    return get_display(arabic_reshaper.reshape(text), base_dir="R")


def wrap_ar(text, font_name, font_size, max_width):
    """Wraps LOGICAL-order Arabic text to lines that fit max_width, then reshapes+bidi's
    each finished line separately, so reportlab never has to re-wrap already-visual-order text."""
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
cell_style = ParagraphStyle("Cell", fontName="Arabic", fontSize=7.6, leading=10.5, alignment=2, textColor=colors.HexColor("#262626"))
cell_bold_navy = ParagraphStyle("CellBoldNavy", parent=cell_style, fontName="Arabic-Bold", textColor=NAVY, alignment=1)
head_cell_style = ParagraphStyle("HeadCell", fontName="Arabic-Bold", fontSize=8.6, alignment=1, textColor=colors.white)


def status_style(v):
    color = GREEN if v == "مصنفة" else AMBER
    return ParagraphStyle("Status", parent=cell_style, fontName="Arabic-Bold", alignment=1, textColor=color)


def rtl_table(headers_ar, rows, col_widths_ltr, status_col=None, first_col_center=True):
    header_row = [Paragraph(ar(h), head_cell_style) for h in reversed(headers_ar)]
    data = [header_row]
    for row_vals in rows:
        cells = []
        for i, v in enumerate(row_vals):
            if status_col is not None and i == status_col:
                cells.append(Paragraph(ar(str(v)), status_style(v)))
            elif i == 0:
                st = cell_bold_navy if first_col_center else ParagraphStyle("C0", parent=cell_style, fontName="Arabic-Bold", textColor=NAVY)
                cells.append(Paragraph(ar(str(v)), st))
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


# ============ بيانات مصدرها الحرفي DC.M.5.docx ============
DATASETS_FROM_DC_M5 = [
    (1, "بيانات الخدمات الحكومية الرقمية", "عام"),
    (2, "بيانات التقارير التشغيلية", "عام"),
    (3, "بيانات استطلاعات رأي المستفيدين", "عام"),
    (4, "بيانات المستخدمين", "سرّي"),
    (5, "بيانات طلبات المستفيدين", "مقيّد"),
    (6, "بيانات البلاغات والشكاوى", "مقيّد"),
    (7, "بيانات الموردين", "مقيّد"),
    (8, "بيانات الأصول التقنية", "سرّي"),
    (9, "بيانات المراسلات الرسمية", "مقيّد"),
    (10, "بيانات الاجتماعات واللجان", "مقيّد"),
    (11, "بيانات الموظفين", "سرّي"),
    (12, "بيانات الرواتب والمزايا", "سرّي"),
    (13, "بيانات العقود والاتفاقيات", "سرّي"),
    (14, "بيانات الصلاحيات وإدارة الهوية", "سرّي"),
    (15, "بيانات المدفوعات المالية", "سرّي"),
    (16, "بيانات الميزانية التشغيلية", "سرّي"),
    (17, "بيانات التدقيق الداخلي", "سرّي"),
    (18, "بيانات الهوية والتحقق الإلكتروني", "سرّي للغاية"),
    (19, "بيانات التكامل مع الجهات الحكومية", "سرّي للغاية"),
    (20, "بيانات سجلات الأحداث الأمنية", "سرّي للغاية"),
]
TOTAL_DATASETS = len(DATASETS_FROM_DC_M5)
CLASSIFIED_DATASETS = len(DATASETS_FROM_DC_M5)
KPI_VALUE = round(CLASSIFIED_DATASETS / TOTAL_DATASETS * 100)

doc = SimpleDocTemplate(
    OUT_PATH, pagesize=A4,
    leftMargin=18 * mm, rightMargin=18 * mm, topMargin=14 * mm, bottomMargin=14 * mm,
)
story = []
FULL_W = doc.width
META_VALUE_COL_W = doc.width - 42 * mm
META_VALUE_TEXT_W = META_VALUE_COL_W - 12  # minus default cell left/right padding (~6pt each)


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
     [Paragraph(ar("سجل احتساب مؤشر نسبة مجموعات البيانات المصنفة (DC-KPI-01)"), title_style)]],
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
story.append(Paragraph(ar("سجل احتساب مؤشر نسبة مجموعات البيانات المصنفة (DC-KPI-01)"), report_title_style))
story.append(Paragraph(ar("Data Classification KPI Calculation Record"), draft_style))
story.append(Spacer(1, 10))

story.append(meta_table_ar([
    ("الجهة", "هيئة الخدمات الحكومية الذكية (SGSA)"),
    ("المنصة", ""),
    ("الإطار المرجعي", "إطار حوكمة البيانات الوطني (NDMO)"),
    ("رمز الدليل", "DC.M.3-E01"),
    ("المتطلب المرتبط", "DC.M.3 — تقرير مراقبة تنفيذ خطة تصنيف البيانات عبر مؤشرات الأداء الرئيسية"),
    ("المؤشر المرتبط", "DC-KPI-01 — نسبة مجموعات البيانات المصنفة"),
    ("الإصدار", "1.0"),
    ("التاريخ", "يونيو 2026"),
    ("حالة الوثيقة", "جاهزة للاعتماد"),
]))
story.append(PageBreak())

# ---- 1. المقدمة ----
story.append(Paragraph(ar("1.  المقدمة"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p(
    "يوثّق هذا السجل مصدر البيانات وطريقة احتساب القيمة الحالية لمؤشر الأداء الرئيسي "
    "DC-KPI-01 (نسبة مجموعات البيانات المصنفة)، الوارد في بطاقة المؤشر ضمن تقرير "
    "DC.M.3 — تقرير مراقبة تنفيذ خطة تصنيف البيانات عبر مؤشرات الأداء الرئيسية، "
    "والذي أظهر قيمة حالية قدرها 100% مقابل هدف 100%.",
    body_style, FULL_W,
))
story.append(Spacer(1, 6))
story.append(ar_p(
    "يعتمد هذا السجل حصراً على البيانات الفعلية الواردة في سجل مجموعات البيانات المصنفة "
    "(DC.M.5)، وهو الوثيقة التي يُشير إليها تقرير DC.M.3 نفسه كمصدر بيانات احتساب هذا "
    "المؤشر ضمن جدول «الوثائق الداعمة». لا يتضمن هذا السجل أي مجموعة بيانات أو رقم لم "
    "يرد في DC.M.5.",
    body_style, FULL_W,
))
story.append(Spacer(1, 14))

# ---- 2. بيانات الاحتساب ----
story.append(Paragraph(ar("2.  بيانات الاحتساب"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p(
    "يُعد هذا السجل وثيقة تحليلية داعمة لأغراض تتبع احتساب المؤشر، بينما يمثل سجل DC.M.5 "
    "مصدر البيانات الأساسي المستخدم في عملية الاحتساب.",
    body_style, FULL_W,
))
story.append(Spacer(1, 8))

story.append(meta_table_ar([
    ("مصدر البيانات المستخدم", "DC.M.5 — القائمة الحالية لمجموعات البيانات المصنفة (الإصدار 1.0، يونيو 2026)"),
    ("فترة القياس", "الربع الثاني 2026 (أبريل – يونيو 2026)"),
    ("نطاق القياس",
     "جميع مجموعات البيانات الواردة في سجل DC.M.5 حتى تاريخ إصداره (20 مجموعة بيانات). "
     "لا يشمل هذا الاحتساب تقرير الجرد الأوسع DC.C.3.1 (30 أصلاً بيانياً: 18 مجموعة بيانات "
     "و12 سجلاً)، التزاماً بالاعتماد الحصري على «سجل مجموعات البيانات» كما ورد نصاً في "
     "تقرير DC.M.3."),
    ("تاريخ استخراج البيانات", "يونيو 2026 (تاريخ إصدار DC.M.5)"),
]))
story.append(Spacer(1, 8))
story.append(ar_p(
    "ملاحظة منهجية: لا يتضمن سجل DC.M.5 معرّفات مستقلة لمجموعات البيانات؛ لذلك استُخدم "
    "الرقم التسلسلي (م) كما ورد في DC.M.5 نفسه كمعرّف تتبّع لكل مجموعة بيانات في الجدول التالي.",
    note_style, FULL_W,
))
story.append(Spacer(1, 14))

# ---- 3. سجل البيانات المستخدمة في الحساب ----
story.append(Paragraph(ar("3.  سجل البيانات المستخدمة في الحساب"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p("يعرض الجدول التالي جميع مجموعات البيانات الواردة في سجل DC.M.5 والمستخدمة في احتساب المؤشر:", body_style, FULL_W))
story.append(Spacer(1, 6))
dataset_rows = [
    (n, f"{n:02d}", name, "مصنفة", f"مستوى التصنيف وفق DC.M.5: {level}")
    for n, name, level in DATASETS_FROM_DC_M5
]
story.append(rtl_table(
    ["الرقم", "الرقم التسلسلي في سجل DC.M.5", "اسم مجموعة البيانات", "حالة التصنيف", "ملاحظات"],
    dataset_rows,
    [10 * mm, 24 * mm, 42 * mm, 20 * mm, 78 * mm],
    status_col=3,
))
story.append(PageBreak())

# ---- 4. حساب المؤشر ----
story.append(Paragraph(ar("4.  حساب المؤشر"), section_style))
story.append(Spacer(1, 6))
story.append(rtl_table(
    ["البند", "القيمة"],
    [
        ("إجمالي مجموعات البيانات (وفق سجل DC.M.5)", str(TOTAL_DATASETS)),
        ("عدد مجموعات البيانات المصنفة", str(CLASSIFIED_DATASETS)),
        ("معادلة المؤشر", "عدد مجموعات البيانات المصنفة ÷ إجمالي مجموعات البيانات × 100"),
        ("تطبيق المعادلة", f"{CLASSIFIED_DATASETS} ÷ {TOTAL_DATASETS} × 100"),
        ("القيمة النهائية للمؤشر", f"{KPI_VALUE}%"),
    ],
    [126 * mm, 48 * mm],
))
story.append(Spacer(1, 8))
story.append(ar_p(
    f"القيمة الناتجة ({KPI_VALUE}%) مطابقة للقيمة الحالية الواردة في بطاقة مؤشر DC-KPI-01 "
    "ضمن تقرير DC.M.3.",
    body_style, FULL_W,
))
story.append(Spacer(1, 16))

# ---- 5. التحقق والاعتماد ----
story.append(Paragraph(ar("5.  التحقق والاعتماد"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p(
    "تمت مراجعة هذا السجل من مكتب إدارة البيانات، وتم التحقق من مطابقة البيانات الواردة "
    "فيه لمحتوى سجل DC.M.5 دون أي إضافة أو حذف أو تعديل.",
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
    "ملاحظة: هذا السجل دليل داعم مستقل ضمن حزمة أدلة تصنيف البيانات الخاصة بهيئة الخدمات الحكومية الذكية (SGSA)، أُعدّ لتوثيق مصدر بيانات "
    "وطريقة احتساب مؤشر DC-KPI-01 دون تعديل أي محتوى في تقرير DC.M.3 أو سجل DC.M.5.",
    note_style, FULL_W,
))

doc.build(story)
print("Saved:", OUT_PATH)
