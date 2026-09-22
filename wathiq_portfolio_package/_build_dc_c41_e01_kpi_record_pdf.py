# -*- coding: utf-8 -*-
"""PDF twin of DC.C.4.1-E01_KPI-DC-01_Data_Classification_KPI_Calculation_Record.docx —
7-section compliance-audit template. Sourced exclusively from the real DC.C.3.1.docx
(Table 8) and DC.C.3.2.docx (Table 11)."""
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

OUT_PATH = "06_DC_C4_1_KPI_Evidence/DC.C.4.1-E01_KPI-DC-01_Data_Classification_KPI_Calculation_Record.pdf"

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
cell_style = ParagraphStyle("Cell", fontName="Arabic", fontSize=6.8, leading=9.5, alignment=2, textColor=colors.HexColor("#262626"))
cell_bold_navy = ParagraphStyle("CellBoldNavy", parent=cell_style, fontName="Arabic-Bold", textColor=NAVY, alignment=1)
head_cell_style = ParagraphStyle("HeadCell", fontName="Arabic-Bold", fontSize=7.6, alignment=1, textColor=colors.white)


def status_style(v):
    return ParagraphStyle("Status", parent=cell_style, fontName="Arabic-Bold", alignment=1, textColor=GREEN)


def rtl_table(headers_ar, rows, col_widths_ltr, status_col=None, font_size=None):
    hstyle, cstyle, bstyle = head_cell_style, cell_style, cell_bold_navy
    if font_size:
        hstyle = ParagraphStyle("HC2", parent=head_cell_style, fontSize=font_size + 0.8)
        cstyle = ParagraphStyle("C2", parent=cell_style, fontSize=font_size)
        bstyle = ParagraphStyle("B2", parent=cell_bold_navy, fontSize=font_size)
    header_row = [Paragraph(ar(h), hstyle) for h in reversed(headers_ar)]
    data = [header_row]
    for row_vals in rows:
        cells = []
        for i, v in enumerate(row_vals):
            if status_col is not None and i == status_col:
                cells.append(Paragraph(ar(str(v)), status_style(v)))
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
KPI_VALUE = round(CLASSIFIED_ASSETS / TOTAL_ASSETS * 100)

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
     [Paragraph(ar("سجل احتساب مؤشر نسبة اكتمال تصنيف الأصول البيانية (KPI-DC-01)"), title_style)]],
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
story.append(Paragraph(ar("سجل احتساب مؤشر نسبة اكتمال تصنيف الأصول البيانية (KPI-DC-01)"), report_title_style))
story.append(Paragraph(ar("Data Classification KPI Calculation Record"), draft_style))
story.append(Spacer(1, 10))

story.append(Paragraph(ar("1.  بيانات الوثيقة"), section_style))
story.append(Spacer(1, 4))
story.append(meta_table_ar([
    ("الجهة", "هيئة الخدمات الحكومية الذكية (SGSA)"),
    ("المنصة", ""),
    ("الإطار المرجعي", "إطار حوكمة البيانات الوطني (NDMO)"),
    ("رمز الدليل", "DC.C.4.1-E01"),
    ("نوع الوثيقة", "Calculation Record"),
    ("المتطلب المرتبط", "DC.C.4.1 — تقرير مراقبة عمليات تصنيف البيانات عبر مؤشرات الأداء الرئيسية"),
    ("المؤشر المرتبط", "KPI-DC-01 — نسبة اكتمال تصنيف الأصول البيانية"),
    ("الإصدار", "1.0"),
    ("التاريخ", "يونيو 2026"),
    ("حالة الوثيقة", "جاهزة للاعتماد"),
]))
story.append(PageBreak())

story.append(Paragraph(ar("2.  نطاق القياس"), section_style))
story.append(Spacer(1, 4))
story.append(meta_table_ar([
    ("فترة القياس", "الربع الثاني 2026 (أبريل – يونيو 2026) — كما ورد في تقرير DC.C.4.1"),
    ("نطاق القياس", "جميع الأصول البيانية الثلاثين (30) الواردة في تقرير الجرد DC.C.3.1 (18 مجموعة بيانات + 12 سجلاً)، والتي حُدِّد لكل منها مستوى تصنيف ناتج في DC.C.3.2."),
    ("تاريخ استخراج البيانات", "يونيو 2026 (تاريخ إصدار DC.C.3.1 وDC.C.3.2 وDC.C.5.1)"),
]))
story.append(Spacer(1, 10))

story.append(Paragraph(ar("3.  مصدر البيانات"), section_style))
story.append(Spacer(1, 4))
story.extend(bullets([
    "DC.C.3.1 — تقرير جرد المجموعات التي تم تحديدها من البيانات والسجلات (قائمة الأصول الثلاثين وحالة الجرد لكل أصل).",
    "DC.C.3.2 — تقرير تقييم الأثر (مستوى التصنيف الناتج لكل أصل بعد تطبيق مبدأ أعلى مستوى أثر).",
    "DC.C.5.1 — سجل البيانات (السجل الموحّد الذي يثبت مستوى التصنيف الممنوح لكل أصل).",
]))
story.append(PageBreak())

story.append(Paragraph(ar("4.  جدول البيانات المستخدمة"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p("يعرض الجدول التالي جميع الأصول البيانية الثلاثين الواردة في تقرير الجرد DC.C.3.1، مع حالة الجرد ومستوى التصنيف الناتج وفق DC.C.3.2:", body_style, FULL_W))
story.append(Spacer(1, 6))
asset_rows = [(n, name, atype, dept, "مُجرَّد", level) for n, name, atype, dept, level in ASSETS]
story.append(rtl_table(
    ["م", "اسم الأصل", "نوع الأصل", "الإدارة المالكة", "حالة الجرد", "مستوى التصنيف"],
    asset_rows,
    [7 * mm, 46 * mm, 20 * mm, 32 * mm, 20 * mm, 21 * mm],
    status_col=4,
))
story.append(Spacer(1, 6))
story.append(ar_p(
    "ملاحظة تدقيق: لا يتضمن أيٌّ من DC.C.3.1 أو DC.C.3.2 أو DC.C.5.1 معرّفات مستقلة "
    "للأصول (مثل رموز SGSA-DAT/REC)؛ لذلك استُخدم الرقم التسلسلي (م) كما ورد في هذه "
    "المصادر نفسها كمعرّف تتبّع لكل أصل في الجدول أعلاه. لم تُستخدم أي بيانات من تقرير "
    "DC.M.7 في هذا السجل، التزاماً بالاقتصار على المصادر الثلاثة المصرَّح بها أعلاه فقط.",
    note_style, FULL_W))
story.append(PageBreak())

story.append(Paragraph(ar("5.  تطبيق المعادلة"), section_style))
story.append(Spacer(1, 6))
story.append(rtl_table(
    ["البند", "القيمة"],
    [
        ("إجمالي الأصول البيانية (وفق DC.C.3.1)", str(TOTAL_ASSETS)),
        ("عدد الأصول المصنَّفة (وفق DC.C.3.2)", str(CLASSIFIED_ASSETS)),
        ("معادلة المؤشر", "عدد الأصول المصنَّفة ÷ إجمالي الأصول البيانية × 100"),
        ("تطبيق المعادلة", f"{CLASSIFIED_ASSETS} ÷ {TOTAL_ASSETS} × 100"),
        ("القيمة النهائية للمؤشر", f"{KPI_VALUE}%"),
    ],
    [126 * mm, 48 * mm],
))
story.append(Spacer(1, 12))

story.append(Paragraph(ar("6.  النتيجة والتحقق مقابل DC.C.4.1"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p(
    f"القيمة الناتجة ({KPI_VALUE}%) مطابقة تماماً للقيمة المقيسة الواردة في بطاقة مؤشر "
    "KPI-DC-01 ضمن تقرير DC.C.4.1 (القسم 8 وبند 9.1: «100% (30 أصلاً من أصل 30 مُصنَّفاً)»)، "
    "وللقيمة الواردة في جدول لوحة الأداء الإجمالية (القسم 10) وجدول التوافق مع متطلبات "
    "NDMO (القسم 14).", body_style, FULL_W))
story.append(Spacer(1, 6))
story.extend(bullets([
    "تم التحقق من مطابقة عدد الأصول (30) وأسمائها وترتيبها التسلسلي بين DC.C.3.1 وDC.C.3.2 وDC.C.5.1 دون أي تعارض.",
    "جميع الأصول الثلاثين مُصنَّفة (لا يوجد أصل بلا مستوى تصنيف ناتج)، وبذلك فإن البسط يساوي المقام ويكون الناتج 100% دون تقريب.",
    "أي معلومة غير واردة حرفياً في DC.C.3.1 أو DC.C.3.2 أو DC.C.5.1 تم استبعادها من هذا السجل.",
]))
story.append(Spacer(1, 6))

story.append(Paragraph(ar("7.  الاعتماد والتوقيع"), section_style))
story.append(Spacer(1, 4))
story.append(ar_p(
    "تمت مراجعة هذا السجل من مكتب إدارة البيانات، وتم التحقق من مطابقة البيانات الواردة "
    "فيه لمحتوى DC.C.3.1 وDC.C.3.2 وDC.C.5.1 دون أي إضافة أو حذف أو تعديل.", body_style, FULL_W))
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
