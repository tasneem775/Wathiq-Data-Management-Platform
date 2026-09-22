# -*- coding: utf-8 -*-
"""PDF twins of the 7 DC.M.12 KPI docx records — same content, same Wathiq/SGSA identity.
See _build_dc_m12_kpi_docx.py / _dc_m12_kpi_data.py for the shared data and rationale.
"""
import os
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

from _dc_m12_kpi_data import RECORDS, DOC_META_COMMON

OUT_DIR = "06_DC_M12_KPI_Evidence"

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


title_style = ParagraphStyle("TitleBar", fontName="Arabic-Bold", fontSize=15, leading=19, textColor=colors.white, alignment=2)
subtitle_bar_style = ParagraphStyle("SubtitleBar", fontName="Arabic-Bold", fontSize=9.5, leading=14, textColor=colors.white, alignment=2)
report_title_style = ParagraphStyle("ReportTitle", fontName="Arabic-Bold", fontSize=12.5, leading=17, textColor=NAVY, alignment=2)
draft_style = ParagraphStyle("Draft", fontName="Arabic", fontSize=10, leading=13, textColor=GOLD, alignment=2)
section_style = ParagraphStyle("Section", fontName="Arabic-Bold", fontSize=12, leading=15, textColor=NAVY, alignment=2, spaceBefore=6)
subhead_style = ParagraphStyle("Subhead", fontName="Arabic-Bold", fontSize=10, leading=14, textColor=NAVY, alignment=2)
meta_label_style = ParagraphStyle("MetaLabel", fontName="Arabic-Bold", fontSize=9, textColor=colors.HexColor("#595959"), alignment=2)
meta_value_style = ParagraphStyle("MetaValue", fontName="Arabic", fontSize=9, leading=13, textColor=colors.HexColor("#262626"), alignment=2)
body_style = ParagraphStyle("Body", fontName="Arabic", fontSize=9.5, leading=15, textColor=colors.HexColor("#262626"), alignment=2)
note_style = ParagraphStyle("Note", fontName="Arabic", fontSize=8, leading=12, textColor=colors.HexColor("#595959"), alignment=2, italic=1)
cell_style = ParagraphStyle("Cell", fontName="Arabic", fontSize=7.4, leading=10.5, alignment=2, textColor=colors.HexColor("#262626"))
cell_bold_navy = ParagraphStyle("CellBoldNavy", parent=cell_style, fontName="Arabic-Bold", textColor=NAVY, alignment=1)
head_cell_style = ParagraphStyle("HeadCell", fontName="Arabic-Bold", fontSize=8.4, alignment=1, textColor=colors.white)


def status_style(v):
    color = GREEN if str(v) in ("تثبيت التصنيف", "مُنشور", "محقق") else AMBER
    return ParagraphStyle("Status", parent=cell_style, fontName="Arabic-Bold", alignment=1, textColor=color)


def rtl_table(headers_ar, rows, col_widths_ltr, status_col=None):
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


def simple_kv_table(rows, col_widths_ltr, status_col=None):
    return rtl_table(["البند", "القيمة"], rows, col_widths_ltr, status_col=status_col)


def build_record(rec):
    out_path = os.path.join(OUT_DIR, rec["docx_name"] + ".pdf")
    is_calc = rec["record_type"] == "calculation"

    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
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

    # ---- غلاف ----
    title_tbl = Table(
        [[Paragraph(ar("منصة ذكية لإدارة وقياس الامتثال لمتطلبات المكتب الوطني لإدارة البيانات (NDMO)"), subtitle_bar_style)],
         [Paragraph(ar("هيئة الخدمات الحكومية الذكية (SGSA)"), title_style)]],
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

    record_type_ar = "سجل احتساب" if is_calc else "سجل إثبات"
    story.append(ar_p(f"{record_type_ar} مؤشر «{rec['kpi_name_ar']}» ({rec['kpi_code']})", report_title_style, FULL_W))
    suffix_en = "KPI Calculation Record" if is_calc else "KPI Evidence Record"
    story.append(Paragraph(ar(f"{rec['kpi_name_en']} — {suffix_en}"), draft_style))
    story.append(Spacer(1, 10))

    story.append(meta_table_ar([
        ("الجهة", DOC_META_COMMON["entity"]),
        ("المنصة", DOC_META_COMMON["platform"]),
        ("الإطار المرجعي", DOC_META_COMMON["framework"]),
        ("رمز الدليل", rec["doc_code"]),
        ("المتطلب المرتبط", DOC_META_COMMON["related_requirement"]),
        ("المؤشر المرتبط", f"{rec['kpi_code']} — {rec['kpi_name_ar']}"),
        ("نوع السجل", "سجل احتساب (Calculation Record)" if is_calc else "سجل إثبات (Evidence Record)"),
        ("الإصدار", DOC_META_COMMON["version"]),
        ("التاريخ", DOC_META_COMMON["date"]),
        ("حالة الوثيقة", DOC_META_COMMON["status"]),
    ]))
    story.append(PageBreak())

    # ---- 1. نطاق القياس ----
    story.append(Paragraph(ar("1.  نطاق القياس"), section_style))
    story.append(Spacer(1, 4))
    story.append(ar_p(rec["scope"], body_style, FULL_W))
    story.append(Spacer(1, 12))

    # ---- 2. مصادر البيانات ----
    story.append(Paragraph(ar("2.  مصادر البيانات"), section_style))
    story.append(Spacer(1, 4))
    story.append(ar_p(
        "تعتمد بيانات هذا السجل حصراً على الوثائق التالية، وهي الوثائق الثلاث الوحيدة "
        "المعتمدة كمصدر بيانات فعلي لأدلة مؤشرات DC.M.12؛ أما DC.M.12 ذاته فيُستخدم فقط "
        "للتحقق من مطابقة النتيجة النهائية، دون استخدامه كمصدر بيانات خام:",
        body_style, FULL_W,
    ))
    story.append(Spacer(1, 4))
    for s in rec["sources"]:
        story.append(ar_p("•  " + s, body_style, FULL_W))
        story.append(Spacer(1, 3))
    story.append(Spacer(1, 10))

    # ---- 3. جدول البيانات المستخدمة ----
    story.append(Paragraph(ar("3.  جدول البيانات المستخدمة"), section_style))
    story.append(Spacer(1, 4))
    story.append(ar_p(rec["data_table_note"], body_style, FULL_W))
    story.append(Spacer(1, 6))
    col_widths_mm = [w * 10 for w in rec["data_table_col_widths_cm"]]
    # scale to fit page width
    scale = FULL_W / (sum(col_widths_mm) * mm)
    col_widths_scaled = [w * mm * scale for w in col_widths_mm]
    status_col = rec["data_table_status_col"][0] if rec["data_table_status_col"] else None
    story.append(rtl_table(rec["data_table_headers"], rec["data_table_rows"], col_widths_scaled, status_col=status_col))
    story.append(PageBreak())

    section_num = 4

    if is_calc:
        calc = rec["calc"]
        story.append(Paragraph(ar(f"{section_num}.  تطبيق المعادلة"), section_style))
        story.append(Spacer(1, 6))
        story.append(simple_kv_table(
            [
                (calc["numerator_label"], calc["numerator_value"]),
                (calc["denominator_label"], calc["denominator_value"]),
                ("المعادلة", calc["formula_text"]),
                ("تطبيق المعادلة", calc["application_text"]),
                ("النتيجة النهائية", calc["result"]),
            ],
            [FULL_W * 0.6, FULL_W * 0.4],
            status_col=1,
        ))
        if rec.get("calc_note"):
            story.append(Spacer(1, 6))
            story.append(ar_p(rec["calc_note"], note_style, FULL_W))
        story.append(Spacer(1, 14))
        section_num += 1
    else:
        story.append(Paragraph(ar(f"{section_num}.  القيمة المُثبَتة وحدود البيانات المتاحة"), section_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(ar("القيمة الإجمالية كما وردت في المصدر:"), subhead_style))
        story.append(Spacer(1, 3))
        story.append(ar_p(rec["evidence_reported_value"], body_style, FULL_W))
        story.append(Spacer(1, 8))
        story.append(Paragraph(ar("ملاحظة بشأن البيانات التفصيلية غير المتاحة:"), subhead_style))
        story.append(Spacer(1, 3))
        story.append(ar_p(rec["evidence_unavailable_note"], note_style, FULL_W))
        story.append(Spacer(1, 14))
        section_num += 1

    # ---- النتيجة والتحقق مقابل DC.M.12 ----
    story.append(Paragraph(ar(f"{section_num}.  النتيجة والتحقق مقابل DC.M.12"), section_style))
    story.append(Spacer(1, 6))
    story.append(simple_kv_table(
        [
            ("القيمة المستهدفة (DC.M.12)", rec["target"]),
            ("القيمة الفعلية المُثبَتة في DC.M.12", rec["dcm12_actual"]),
            ("حالة الإنجاز في DC.M.12", rec["dcm12_status"]),
            ("مرجع التحقق في DC.M.12", rec["dcm12_ref"]),
        ],
        [FULL_W * 0.42, FULL_W * 0.58],
        status_col=1,
    ))
    story.append(Spacer(1, 8))
    story.append(ar_p(rec["verification_text"], body_style, FULL_W))
    story.append(Spacer(1, 16))
    section_num += 1

    # ---- الاعتماد ----
    story.append(Paragraph(ar(f"{section_num}.  الاعتماد"), section_style))
    story.append(Spacer(1, 4))
    sources_short = " و".join(s.split(" — ")[0] for s in rec["sources"])
    story.append(ar_p(
        "تمت مراجعة هذا السجل من مكتب إدارة البيانات، وتم التحقق من مطابقة البيانات "
        f"الواردة فيه لمحتوى {sources_short} دون أي إضافة أو حذف أو تعديل، ومن مطابقة "
        "نتيجته النهائية للقيمة الفعلية الموثقة في DC.M.12.",
        body_style, FULL_W,
    ))
    story.append(Spacer(1, 8))

    approval_headers = ["صاحب الصلاحية", "المسمى الوظيفي", "التوقيع", "التاريخ"]
    approval_row = ["________________", "مدير مكتب إدارة البيانات", "________________", "________________"]
    approval_head_cells = [Paragraph(ar(h), head_cell_style) for h in reversed(approval_headers)]
    approval_data_cells = [Paragraph(ar(v), ParagraphStyle("AppCell", fontName="Arabic", fontSize=9, alignment=1)) for v in reversed(approval_row)]
    approval_tbl = Table([approval_head_cells, approval_data_cells], colWidths=[FULL_W / 4] * 4)
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
        f"ملاحظة: هذا السجل دليل داعم مستقل ضمن حزمة أدلة تصنيف البيانات الخاصة بهيئة الخدمات الحكومية الذكية (SGSA)، أُعدّ لتوثيق بيانات "
        f"وطريقة {'احتساب' if is_calc else 'إثبات'} مؤشر {rec['kpi_code']} دون تعديل أي "
        "محتوى في تقرير DC.M.12 أو الوثائق المصدر.",
        note_style, FULL_W,
    ))

    doc.build(story)
    print("Saved:", out_path)


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    for rec in RECORDS:
        build_record(rec)
