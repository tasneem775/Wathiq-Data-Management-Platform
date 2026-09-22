# -*- coding: utf-8 -*-
"""PDF twin of DC.M.2-E03_Data_Classification_Follow_Up_Meeting_Minutes.docx.
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

OUT_PATH = "05_DC_M2_Draft_Evidence/DC.M.2-E03_Data_Classification_Follow_Up_Meeting_Minutes.pdf"

pdfmetrics.registerFont(TTFont("Arabic", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arabic-Bold", r"C:\Windows\Fonts\arialbd.ttf"))

NAVY = colors.HexColor("#1F2A44")
GOLD = colors.HexColor("#AB8654")
LIGHT_GREY = colors.HexColor("#F2F2F2")
GREY = colors.HexColor("#595959")


def ar(text):
    return get_display(arabic_reshaper.reshape(text), base_dir="R")


title_style = ParagraphStyle("TitleBar", fontName="Arabic-Bold", fontSize=17, leading=22, textColor=colors.white, alignment=2)
subtitle_bar_style = ParagraphStyle("SubtitleBar", fontName="Arabic-Bold", fontSize=10.5, leading=15, textColor=colors.white, alignment=2)
report_title_style = ParagraphStyle("ReportTitle", fontName="Arabic-Bold", fontSize=14.5, leading=19, textColor=NAVY, alignment=2)
draft_style = ParagraphStyle("Draft", fontName="Arabic", fontSize=10.5, leading=14, textColor=GOLD, alignment=2)
meeting_title_style = ParagraphStyle("MeetingTitle", fontName="Arabic-Bold", fontSize=13, leading=17, textColor=NAVY, alignment=2, spaceBefore=4)
meta_label_style = ParagraphStyle("MetaLabel", fontName="Arabic-Bold", fontSize=9.5, textColor=GREY, alignment=2)
meta_value_style = ParagraphStyle("MetaValue", fontName="Arabic", fontSize=9.5, textColor=colors.HexColor("#262626"), alignment=2)
info_style = ParagraphStyle("Info", fontName="Arabic", fontSize=9.5, leading=14, textColor=colors.HexColor("#262626"), alignment=2)
info_bold_style = ParagraphStyle("InfoBold", fontName="Arabic-Bold", fontSize=9.5, leading=14, textColor=GREY, alignment=2)
label_style = ParagraphStyle("Label", fontName="Arabic-Bold", fontSize=10, textColor=NAVY, alignment=2, spaceBefore=6, spaceAfter=3)
bullet_style = ParagraphStyle("Bullet", fontName="Arabic", fontSize=9.3, leading=14, textColor=colors.HexColor("#262626"), alignment=2, spaceAfter=3)
note_style = ParagraphStyle("Note", fontName="Arabic", fontSize=8, leading=12, textColor=GREY, alignment=2)
cell_style = ParagraphStyle("Cell", fontName="Arabic", fontSize=8.6, leading=12, alignment=2, textColor=colors.HexColor("#262626"))
cell_bold_navy = ParagraphStyle("CellBoldNavy", parent=cell_style, fontName="Arabic-Bold", textColor=NAVY)
cell_center = ParagraphStyle("CellCenter", parent=cell_style, alignment=1)
head_cell_style = ParagraphStyle("HeadCell", fontName="Arabic-Bold", fontSize=9.5, alignment=1, textColor=colors.white)

MEETING1_ATTENDEES = [
    "مدير مكتب إدارة البيانات",
    "ممثل إدارة الموارد البشرية",
    "ممثل الإدارة المالية",
    "ممثل إدارة تقنية المعلومات",
    "ممثل إدارة الخدمات الرقمية",
]

MEETINGS = [
    {
        "title": "محضر اجتماع متابعة تنفيذ خطة تصنيف البيانات رقم (1)",
        "date": "01 مايو 2026",
        "objective": "متابعة بدء تنفيذ خطة تصنيف البيانات.",
        "attendees": MEETING1_ATTENDEES,
        "attendees_note": None,
        "topics": ["مراجعة خطة التنفيذ.", "متابعة حصر مجموعات البيانات والسجلات.", "متابعة تحديد ملاك البيانات."],
        "decisions": ["اعتماد بدء تنفيذ أنشطة الخطة.", "استكمال أعمال حصر البيانات.", "متابعة تحديث سجل ملاك البيانات."],
    },
    {
        "title": "محضر اجتماع متابعة تنفيذ خطة تصنيف البيانات رقم (2)",
        "date": "30 مايو 2026",
        "objective": "مراجعة مستوى التقدم في تنفيذ الخطة.",
        "attendees": MEETING1_ATTENDEES,
        "attendees_note": "نفس حضور الاجتماع رقم (1)",
        "topics": ["مراجعة حالة الأنشطة المنفذة.", "متابعة المبادرات قيد التنفيذ."],
        "decisions": ["تأكيد اكتمال حصر مجموعات البيانات.", "متابعة استكمال الأنشطة المتبقية."],
    },
    {
        "title": "محضر اجتماع متابعة تنفيذ خطة تصنيف البيانات رقم (3)",
        "date": "15 يونيو 2026",
        "objective": "مراجعة حالة الإنجاز النهائية للمرحلة الأولى.",
        "attendees": MEETING1_ATTENDEES,
        "attendees_note": "نفس حضور الاجتماع رقم (1)",
        "topics": ["مراجعة نسبة الإنجاز.", "توثيق الملاحظات النهائية."],
        "decisions": ["توثيق نتائج التنفيذ.", "رفع حالة التنفيذ ضمن تقرير المتابعة."],
    },
]


def rtl_table(headers_ar, rows, col_widths_ltr, center_cols=None):
    center_cols = center_cols or []
    header_row = [Paragraph(ar(h), head_cell_style) for h in reversed(headers_ar)]
    data = [header_row]
    ncols = len(headers_ar)
    for row_vals in rows:
        cells = []
        for i, v in enumerate(row_vals):
            style = cell_bold_navy if i == 0 else (cell_center if i in center_cols else cell_style)
            cells.append(Paragraph(ar(str(v)), style))
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
     [Paragraph(ar("محضر متابعة تنفيذ خطة تصنيف البيانات"), title_style)]],
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
story.append(Paragraph(ar("محاضر اجتماعات متابعة تنفيذ خطة تصنيف البيانات"), report_title_style))
story.append(Paragraph(ar("دليل داعم — DC.M.2-E03"), draft_style))
story.append(Spacer(1, 10))

meta_rows = [
    ("الجهة", "هيئة الخدمات الحكومية الذكية (SGSA)"),
    ("القسم", "مكتب إدارة البيانات"),
    ("المنصة", ""),
    ("الإطار المرجعي", "إطار حوكمة البيانات الوطني (NDMO)"),
    ("رمز الدليل", "DC.M.2-E03"),
    ("المتطلب المرتبط", "DC.M.2 — تنفيذ خطة تصنيف البيانات وخارطة الطريق"),
    ("اسم الدليل", "محاضر اجتماعات متابعة تنفيذ خطة تصنيف البيانات"),
    ("الإصدار", "1.0"),
    ("التاريخ", "يونيو 2026"),
    ("حالة الوثيقة", "جاهزة للمراجعة"),
]
meta_data = [[Paragraph(ar(v), meta_value_style), Paragraph(ar(l), meta_label_style)] for l, v in meta_rows]
meta_tbl = Table(meta_data, colWidths=[doc.width - 45 * mm, 45 * mm])
meta_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
story.append(meta_tbl)
story.append(PageBreak())

# ---- Meeting minutes ----
for idx, m in enumerate(MEETINGS, start=1):
    story.append(Paragraph(ar(m["title"]), meeting_title_style))
    story.append(Paragraph(ar(f"التاريخ: {m['date']}"), info_bold_style))
    story.append(Paragraph(ar(f"الهدف: {m['objective']}"), info_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph(ar("الحضور:"), label_style))
    if m["attendees_note"]:
        story.append(Paragraph(ar(m["attendees_note"]), ParagraphStyle("AttNote", fontName="Arabic", fontSize=8.5, textColor=GREY, alignment=2, italic=1)))
        story.append(Spacer(1, 3))
    story.append(rtl_table(["المسمى الوظيفي"], [(a,) for a in m["attendees"]], [160 * mm]))
    story.append(Spacer(1, 10))

    story.append(Paragraph(ar("المواضيع:"), label_style))
    for t in m["topics"]:
        story.append(Paragraph(ar("•  " + t), bullet_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph(ar("القرارات:"), label_style))
    story.append(rtl_table(
        ["الرقم", "القرار"],
        [(i + 1, d) for i, d in enumerate(m["decisions"])],
        [20 * mm, 140 * mm],
        center_cols=[0],
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph(ar("التوقيعات:"), label_style))
    story.append(rtl_table(
        ["المسمى الوظيفي", "التوقيع"],
        [(a, "____________") for a in m["attendees"]],
        [110 * mm, 50 * mm],
        center_cols=[1],
    ))

    if idx < len(MEETINGS):
        story.append(PageBreak())

story.append(Spacer(1, 16))
story.append(Paragraph(ar("الاعتماد"), ParagraphStyle("SectionHead", fontName="Arabic-Bold", fontSize=12.5, textColor=NAVY, alignment=2)))
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
    "لإثبات اجتماعات متابعة تنفيذ خطة تصنيف البيانات."
), note_style))

doc.build(story)
print("Saved:", OUT_PATH)
