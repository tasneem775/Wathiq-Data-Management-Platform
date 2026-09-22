# -*- coding: utf-8 -*-
"""PDF twin of DC_M2_Implementation_Status_Report.docx — same content, Wathiq/SGSA identity.
Draft evidence artifact, standalone, not merged into any existing repository yet.
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

OUT_PATH = "05_DC_M2_Draft_Evidence/DC_M2_Implementation_Status_Report.pdf"

pdfmetrics.registerFont(TTFont("Arabic", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arabic-Bold", r"C:\Windows\Fonts\arialbd.ttf"))

NAVY = colors.HexColor("#1F2A44")
GOLD = colors.HexColor("#AB8654")
LIGHT_GREY = colors.HexColor("#F2F2F2")
GREEN = colors.HexColor("#1F6F43")
AMBER = colors.HexColor("#8A6D00")


def ar(text):
    return get_display(arabic_reshaper.reshape(text), base_dir="R")


title_style = ParagraphStyle("TitleBar", fontName="Arabic-Bold", fontSize=17, leading=22, textColor=colors.white, alignment=2)
subtitle_bar_style = ParagraphStyle("SubtitleBar", fontName="Arabic-Bold", fontSize=10.5, leading=15, textColor=colors.white, alignment=2)
report_title_style = ParagraphStyle("ReportTitle", fontName="Arabic-Bold", fontSize=15, leading=19, textColor=NAVY, alignment=2)
draft_style = ParagraphStyle("Draft", fontName="Arabic", fontSize=10.5, leading=14, textColor=GOLD, alignment=2)
section_style = ParagraphStyle("Section", fontName="Arabic-Bold", fontSize=12.5, leading=16, textColor=NAVY, alignment=2, spaceBefore=6)
meta_label_style = ParagraphStyle("MetaLabel", fontName="Arabic-Bold", fontSize=9.5, textColor=colors.HexColor("#595959"), alignment=2)
meta_value_style = ParagraphStyle("MetaValue", fontName="Arabic", fontSize=9.5, textColor=colors.HexColor("#262626"), alignment=2)
body_style = ParagraphStyle("Body", fontName="Arabic", fontSize=9.5, leading=15, textColor=colors.HexColor("#262626"), alignment=2)
bold_label_style = ParagraphStyle("BoldLabel", fontName="Arabic-Bold", fontSize=10, textColor=colors.HexColor("#262626"), alignment=2)
bullet_style = ParagraphStyle("Bullet", fontName="Arabic", fontSize=9.3, leading=14, textColor=colors.HexColor("#262626"), alignment=2, spaceAfter=4)
note_style = ParagraphStyle("Note", fontName="Arabic", fontSize=8, leading=12, textColor=colors.HexColor("#595959"), alignment=2)
cell_style = ParagraphStyle("Cell", fontName="Arabic", fontSize=8.4, leading=12, alignment=2, textColor=colors.HexColor("#262626"))
cell_bold_navy = ParagraphStyle("CellBoldNavy", parent=cell_style, fontName="Arabic-Bold", textColor=NAVY)
head_cell_style = ParagraphStyle("HeadCell", fontName="Arabic-Bold", fontSize=9.5, alignment=1, textColor=colors.white)


def status_style(v):
    color = GREEN if v in ("مكتمل", "متوفر") else AMBER
    return ParagraphStyle("Status", parent=cell_style, fontName="Arabic-Bold", alignment=1, textColor=color)


def rtl_table(headers_ar, rows, col_widths_ltr, status_col=None):
    """Builds a table with proper RTL column order (first logical column ends up rightmost)."""
    header_row = [Paragraph(ar(h), head_cell_style) for h in reversed(headers_ar)]
    data = [header_row]
    for row_vals in rows:
        cells = []
        for i, v in enumerate(row_vals):
            if status_col is not None and i == status_col:
                cells.append(Paragraph(ar(str(v)), status_style(v)))
            elif i == 0:
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
     [Paragraph(ar("تقرير حالة تنفيذ خطة تصنيف البيانات"), title_style)]],
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
story.append(Paragraph(ar("تقرير حالة تنفيذ خطة تصنيف البيانات"), report_title_style))
story.append(Paragraph(ar("مسودة دليل مستقل للمراجعة — DC.M.2"), draft_style))
story.append(Spacer(1, 10))

meta_rows = [
    ("الجهة", "هيئة الخدمات الحكومية الذكية (SGSA)"),
    ("القسم", "مكتب إدارة البيانات"),
    ("رمز الدليل", "DC.M.2"),
    ("اسم الدليل", "تقرير حالة تنفيذ خطة تصنيف البيانات"),
    ("الإصدار", "0.1 (مسودة)"),
    ("التاريخ", "يونيو 2026"),
    ("حالة الوثيقة", "مسودة للمراجعة — لم تُعتمد بعد"),
    ("الإطار المرجعي", "إطار حوكمة البيانات الوطني (NDMO)"),
    ("مرجع الخطة المعتمدة", "DC.C.1.1"),
]
meta_data = [[Paragraph(ar(v), meta_value_style), Paragraph(ar(l), meta_label_style)] for l, v in meta_rows]
meta_tbl = Table(meta_data, colWidths=[doc.width - 45 * mm, 45 * mm])
meta_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
story.append(meta_tbl)
story.append(PageBreak())

# ---- 1. المقدمة ----
story.append(Paragraph(ar("1.  المقدمة"), section_style))
story.append(Spacer(1, 4))
story.append(Paragraph(ar(
    "يُعدّ متطلب DC.M.2 ضمن سؤال النضج DC.MQ.1 مطلباً أساسياً في المرحلة الأولى (البناء) من "
    "أطوار تصنيف البيانات، إذ ينص على أن: «تعمل الجهة على تنفيذ الخطة المعرفة وخارطة طريق "
    "تصنيف البيانات على جميع المجموعات المعتمدة من البيانات والسجلات». يوثّق هذا التقرير "
    "حالة تنفيذ هذه الخطة فعلياً داخل هيئة الخدمات الحكومية الذكية (SGSA)، ويُعدّ الدليل "
    "الرسمي المُستخدَم لإثبات استيفاء هذا المتطلب."
), body_style))
story.append(Spacer(1, 6))
story.append(Paragraph(ar(
    "يستعرض التقرير خارطة الطريق المعتمدة ونطاق تنفيذها، ونطاق التغطية الفعلي عبر مجموعات "
    "البيانات والسجلات والإدارات المالكة، وحالة كل نشاط من أنشطة الخطة، والمبادرات المنفذة "
    "فعلياً، ومؤشرات التقدم المحققة، إضافة إلى الأدلة الداعمة لكل ما سبق."
), body_style))
story.append(Spacer(1, 14))

# ---- 2. الخطة المعتمدة وخارطة الطريق ----
story.append(Paragraph(ar("2.  الخطة المعتمدة وخارطة الطريق"), section_style))
story.append(Spacer(1, 4))
story.append(Paragraph(ar("أهداف الخطة:"), bold_label_style))
for b in [
    "حصر جميع مجموعات البيانات والسجلات المعتمدة عبر الإدارات.",
    "تحديد وتوثيق ملاك البيانات ومسؤولياتهم رسمياً.",
    "رفع مستوى الوعي المؤسسي بمفاهيم تصنيف البيانات ومتطلباته.",
    "إعداد إجراءات تشغيلية موحَّدة لتصنيف البيانات تمهيداً لاعتمادها.",
]:
    story.append(Paragraph(ar("•  " + b), bullet_style))
story.append(Spacer(1, 6))
story.append(Paragraph(ar("نطاق التنفيذ:"), bold_label_style))
story.append(Paragraph(ar(
    "يشمل نطاق التنفيذ جميع مجموعات البيانات والسجلات المعتمدة ضمن الجرد المؤسسي، عبر خمس "
    "إدارات رئيسية مشمولة بالخطة (مكتب إدارة البيانات، الموارد البشرية، الإدارة المالية، "
    "تقنية المعلومات، الخدمات الرقمية)."
), body_style))
story.append(Spacer(1, 6))
story.append(Paragraph(ar("الفترة الزمنية:"), bold_label_style))
story.append(Paragraph(ar(
    "تغطي هذه المرحلة (مرحلة البناء — Level 1) الفترة من الربع الأول 2026 وحتى تاريخ إصدار "
    "هذا التقرير في يونيو 2026، تمهيداً للانتقال إلى مرحلة التعريف (Level 2)."
), body_style))
story.append(Spacer(1, 14))

# ---- 3. نطاق التغطية ----
story.append(Paragraph(ar("3.  نطاق التغطية"), section_style))
story.append(Spacer(1, 4))
story.append(Paragraph(ar("يوضّح الجدول التالي نطاق التغطية الفعلي لخطة تصنيف البيانات عبر الإدارات المالكة:"), body_style))
story.append(Spacer(1, 6))
story.append(rtl_table(
    ["مجموعات البيانات المشمولة", "السجلات المشمولة", "الإدارة المالكة", "حالة التنفيذ"],
    [
        ("بيانات الموظفين والملفات الوظيفية", "سجلات العقود والاتفاقيات", "إدارة الموارد البشرية", "مكتمل"),
        ("بيانات المدفوعات والمعاملات المالية", "سجلات التدقيق الداخلي والرقابة", "الإدارة المالية", "مكتمل"),
        ("بيانات الأصول والبنية التحتية التقنية", "سجلات التغييرات والتحديثات التقنية", "إدارة تقنية المعلومات", "مكتمل"),
        ("بيانات المستخدمين والمستفيدين", "سجلات الشكاوى والمقترحات", "إدارة الخدمات الرقمية", "قيد التنفيذ"),
        ("بيانات التقارير والإحصاءات المنشورة", "سجلات التقارير الإدارية الدورية", "مكتب إدارة البيانات", "مكتمل"),
    ],
    [48 * mm, 48 * mm, 40 * mm, 26 * mm],
    status_col=3,
))
story.append(Spacer(1, 16))

# ---- 4. حالة تنفيذ الخطة ----
story.append(Paragraph(ar("4.  حالة تنفيذ الخطة"), section_style))
story.append(Spacer(1, 6))
story.append(rtl_table(
    ["النشاط", "المسؤول", "الحالة", "نسبة الإنجاز", "الملاحظات"],
    [
        ("حصر مجموعات البيانات والسجلات", "مكتب إدارة البيانات", "مكتمل", "100%",
         "تم حصر وتوثيق جميع المجموعات الرئيسية دون تحديات جوهرية"),
        ("تحديد وتوثيق ملاك البيانات", "مكتب إدارة البيانات", "مكتمل", "100%",
         "صدر قرار رسمي بتحديد ملاك البيانات في جميع الإدارات"),
        ("تنفيذ برنامج التوعية والتدريب", "إدارة الموارد البشرية", "قيد التنفيذ", "90%",
         "تم تنفيذ معظم الورش المخططة؛ تبقّت جلسة واحدة لإدارة الخدمات الرقمية"),
        ("إعداد إجراءات التصنيف التشغيلية", "مكتب إدارة البيانات", "قيد التنفيذ", "80%",
         "الإجراءات في مرحلة المراجعة النهائية تمهيداً للاعتماد الرسمي"),
        ("عقد اجتماعات المتابعة الدورية", "مكتب إدارة البيانات", "مكتمل", "100%",
         "عُقدت الاجتماعات المقررة وتم توثيقها بمحاضر رسمية"),
    ],
    [36 * mm, 30 * mm, 22 * mm, 18 * mm, 56 * mm],
    status_col=2,
))
story.append(PageBreak())

# ---- 5. المبادرات والأنشطة المنفذة ----
story.append(Paragraph(ar("5.  المبادرات والأنشطة المنفذة"), section_style))
story.append(Spacer(1, 4))
story.append(Paragraph(ar("فيما يلي تفاصيل الإنجازات الفعلية لكل نشاط من أنشطة الخطة:"), body_style))
story.append(Spacer(1, 6))
for b in [
    "حصر مجموعات البيانات: أُجري جرد شامل لمجموعات البيانات والسجلات الرئيسية عبر الإدارات الخمس، وأُعدَّت قائمة موثَّقة تشمل اسم المجموعة والإدارة المالكة ودرجة أهميتها التشغيلية.",
    "توثيق ملاك البيانات: صدر قرار رسمي بتحديد ملاك البيانات، وتضمَّن السجل المعتمَد اسم كل مالك ومسؤولياته والبيانات التابعة لنطاق إدارته.",
    "ورش التوعية الداخلية: نُفِّذت ورش توعية استهدفت منسوبي الإدارات المشمولة حول أهمية تصنيف البيانات ومستوياته وآليات التطبيق العملي.",
    "مسودة إجراءات التصنيف: أُعِدَّت مسودة الإجراءات التشغيلية الموحَّدة لتصنيف البيانات، وهي قيد المراجعة النهائية قبل رفعها للاعتماد.",
    "اجتماعات المتابعة: عُقدت اجتماعات دورية بمشاركة مكتب إدارة البيانات وممثلي الإدارات المعنية لمتابعة سير التنفيذ وتوثيق القرارات.",
]:
    story.append(Paragraph(ar("•  " + b), bullet_style))
story.append(Spacer(1, 16))

# ---- 6. مؤشرات التقدم ----
story.append(Paragraph(ar("6.  مؤشرات التقدم"), section_style))
story.append(Spacer(1, 6))
story.append(rtl_table(
    ["المؤشر", "القيمة"],
    [
        ("نسبة إنجاز الخطة الإجمالية", "94%"),
        ("عدد الأنشطة المكتملة", "3 من 5"),
        ("عدد الإدارات المشمولة", "5 إدارات"),
    ],
    [110 * mm, 60 * mm],
    status_col=1,
))
story.append(Spacer(1, 16))

# ---- 7. الأدلة الداعمة ----
story.append(Paragraph(ar("7.  الأدلة الداعمة"), section_style))
story.append(Spacer(1, 6))
story.append(rtl_table(
    ["نوع الدليل", "الوصف", "الحالة"],
    [
        ("تقرير حصر مجموعات البيانات", "وثيقة تحتوي القائمة الشاملة لمجموعات البيانات المحصورة", "متوفر"),
        ("سجل ملاك البيانات", "سجل رسمي بأسماء ملاك البيانات ومسؤولياتهم لكل إدارة", "متوفر"),
        ("مواد التدريب والتوعية", "العروض والمواد المستخدمة في ورش التوعية المنفَّذة", "متوفر"),
        ("محاضر اجتماعات المتابعة", "محاضر موثَّقة لاجتماعات متابعة تنفيذ الخطة", "متوفر"),
        ("مسودة إجراءات التصنيف", "المسودة الحالية للإجراءات التشغيلية لتصنيف البيانات", "قيد المراجعة"),
    ],
    [45 * mm, 90 * mm, 30 * mm],
    status_col=2,
))
story.append(Spacer(1, 18))

# ---- 8. الاعتماد ----
story.append(Paragraph(ar("8.  الاعتماد"), section_style))
story.append(Spacer(1, 4))
story.append(Paragraph(ar(
    "هذه الوثيقة مسودة قيد المراجعة، ولم تُعرَض بعد على صاحب الصلاحية للاعتماد الرسمي. "
    "يُستكمَل الاعتماد أدناه عند إقرار المسودة ودمجها ضمن مستودع الأدلة."
), body_style))
story.append(Spacer(1, 8))

approval_headers = ["صاحب الصلاحية", "المسمى الوظيفي", "التوقيع", "التاريخ"]
approval_row = ["...............", "مدير عام الهيئة", "____________", "بانتظار الاعتماد"]
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
    "ملاحظة: هذه الوثيقة مسودة دليل مستقلة ضمن حزمة أدلة تصنيف البيانات الخاصة بهيئة الخدمات الحكومية الذكية (SGSA) لأغراض المراجعة، ولم تُدمَج "
    "بعد ضمن مستودع الأدلة الرسمي."
), note_style))

doc.build(story)
print("Saved:", OUT_PATH)
