# -*- coding: utf-8 -*-
"""Builds DC.C.4.1-E01_Asset_Traceability_Verification.pdf — a 4-page Evidence
Verification Package proving that the 30 assets used to calculate KPI-DC-01 in DC.C.4.1
are traceable across DC.C.3.1 (Table 8), DC.C.3.2 (Table 11/9), and DC.C.5.1 (Table 6).
No asset name/type/department/classification is invented or altered; the two
source-to-source naming differences (asset 3, asset 13) are shown as Notes only.
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

OUT_PATH = "06_DC_C4_1_KPI_Evidence/DC.C.4.1-E01_Asset_Traceability_Verification.pdf"

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


def mixed(text):
    """For strings mixing English labels with Arabic asset names — reshape only,
    let reportlab's own bidi handle the mixed-direction line."""
    return get_display(arabic_reshaper.reshape(text))


def wrap_mixed(text, font_name, font_size, max_width):
    words = text.split(" ")
    lines, current = [], []
    for w in words:
        trial = current + [w]
        shaped = mixed(" ".join(trial))
        if not current or stringWidth(shaped, font_name, font_size) <= max_width:
            current = trial
        else:
            lines.append(" ".join(current))
            current = [w]
    if current:
        lines.append(" ".join(current))
    return "<br/>".join(mixed(l) for l in lines)


def mixed_p(text, style, max_width):
    return Paragraph(wrap_mixed(text, style.fontName, style.fontSize, max_width), style)


title_style = ParagraphStyle("TitleBar", fontName="Arabic-Bold", fontSize=17, leading=22, textColor=colors.white, alignment=1)
subtitle_bar_style = ParagraphStyle("SubtitleBar", fontName="Arabic-Bold", fontSize=10, leading=14, textColor=colors.white, alignment=1)
page_title_style = ParagraphStyle("PageTitle", fontName="Arabic-Bold", fontSize=15, leading=19, textColor=NAVY, alignment=1, spaceBefore=10, spaceAfter=6)
label_style = ParagraphStyle("Label", fontName="Arabic-Bold", fontSize=10.5, leading=15, textColor=GREY, alignment=2)
value_style = ParagraphStyle("Value", fontName="Arabic", fontSize=10.5, leading=15, textColor=colors.HexColor("#262626"), alignment=2)
body_style = ParagraphStyle("Body", fontName="Arabic", fontSize=10, leading=16, textColor=colors.HexColor("#262626"), alignment=2)
kpi_label_style = ParagraphStyle("KpiLabel", fontName="Arabic-Bold", fontSize=11, leading=15, textColor=colors.white, alignment=1)
kpi_value_style = ParagraphStyle("KpiValue", fontName="Arabic-Bold", fontSize=26, leading=30, textColor=colors.white, alignment=1)
section_style = ParagraphStyle("Section", fontName="Arabic-Bold", fontSize=12.5, leading=16, textColor=NAVY, alignment=2, spaceBefore=4)
bullet_style = ParagraphStyle("Bullet", fontName="Arabic", fontSize=10, leading=15, textColor=colors.HexColor("#262626"), alignment=2)
note_style = ParagraphStyle("Note", fontName="Arabic", fontSize=8, leading=12, textColor=GREY, alignment=2, italic=1)
cell_style = ParagraphStyle("Cell", fontName="Arabic", fontSize=7.4, leading=10, alignment=2, textColor=colors.HexColor("#262626"))
cell_center = ParagraphStyle("CellCenter", parent=cell_style, alignment=1)
cell_bold_navy = ParagraphStyle("CellBoldNavy", parent=cell_style, fontName="Arabic-Bold", textColor=NAVY, alignment=1)
cell_bold_green = ParagraphStyle("CellBoldGreen", parent=cell_style, fontName="Arabic-Bold", textColor=GREEN, alignment=1)
cell_bold_amber = ParagraphStyle("CellBoldAmber", parent=cell_style, fontName="Arabic-Bold", textColor=AMBER, alignment=1)
head_cell_style = ParagraphStyle("HeadCell", fontName="Arabic-Bold", fontSize=7.6, alignment=1, textColor=colors.white)


# ============ بيانات مصدرها الحرفي DC.C.3.1 (Table 8) + DC.C.3.2 (Table 11/9) + DC.C.5.1 (Table 6) ============
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
TOTAL = len(ASSETS)
NAME_PARTIAL = {3}
DEPT_PARTIAL = {13}

doc = SimpleDocTemplate(
    OUT_PATH, pagesize=A4,
    leftMargin=16 * mm, rightMargin=16 * mm, topMargin=14 * mm, bottomMargin=14 * mm,
)
story = []
FULL_W = doc.width


def banner():
    tbl = Table(
        [[Paragraph(ar("منصة ذكية لإدارة وقياس الامتثال لمتطلبات المكتب الوطني لإدارة البيانات (NDMO)"), subtitle_bar_style)],
         [Paragraph(ar("Data Asset Classification Traceability Verification Guide"), title_style)]],
        colWidths=[FULL_W],
    )
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING", (0, 0), (-1, 0), 6), ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
        ("TOPPADDING", (0, -1), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
    ]))
    return tbl


def meta_line(label, value):
    tbl = Table([[mixed_p(value, value_style, FULL_W - 46 * mm), Paragraph(ar(label), label_style)]],
                colWidths=[FULL_W - 46 * mm, 46 * mm])
    tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return tbl


# ============================================================
# Page 1 — Title, Project, Objective, KPI
# ============================================================
story.append(banner())
story.append(Spacer(1, 14))
story.append(Paragraph(mixed("Asset Classification Traceability Verification"), page_title_style))
story.append(Spacer(1, 4))
story.append(Paragraph(mixed("Evidence Verification Package — DC.C.4.1-E01 (KPI-DC-01)"),
                        ParagraphStyle("Sub", fontName="Arabic", fontSize=10.5, textColor=GOLD, alignment=1)))
story.append(Spacer(1, 18))

story.append(meta_line("Project:", "Data Asset Classification Traceability Verification Guide"))
story.append(Spacer(1, 10))

story.append(Paragraph(ar("الهدف"), section_style))
story.append(Spacer(1, 4))
story.append(mixed_p(
    "إثبات إمكانية تتبع الأصول البيانية الثلاثين المستخدمة في احتساب مؤشر KPI-DC-01 عبر "
    "مصادرها المرجعية الثلاثة: DC.C.3.1 (Table 8)، DC.C.3.2 (Table 11/9)، وDC.C.5.1 (Table 6).",
    body_style, FULL_W,
))
story.append(Spacer(1, 20))

kpi_tbl = Table(
    [[Paragraph(mixed("KPI-DC-01"), kpi_label_style)],
     [Paragraph(mixed("Classification Completeness Rate"), kpi_label_style)],
     [Paragraph(mixed("100%"), kpi_value_style)]],
    colWidths=[FULL_W],
)
kpi_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), NAVY),
    ("TOPPADDING", (0, 0), (-1, 0), 10), ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
    ("TOPPADDING", (0, 1), (-1, 1), 2), ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
    ("TOPPADDING", (0, 2), (-1, 2), 4), ("BOTTOMPADDING", (0, 2), (-1, 2), 14),
]))
story.append(kpi_tbl)
story.append(PageBreak())

# ============================================================
# Page 2 — Source summary table
# ============================================================
story.append(banner())
story.append(Spacer(1, 10))
story.append(Paragraph(mixed("Source Verification Summary"), page_title_style))
story.append(Spacer(1, 10))

summary_headers = ["Source", "Asset Count", "Verification Result"]
summary_rows = [("DC.C.3.1", str(TOTAL), "Matched"), ("DC.C.3.2", str(TOTAL), "Matched"), ("DC.C.5.1", str(TOTAL), "Matched")]
head_cells = [Paragraph(mixed(h), head_cell_style) for h in summary_headers]
data = [head_cells]
for s, cnt, res in summary_rows:
    data.append([
        Paragraph(mixed(s), cell_bold_navy),
        Paragraph(mixed(cnt), cell_center),
        Paragraph(mixed(res), cell_bold_green),
    ])
summary_tbl = Table(data, colWidths=[60 * mm, 50 * mm, 60 * mm], repeatRows=1)
summary_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ("BACKGROUND", (0, 2), (-1, 2), LIGHT_GREY),
]))
story.append(summary_tbl)
story.append(Spacer(1, 16))
story.append(mixed_p(
    "جميع الأصول الثلاثين (30) الموجودة في تقرير الجرد DC.C.3.1 موجودة أيضاً في تقرير "
    "تقييم الأثر DC.C.3.2 وسجل البيانات DC.C.5.1، دون أي أصل ناقص أو زائد في أي من المصادر الثلاثة.",
    body_style, FULL_W,
))
story.append(PageBreak())

# ============================================================
# Page 3 — Condensed matching table (30 assets)
# ============================================================
story.append(banner())
story.append(Spacer(1, 8))
story.append(Paragraph(mixed("Asset Matching Summary — All 30 Assets"), page_title_style))
story.append(Spacer(1, 6))

cond_headers = ["No.", "Asset Name (DC.C.3.1)", "Type", "Owner Department", "Classification", "Match Status", "Notes"]
cond_head_cells = [Paragraph(mixed(h), head_cell_style) for h in cond_headers]
cond_data = [cond_head_cells]
for n, name, atype, dept, cls in ASSETS:
    if n in NAME_PARTIAL or n in DEPT_PARTIAL:
        status_p = Paragraph(mixed("Partial"), cell_bold_amber)
        note_txt = "Naming difference between source documents (see E01 Notes)."
    else:
        status_p = Paragraph(mixed("Matched"), cell_bold_green)
        note_txt = "—"
    cond_data.append([
        Paragraph(mixed(str(n)), cell_bold_navy),
        Paragraph(mixed(name), cell_style),
        Paragraph(mixed(atype), cell_center),
        Paragraph(mixed(dept), cell_style),
        Paragraph(mixed(cls), cell_center),
        status_p,
        Paragraph(mixed(note_txt), ParagraphStyle("NoteCell", parent=cell_style, fontSize=6.6, italic=True, textColor=GREY)),
    ])
cond_tbl = Table(cond_data, colWidths=[8 * mm, 46 * mm, 20 * mm, 34 * mm, 16 * mm, 16 * mm, 38 * mm], repeatRows=1)
cond_style = [
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9D9D9")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
]
for i in range(1, len(cond_data)):
    if i % 2 == 0:
        cond_style.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GREY))
cond_tbl.setStyle(TableStyle(cond_style))
story.append(cond_tbl)
story.append(PageBreak())

# ============================================================
# Page 4 — Audit Verification Notes
# ============================================================
story.append(banner())
story.append(Spacer(1, 10))
story.append(Paragraph(mixed("Audit Verification Notes"), page_title_style))
story.append(Spacer(1, 10))

notes = [
    "جميع الأصول الثلاثين موجودة في المصادر الثلاثة (DC.C.3.1 وDC.C.3.2 وDC.C.5.1).",
    "لم يتم إنشاء أصول جديدة.",
    "لم يتم استخدام معرفات غير موجودة في المصادر.",
    "الرقم التسلسلي استُخدم كمعرّف تتبع لأنه لا توجد Asset IDs مستقلة في المصادر.",
]
for n in notes:
    story.append(mixed_p("•  " + n, bullet_style, FULL_W - 10))
    story.append(Spacer(1, 6))

story.append(Spacer(1, 16))
story.append(mixed_p(
    "ملاحظتان إضافيتان مسجَّلتان في ورقة Asset Matching (الأصل رقم 3 والأصل رقم 13) تعكسان "
    "فروقات تسمية موجودة بين المصادر الأصلية نفسها، ولا تُعدّان خطأً في هذا السجل.",
    note_style, FULL_W,
))
story.append(Spacer(1, 10))
story.append(mixed_p(
    "This document is an Evidence Verification Package supporting DC.C.4.1 / KPI-DC-01. "
    "It is not a new requirements document.",
    note_style, FULL_W,
))

doc.build(story)
print("Saved:", OUT_PATH)
