# -*- coding: utf-8 -*-
"""Builds 4 illustrative visual attachments (PNG) supporting DC.M.2-E03 only.

All content (dates, objectives, attendee roles, topics, decisions) is reused
VERBATIM from the existing DC.M.2-E03 meeting minutes — nothing new is invented.
No Word/PDF file is touched. No real people. Wathiq visual identity.

Output folder: 05_DC_M2_Draft_Evidence/DC.M.2-E03_Attachments/
"""
import os
import tempfile
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import fitz

OUT_DIR = "05_DC_M2_Draft_Evidence/DC.M.2-E03_Attachments"
TMP_DIR = os.path.join(tempfile.gettempdir(), "wathiq_portfolio_build")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)

pdfmetrics.registerFont(TTFont("Arabic", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arabic-Bold", r"C:\Windows\Fonts\arialbd.ttf"))

NAVY = colors.HexColor("#1F2A44")
NAVY2 = colors.HexColor("#2E3D63")
GOLD = colors.HexColor("#AB8654")
GOLD_L = colors.HexColor("#D8B37C")
PAPER = colors.HexColor("#FBFAF7")
GREY = colors.HexColor("#595959")
LIGHT = colors.HexColor("#EDEAE2")
WHITE = colors.white

# ---- Verbatim content reused from DC.M.2-E03 (no new data) ----
ATTENDEES = [
    "مدير مكتب إدارة البيانات",
    "ممثل إدارة الموارد البشرية",
    "ممثل الإدارة المالية",
    "ممثل إدارة تقنية المعلومات",
    "ممثل إدارة الخدمات الرقمية",
]

MEETING1 = {
    "title": "محضر اجتماع متابعة تنفيذ خطة تصنيف البيانات رقم (1)",
    "date": "01 مايو 2026",
    "objective": "متابعة بدء تنفيذ خطة تصنيف البيانات.",
    "topics": [
        "مراجعة خطة التنفيذ.",
        "متابعة حصر مجموعات البيانات والسجلات.",
        "متابعة تحديد ملاك البيانات.",
    ],
}

ALL_DECISIONS = [
    ("1", "01 مايو 2026", "اعتماد بدء تنفيذ أنشطة الخطة."),
    ("1", "01 مايو 2026", "استكمال أعمال حصر البيانات."),
    ("1", "01 مايو 2026", "متابعة تحديث سجل ملاك البيانات."),
    ("2", "30 مايو 2026", "تأكيد اكتمال حصر مجموعات البيانات."),
    ("2", "30 مايو 2026", "متابعة استكمال الأنشطة المتبقية."),
    ("3", "15 يونيو 2026", "توثيق نتائج التنفيذ."),
    ("3", "15 يونيو 2026", "رفع حالة التنفيذ ضمن تقرير المتابعة."),
]


def ar(text):
    return get_display(arabic_reshaper.reshape(text), base_dir="R")


def draw_seal(c, cx, cy, r=30):
    c.setFillColor(GOLD)
    c.circle(cx, cy, r, stroke=0, fill=1)
    c.setFillColor(GOLD_L)
    c.circle(cx, cy, r - 4, stroke=0, fill=1)
    c.setFont("Arabic-Bold", r * 1.05)
    c.setFillColor(NAVY)
    c.drawCentredString(cx, cy - r * 0.38, "M")


def header_band(c, W, H, band_h=96):
    c.setFillColor(NAVY)
    c.rect(34, H - 34 - band_h, W - 68, band_h, stroke=0, fill=1)
    draw_seal(c, 110, H - 34 - band_h / 2, r=26)
    c.setFont("Arabic-Bold", 22)
    c.setFillColor(WHITE)
    c.drawRightString(W - 60, H - 34 - band_h / 2 + 8, ar("هيئة الخدمات الحكومية الذكية (SGSA)"))
    c.setFont("Arabic", 11.5)
    c.setFillColor(GOLD_L)
    c.drawRightString(W - 60, H - 34 - band_h / 2 - 14, ar("هيئة الخدمات الحكومية الذكية (SGSA)"))


def outer_frame(c, W, H):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setStrokeColor(NAVY)
    c.setLineWidth(2.4)
    c.rect(20, 20, W - 40, H - 40, stroke=1, fill=0)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.rect(28, 28, W - 56, H - 56, stroke=1, fill=0)


def rasterize(pdf_path, png_path, zoom=3.0):
    doc = fitz.open(pdf_path)
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    pix.save(png_path)
    doc.close()


def footer_notes(c, W, lines, y0=64):
    c.setFont("Arabic", 10)
    c.setFillColor(GREY)
    for i, line in enumerate(lines):
        c.drawCentredString(W / 2, y0 - i * 16, ar(line))


# ============================================================
# 1) MEETING INVITATION (based on Meeting No. 1)
# ============================================================
def build_invitation():
    W, H = 850, 1200
    tmp = os.path.join(TMP_DIR, "_inv.pdf")
    c = rl_canvas.Canvas(tmp, pagesize=(W, H))
    outer_frame(c, W, H)
    header_band(c, W, H)

    top = H - 190
    c.setFont("Arabic-Bold", 22)
    c.setFillColor(NAVY)
    c.drawCentredString(W / 2, top, ar("دعوة حضور اجتماع متابعة تنفيذ خطة تصنيف البيانات"))
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.2)
    c.line(W / 2 - 160, top - 18, W / 2 + 160, top - 18)

    c.setFont("Arabic", 11.5)
    c.setFillColor(GREY)
    c.drawCentredString(W / 2, top - 48, ar("مرجع: " + MEETING1["title"] + " — DC.M.2-E03"))

    body_y = top - 100
    c.setFont("Arabic", 13)
    c.setFillColor(colors.HexColor("#262626"))
    c.drawRightString(W - 90, body_y, ar(
        "يسر مكتب إدارة البيانات دعوتكم لحضور اجتماع متابعة تنفيذ خطة تصنيف البيانات،"))
    c.drawRightString(W - 90, body_y - 22, ar("وذلك وفق التفاصيل التالية:"))

    fields_y = body_y - 70
    def field(label, value, dy):
        c.setFont("Arabic-Bold", 12.5)
        c.setFillColor(NAVY)
        c.drawRightString(W - 90, fields_y - dy, ar(label))
        c.setFont("Arabic", 12.5)
        c.setFillColor(colors.HexColor("#262626"))
        c.drawRightString(W - 90, fields_y - dy - 20, ar(value))

    field("التاريخ:", MEETING1["date"], 0)
    field("الهدف من الاجتماع:", MEETING1["objective"], 55)

    c.setFont("Arabic-Bold", 12.5)
    c.setFillColor(NAVY)
    c.drawRightString(W - 90, fields_y - 130, ar("الحضور المدعوون:"))

    ly = fields_y - 160
    c.setFont("Arabic", 12)
    c.setFillColor(colors.HexColor("#262626"))
    for a in ATTENDEES:
        c.drawRightString(W - 110, ly, ar("•  " + a))
        ly -= 24

    c.setStrokeColor(colors.HexColor("#C9C2AF"))
    c.setLineWidth(0.7)
    c.line(90, ly - 30, W - 90, ly - 30)

    footer_notes(c, W, [
        "نموذج توضيحي ضمن حزمة الأدلة الداعمة لـ DC.M.2-E03، ولا يمثل مراسلة رسمية فعلية.",
        "DC.M.2-E03 — دليل داعم توضيحي — لا يمثل وثيقة رسمية نهائية",
    ])
    c.save()
    rasterize(tmp, os.path.join(OUT_DIR, "DC.M.2-E03_Meeting_Invitation_Sample.png"))
    os.remove(tmp)


# ============================================================
# 2) MEETING AGENDA (based on Meeting No. 1)
# ============================================================
def build_agenda():
    W, H = 850, 1200
    tmp = os.path.join(TMP_DIR, "_agenda.pdf")
    c = rl_canvas.Canvas(tmp, pagesize=(W, H))
    outer_frame(c, W, H)
    header_band(c, W, H)

    top = H - 190
    c.setFont("Arabic-Bold", 20)
    c.setFillColor(NAVY)
    c.drawCentredString(W / 2, top, ar("جدول أعمال اجتماع متابعة تنفيذ خطة تصنيف البيانات رقم (1)"))
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.2)
    c.line(W / 2 - 180, top - 18, W / 2 + 180, top - 18)

    c.setFont("Arabic", 12)
    c.setFillColor(GREY)
    c.drawCentredString(W / 2, top - 46, ar(f"التاريخ: {MEETING1['date']}"))
    c.drawCentredString(W / 2, top - 66, ar(f"الهدف: {MEETING1['objective']}"))

    # agenda table
    tbl_top = top - 110
    row_h = 46
    col1_w, col2_w = 60, W - 180 - 60
    x0 = 90
    c.setFillColor(NAVY)
    c.rect(x0, tbl_top - row_h, W - 180, row_h, stroke=0, fill=1)
    c.setFont("Arabic-Bold", 12.5)
    c.setFillColor(WHITE)
    c.drawCentredString(x0 + col1_w / 2, tbl_top - row_h / 2 - 5, ar("م"))
    c.drawCentredString(x0 + col1_w + col2_w / 2, tbl_top - row_h / 2 - 5, ar("بند جدول الأعمال"))

    y = tbl_top - row_h
    for i, topic in enumerate(MEETING1["topics"], start=1):
        y2 = y - row_h
        fill = LIGHT if i % 2 == 1 else WHITE
        c.setFillColor(fill)
        c.rect(x0, y2, W - 180, row_h, stroke=0, fill=1)
        c.setStrokeColor(colors.HexColor("#D9D9D9"))
        c.setLineWidth(0.6)
        c.rect(x0, y2, W - 180, row_h, stroke=1, fill=0)
        c.setFont("Arabic-Bold", 12)
        c.setFillColor(NAVY)
        c.drawCentredString(x0 + col1_w / 2, y2 + row_h / 2 - 5, str(i))
        c.setFont("Arabic", 12)
        c.setFillColor(colors.HexColor("#262626"))
        c.drawRightString(x0 + col1_w + col2_w - 12, y2 + row_h / 2 - 5, ar(topic))
        y = y2

    footer_notes(c, W, [
        "نموذج توضيحي ضمن حزمة الأدلة الداعمة لـ DC.M.2-E03، ولا يمثل مراسلة رسمية فعلية.",
        "DC.M.2-E03 — دليل داعم توضيحي — لا يمثل وثيقة رسمية نهائية",
    ])
    c.save()
    rasterize(tmp, os.path.join(OUT_DIR, "DC.M.2-E03_Meeting_Agenda_Sample.png"))
    os.remove(tmp)


# ============================================================
# 3) MEETING EXECUTION ILLUSTRATIVE IMAGE (no real people)
# ============================================================
def build_execution_image():
    W, H = 1280, 720
    tmp = os.path.join(TMP_DIR, "_meeting_exec.pdf")
    c = rl_canvas.Canvas(tmp, pagesize=(W, H))

    c.setFillColor(colors.HexColor("#F1EEE7"))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # background screen/whiteboard
    screen_w, screen_h = 520, 230
    sx, sy = (W - screen_w) / 2, H - screen_h - 110
    c.setFillColor(colors.HexColor("#0E1220"))
    c.roundRect(sx - 8, sy - 8, screen_w + 16, screen_h + 16, 8, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.roundRect(sx, sy, screen_w, screen_h, 5, stroke=0, fill=1)
    c.setFillColor(GOLD)
    c.rect(sx + 30, sy + screen_h - 56, 50, 5, stroke=0, fill=1)
    c.setFont("Arabic-Bold", 22)
    c.setFillColor(WHITE)
    c.drawString(sx + 30, sy + screen_h - 92, ar("متابعة تنفيذ خطة تصنيف البيانات"))
    c.setFont("Arabic", 12)
    c.setFillColor(GOLD_L)
    c.drawString(sx + 30, sy + screen_h - 114, ar("اجتماع متابعة — DC.M.2-E03"))

    # meeting table (oval-ish rounded rect) viewed from above
    table_w, table_h = 520, 160
    tx, ty = (W - table_w) / 2, 150
    c.setFillColor(colors.HexColor("#C9BFA5"))
    c.roundRect(tx, ty, table_w, table_h, table_h / 2, stroke=0, fill=1)
    c.setFillColor(colors.HexColor("#B9AE8F"))
    c.roundRect(tx + 14, ty + 14, table_w - 28, table_h - 28, (table_h - 28) / 2, stroke=0, fill=1)

    # abstract generic seated attendee icons around the table (5 = attendee count)
    def avatar(cx, cy, scale=1.0):
        c.setFillColor(colors.HexColor("#7A8AA8"))
        c.circle(cx, cy + 15 * scale, 10 * scale, stroke=0, fill=1)
        c.setFillColor(colors.HexColor("#5B6B8C"))
        p = c.beginPath()
        p.moveTo(cx - 16 * scale, cy - 16 * scale)
        p.curveTo(cx - 16 * scale, cy + 6 * scale, cx - 12 * scale, cy + 7 * scale, cx, cy + 7 * scale)
        p.curveTo(cx + 12 * scale, cy + 7 * scale, cx + 16 * scale, cy + 6 * scale, cx + 16 * scale, cy - 16 * scale)
        p.close()
        c.drawPath(p, stroke=0, fill=1)

    n = len(ATTENDEES)
    positions_x = [tx + 40 + i * (table_w - 80) / (n - 1) for i in range(n)]
    for i, px in enumerate(positions_x):
        avatar(px, ty + table_h + 46, scale=1.05)

    # caption strip
    c.setFillColor(NAVY)
    c.rect(0, 0, W, 42, stroke=0, fill=1)
    c.setFont("Arabic-Bold", 12.5)
    c.setFillColor(WHITE)
    c.drawCentredString(W / 2, 15, ar(
        "نموذج توضيحي لاجتماعات المتابعة — DC.M.2-E03 — لا يمثل صورة فعلية لأشخاص"))

    c.save()
    rasterize(tmp, os.path.join(OUT_DIR, "DC.M.2-E03_Meeting_Execution_Screenshot.png"))
    os.remove(tmp)


# ============================================================
# 4) DECISION LOG (all 7 decisions across the 3 real meetings)
# ============================================================
def build_decision_log():
    W, H = 1100, 850
    tmp = os.path.join(TMP_DIR, "_decisions.pdf")
    c = rl_canvas.Canvas(tmp, pagesize=(W, H))
    outer_frame(c, W, H)
    header_band(c, W, H, band_h=88)

    top = H - 176
    c.setFont("Arabic-Bold", 21)
    c.setFillColor(NAVY)
    c.drawCentredString(W / 2, top, ar("سجل القرارات — محاضر اجتماعات متابعة تنفيذ خطة تصنيف البيانات"))
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.2)
    c.line(W / 2 - 220, top - 16, W / 2 + 220, top - 16)
    c.setFont("Arabic", 11)
    c.setFillColor(GREY)
    c.drawCentredString(W / 2, top - 40, ar("DC.M.2-E03 — إجمالي القرارات الموثَّقة عبر الاجتماعات الثلاثة: 7 قرارات"))

    # table
    x0, tbl_top = 70, top - 74
    col_meet, col_date, col_dec = 90, 140, W - 140 - 90 - 140
    row_h = 44
    headers = ["رقم الاجتماع", "التاريخ", "القرار"]
    c.setFillColor(NAVY)
    c.rect(x0, tbl_top - row_h, W - 140, row_h, stroke=0, fill=1)
    c.setFont("Arabic-Bold", 11.5)
    c.setFillColor(WHITE)
    c.drawCentredString(x0 + col_meet / 2, tbl_top - row_h / 2 - 5, ar(headers[0]))
    c.drawCentredString(x0 + col_meet + col_date / 2, tbl_top - row_h / 2 - 5, ar(headers[1]))
    c.drawCentredString(x0 + col_meet + col_date + col_dec / 2, tbl_top - row_h / 2 - 5, ar(headers[2]))

    y = tbl_top - row_h
    for i, (meet_no, date, decision) in enumerate(ALL_DECISIONS):
        y2 = y - row_h
        fill = LIGHT if i % 2 == 0 else WHITE
        c.setFillColor(fill)
        c.rect(x0, y2, W - 140, row_h, stroke=0, fill=1)
        c.setStrokeColor(colors.HexColor("#D9D9D9"))
        c.setLineWidth(0.6)
        c.rect(x0, y2, W - 140, row_h, stroke=1, fill=0)

        c.setFont("Arabic-Bold", 11.5)
        c.setFillColor(NAVY)
        c.drawCentredString(x0 + col_meet / 2, y2 + row_h / 2 - 5, meet_no)
        c.setFont("Arabic", 10.5)
        c.setFillColor(colors.HexColor("#262626"))
        c.drawCentredString(x0 + col_meet + col_date / 2, y2 + row_h / 2 - 5, ar(date))
        c.drawRightString(x0 + col_meet + col_date + col_dec - 12, y2 + row_h / 2 - 5, ar(decision))
        y = y2

    footer_notes(c, W, [
        "نموذج توضيحي ضمن حزمة الأدلة الداعمة لـ DC.M.2-E03، ويعكس القرارات الموثقة فعلياً في المحاضر الثلاثة.",
        "DC.M.2-E03 — دليل داعم توضيحي — لا يمثل وثيقة رسمية نهائية",
    ], y0=y - 30)
    c.save()
    rasterize(tmp, os.path.join(OUT_DIR, "DC.M.2-E03_Decision_Log_Sample.png"))
    os.remove(tmp)


if __name__ == "__main__":
    build_invitation()
    build_agenda()
    build_execution_image()
    build_decision_log()
    print("All 4 attachments saved to:", OUT_DIR)
