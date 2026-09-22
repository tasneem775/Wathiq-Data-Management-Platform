# -*- coding: utf-8 -*-
"""PDF twin of DC.M.2-E04-A_Awareness_Workshop_Attendance_Register.docx.
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

OUT_PATH = "05_DC_M2_Draft_Evidence/DC.M.2-E04-A_Awareness_Workshop_Attendance_Register.pdf"

pdfmetrics.registerFont(TTFont("Arabic", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arabic-Bold", r"C:\Windows\Fonts\arialbd.ttf"))

NAVY = colors.HexColor("#1F2A44")
GOLD = colors.HexColor("#AB8654")
LIGHT_GREY = colors.HexColor("#F2F2F2")
GREY = colors.HexColor("#595959")

DEPARTMENTS = [
    "مكتب إدارة البيانات",
    "إدارة الموارد البشرية",
    "الإدارة المالية",
    "إدارة تقنية المعلومات",
    "إدارة الخدمات الرقمية",
]


def dept_for(i):
    return DEPARTMENTS[i % len(DEPARTMENTS)]


# 47 unique generic Arabic full names (common first name + common family name).
# Not linked to any real individual or public figure — illustrative sample data only.
NAMES = [
    "أحمد السالم", "سارة العتيبي", "خالد القحطاني", "نورة الشهري", "محمد الدوسري",
    "منى الحربي", "عبدالله الغامدي", "فاطمة الزهراني", "فهد المطيري", "هند العنزي",
    "سعود الشمري", "ريم القرني", "ماجد البقمي", "لمياء السبيعي", "طارق الرشيدي",
    "أمل الجهني", "بندر العمري", "عائشة الشهراني", "ناصر الخالدي", "جواهر اليامي",
    "سلطان الفيفي", "لطيفة الثقفي", "عمر السلمي", "مها المالكي", "يوسف الحازمي",
    "غادة العتيبي", "وليد القحطاني", "أروى الدوسري", "تركي الحربي", "دلال الغامدي",
    "فيصل الزهراني", "شيخة المطيري", "عبدالعزيز العنزي", "بشاير الشمري", "راشد القرني",
    "رهف البقمي", "سامي السبيعي", "لينا الرشيدي", "حمد الجهني", "حصة العمري",
    "إبراهيم الشهراني", "سارة الخالدي", "عبدالرحمن اليامي", "نورة الفيفي", "مشعل الثقفي",
    "منى السلمي", "سعد المالكي",
]
assert len(NAMES) == 47
assert len(set(NAMES)) == 47


WORKSHOPS = [
    {"title": "ورشة التوعية الأولى: مفاهيم تصنيف البيانات", "date": "مايو 2026", "count": 16, "start_id": 1},
    {"title": "ورشة التوعية الثانية: مستويات التصنيف ومتطلباته", "date": "مايو 2026", "count": 16, "start_id": 17},
    {"title": "ورشة التوعية الثالثة: آليات التطبيق العملي", "date": "يونيو 2026", "count": 15, "start_id": 33},
]
assert sum(w["count"] for w in WORKSHOPS) == 47


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
workshop_title_style = ParagraphStyle("WTitle", fontName="Arabic-Bold", fontSize=11, leading=15, textColor=NAVY, alignment=2)
workshop_info_style = ParagraphStyle("WInfo", fontName="Arabic", fontSize=9, leading=13, textColor=GREY, alignment=2)
note_style = ParagraphStyle("Note", fontName="Arabic", fontSize=8, leading=12, textColor=GREY, alignment=2)
cell_style = ParagraphStyle("Cell", fontName="Arabic", fontSize=8.6, leading=12, alignment=2, textColor=colors.HexColor("#262626"))
cell_center = ParagraphStyle("CellCenter", parent=cell_style, alignment=1)
cell_bold_navy = ParagraphStyle("CellBoldNavy", parent=cell_style, fontName="Arabic-Bold", textColor=NAVY, alignment=1)
head_cell_style = ParagraphStyle("HeadCell", fontName="Arabic-Bold", fontSize=9.5, alignment=1, textColor=colors.white)


def rtl_table(headers_ar, rows, col_widths_ltr, center_cols=None):
    center_cols = center_cols or []
    header_row = [Paragraph(ar(h), head_cell_style) for h in reversed(headers_ar)]
    data = [header_row]
    for row_vals in rows:
        cells = []
        for i, v in enumerate(row_vals):
            if i == 0:
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
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
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
     [Paragraph(ar("سجل حضور ورش التوعية والتدريب الخاصة بتصنيف البيانات"), title_style)]],
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
story.append(Paragraph(ar("سجل حضور ورش التوعية والتدريب الخاصة بتصنيف البيانات"), report_title_style))
story.append(Paragraph(ar("دليل داعم — DC.M.2-E04-A"), draft_style))
story.append(Spacer(1, 10))

meta_rows = [
    ("الجهة", "هيئة الخدمات الحكومية الذكية (SGSA)"),
    ("القسم", "مكتب إدارة البيانات"),
    ("المنصة", ""),
    ("الإطار المرجعي", "إطار حوكمة البيانات الوطني (NDMO)"),
    ("رمز الدليل", "DC.M.2-E04-A"),
    ("المتطلب المرتبط", "DC.M.2 — تنفيذ خطة تصنيف البيانات وخارطة الطريق"),
    ("اسم الدليل", "سجل حضور ورش التوعية والتدريب الخاصة بتصنيف البيانات"),
    ("مالك الوثيقة", "مكتب إدارة البيانات (Data Management Office)"),
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
story.append(Paragraph(ar("القسم الأول: بيانات الورشة"), section_style))
story.append(Spacer(1, 4))
story.append(Paragraph(ar(
    "يوثّق هذا الدليل سجل حضور ورش التوعية الثلاث المنفذة ضمن المرحلة الأولى من خطة تصنيف "
    "البيانات، ويُستخدم كمرفق تدقيق داعم لإثبات تنفيذ نشاط التوعية والتدريب ورفع مستوى الوعي "
    "بمتطلبات تصنيف البيانات."
), body_style))
story.append(Spacer(1, 12))

for w in WORKSHOPS:
    story.append(Paragraph(ar(w["title"]), workshop_title_style))
    story.append(Paragraph(ar(f"التاريخ: {w['date']}"), workshop_info_style))
    story.append(Paragraph(ar(f"عدد الحضور: {w['count']}"), workshop_info_style))
    story.append(Spacer(1, 8))

story.append(PageBreak())

# ---- القسم الثاني ----
story.append(Paragraph(ar("القسم الثاني: سجل الحضور لكل ورشة"), section_style))
story.append(Spacer(1, 8))

for w_idx, w in enumerate(WORKSHOPS):
    story.append(Paragraph(ar(w["title"]), workshop_title_style))
    story.append(Paragraph(ar(f"التاريخ: {w['date']}  —  عدد الحضور: {w['count']}"), workshop_info_style))
    story.append(Spacer(1, 6))

    rows = []
    for i in range(w["count"]):
        participant_id = w["start_id"] + i
        rows.append((i + 1, NAMES[participant_id - 1], dept_for(participant_id - 1), "____________"))

    story.append(rtl_table(
        ["الرقم", "اسم المشارك", "الإدارة", "التوقيع"],
        rows,
        [14 * mm, 40 * mm, 55 * mm, 35 * mm],
        center_cols=[0, 3],
    ))
    if w_idx < len(WORKSHOPS) - 1:
        story.append(PageBreak())
    else:
        story.append(Spacer(1, 14))

story.append(PageBreak())

# ---- القسم الثالث ----
story.append(Paragraph(ar("القسم الثالث: اعتماد السجل"), section_style))
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
    "ملاحظة: تم إعداد هذا السجل ضمن حزمة أدلة تصنيف البيانات الخاصة بهيئة الخدمات الحكومية الذكية (SGSA) التوضيحية وفق نموذج سجلات التدقيق "
    "المعتمد، وتستخدم بيانات نموذجية لغرض عرض آلية توثيق الحضور، ويتم استبدالها بالبيانات "
    "الفعلية عند التطبيق التشغيلي."
), note_style))
story.append(Spacer(1, 4))
story.append(Paragraph(ar(
    "هذا الدليل مرفق تدقيق مستقل ضمن حزمة أدلة تصنيف البيانات الخاصة بهيئة الخدمات الحكومية الذكية (SGSA) الداعمة لمتطلب DC.M.2، ويستخدم "
    "لإثبات تنفيذ أنشطة التوعية والتدريب الخاصة بتصنيف البيانات."
), note_style))

doc.build(story)
print("Saved:", OUT_PATH)
print("Total attendance:", sum(w["count"] for w in WORKSHOPS))
