# -*- coding: utf-8 -*-
"""PDF twin of DC.M.3-E02_Data_Owner_Assignment_KPI_Calculation_Record.docx — same content,
same Wathiq/SGSA identity. Standalone supporting evidence record for DC-KPI-02 (DC.M.3),
sourced exclusively from the real DC.M.5.docx dataset registry.

Long Arabic paragraphs are pre-wrapped manually (wrap_ar) before being handed to reportlab,
to avoid the reversed-line-order defect that occurs when a whole multi-line bidi-reordered
string is handed to reportlab's Paragraph auto-wrap.
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

OUT_PATH = "06_DC_M3_KPI_Evidence/DC.M.3-E02_Data_Owner_Assignment_KPI_Calculation_Record.pdf"

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
cell_style = ParagraphStyle("Cell", fontName="Arabic", fontSize=8.2, leading=11, alignment=2, textColor=colors.HexColor("#262626"))
cell_bold_navy = ParagraphStyle("CellBoldNavy", parent=cell_style, fontName="Arabic-Bold", textColor=NAVY, alignment=1)
head_cell_style = ParagraphStyle("HeadCell", fontName="Arabic-Bold", fontSize=8.6, alignment=1, textColor=colors.white)


def rtl_table(headers_ar, rows, col_widths_ltr, status_col=None):
    header_row = [Paragraph(ar(h), head_cell_style) for h in reversed(headers_ar)]
    data = [header_row]
    for row_vals in rows:
        cells = []
        for i, v in enumerate(row_vals):
            if i == 0:
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


# ============ بيانات مصدرها الحرفي DC.M.5.docx (اسم مجموعة البيانات، مالك البيانات) ============
DATASETS_FROM_DC_M5 = [
    (1, "بيانات الخدمات الحكومية الرقمية", "مدير الخدمات الرقمية"),
    (2, "بيانات التقارير التشغيلية", "مدير التخطيط"),
    (3, "بيانات استطلاعات رأي المستفيدين", "مدير الجودة"),
    (4, "بيانات المستخدمين", "مدير الخدمات الرقمية"),
    (5, "بيانات طلبات المستفيدين", "مدير خدمات المستفيدين"),
    (6, "بيانات البلاغات والشكاوى", "مدير الجودة"),
    (7, "بيانات الموردين", "مدير المشتريات"),
    (8, "بيانات الأصول التقنية", "مدير تقنية المعلومات"),
    (9, "بيانات المراسلات الرسمية", "مدير الشؤون الإدارية"),
    (10, "بيانات الاجتماعات واللجان", "مدير الشؤون الإدارية"),
    (11, "بيانات الموظفين", "مدير الموارد البشرية"),
    (12, "بيانات الرواتب والمزايا", "المدير المالي"),
    (13, "بيانات العقود والاتفاقيات", "مدير المشتريات"),
    (14, "بيانات الصلاحيات وإدارة الهوية", "مسؤول أمن المعلومات"),
    (15, "بيانات المدفوعات المالية", "المدير المالي"),
    (16, "بيانات الميزانية التشغيلية", "المدير المالي"),
    (17, "بيانات التدقيق الداخلي", "مدير التدقيق الداخلي"),
    (18, "بيانات الهوية والتحقق الإلكتروني", "مسؤول أمن المعلومات"),
    (19, "بيانات التكامل مع الجهات الحكومية", "مدير تقنية المعلومات"),
    (20, "بيانات سجلات الأحداث الأمنية", "مسؤول أمن المعلومات"),
]
TOTAL_DATASETS = len(DATASETS_FROM_DC_M5)
OWNED_DATASETS = len(DATASETS_FROM_DC_M5)
KPI_VALUE = round(OWNED_DATASETS / TOTAL_DATASETS * 100)

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
     [Paragraph(ar("سجل احتساب مؤشر نسبة تعيين ملاك البيانات (DC-KPI-02)"), title_style)]],
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
story.append(Paragraph(ar("سجل احتساب مؤشر نسبة تعيين ملاك البيانات (DC-KPI-02)"), report_title_style))
story.append(Paragraph(ar("Data Owner Assignment KPI Calculation Record"), draft_style))
story.append(Spacer(1, 10))

story.append(meta_table_ar([
    ("الجهة", "هيئة الخدمات الحكومية الذكية (SGSA)"),
    ("المنصة", ""),
    ("الإطار المرجعي", "إطار حوكمة البيانات الوطني (NDMO)"),
    ("رمز الدليل", "DC.M.3-E02"),
    ("المتطلب المرتبط", "DC.M.3 — تقرير مراقبة تنفيذ خطة تصنيف البيانات عبر مؤشرات الأداء الرئيسية"),
    ("المؤشر المرتبط", "DC-KPI-02 — نسبة تعيين ملاك البيانات"),
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
    "DC-KPI-02 (نسبة تعيين ملاك البيانات)، الوارد في بطاقة المؤشر ضمن تقرير "
    "DC.M.3 — تقرير مراقبة تنفيذ خطة تصنيف البيانات عبر مؤشرات الأداء الرئيسية، "
    "والذي أظهر قيمة حالية قدرها 100% مقابل هدف 100%.",
    body_style, FULL_W,
))
story.append(Spacer(1, 6))
story.append(ar_p(
    "يعتمد هذا السجل حصراً على البيانات الفعلية الواردة في سجل DC.M.5 — القائمة الحالية "
    "لمجموعات البيانات المصنفة. لا يستخدم هذا السجل تقرير الجرد DC.C.3.1 ولا سجل ملاك "
    "البيانات ضمن حزمة أدلة تصنيف البيانات الخاصة بهيئة الخدمات الحكومية الذكية (SGSA) للمتطلب DC.M.2، إذ إن نطاق مؤشر DC-KPI-02 كما ورد "
    "حرفياً في بطاقته ضمن DC.M.3 مقتصر على «مجموعات البيانات» دون أي ذكر لكلمة «أصول» "
    "أو «سجلات»، وهو ما يطابق نطاق DC.M.5 حصراً (مجموعات بيانات فقط)، بخلاف DC.C.3.1 "
    "الذي يغطي نطاقاً أوسع (مجموعات بيانات وسجلات معاً).",
    body_style, FULL_W,
))
story.append(Spacer(1, 14))

# ---- 2. بيانات الاحتساب ----
story.append(Paragraph(ar("2.  بيانات الاحتساب"), section_style))
story.append(Spacer(1, 4))
story.append(meta_table_ar([
    ("مصدر البيانات المستخدم", "DC.M.5 — القائمة الحالية لمجموعات البيانات المصنفة (الإصدار 1.0، يونيو 2026)"),
    ("فترة القياس", "الربع الثاني 2026 (أبريل – يونيو 2026)"),
    ("نطاق القياس",
     "جميع مجموعات البيانات الواردة في سجل DC.M.5 حتى تاريخ إصداره (20 مجموعة بيانات)، "
     "التزاماً بنطاق مؤشر DC-KPI-02 كما ورد حرفياً في بطاقته («المجموعات» فقط)."),
    ("تاريخ استخراج البيانات", "يونيو 2026 (تاريخ إصدار DC.M.5)"),
]))
story.append(Spacer(1, 14))

# ---- 3. مجموعات البيانات وملاكها ----
story.append(Paragraph(ar("3.  مجموعات البيانات وملاكها (وفق سجل DC.M.5)"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p("يعرض الجدول التالي جميع مجموعات البيانات الـ20 الواردة في سجل DC.M.5 مع مالك البيانات المحدد لكل منها:", body_style, FULL_W))
story.append(Spacer(1, 6))
dataset_rows = [(f"{n:02d}", name, owner) for n, name, owner in DATASETS_FROM_DC_M5]
story.append(rtl_table(
    ["الرقم التسلسلي", "اسم مجموعة البيانات", "مالك البيانات"],
    dataset_rows,
    [26 * mm, 74 * mm, 64 * mm],
))
story.append(PageBreak())

# ---- 4. حساب المؤشر ----
story.append(Paragraph(ar("4.  حساب المؤشر"), section_style))
story.append(Spacer(1, 6))
story.append(rtl_table(
    ["البند", "القيمة"],
    [
        ("إجمالي مجموعات البيانات (وفق سجل DC.M.5)", str(TOTAL_DATASETS)),
        ("عدد المجموعات ذات المالك المحدد", str(OWNED_DATASETS)),
        ("معادلة المؤشر", "عدد المجموعات ذات المالك المحدد ÷ إجمالي المجموعات × 100"),
        ("تطبيق المعادلة", f"{OWNED_DATASETS} ÷ {TOTAL_DATASETS} × 100"),
        ("القيمة النهائية للمؤشر", f"{KPI_VALUE}%"),
    ],
    [126 * mm, 48 * mm],
))
story.append(Spacer(1, 8))
story.append(ar_p(
    f"القيمة الناتجة ({KPI_VALUE}%) مطابقة للقيمة الحالية الواردة في بطاقة مؤشر DC-KPI-02 "
    "ضمن تقرير DC.M.3.",
    body_style, FULL_W,
))
story.append(Spacer(1, 16))

# ---- 5. التحقق والاعتماد ----
story.append(Paragraph(ar("5.  التحقق والاعتماد"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p(
    "تمت مراجعة هذا السجل من مكتب إدارة البيانات، وتم التحقق من مطابقة أسماء مجموعات "
    "البيانات وملاكها الواردة فيه لمحتوى سجل DC.M.5 دون أي إضافة أو حذف أو تعديل.",
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
    "وطريقة احتساب مؤشر DC-KPI-02 دون تعديل أي محتوى في تقرير DC.M.3 أو سجل DC.M.5.",
    note_style, FULL_W,
))

doc.build(story)
print("Saved:", OUT_PATH)
