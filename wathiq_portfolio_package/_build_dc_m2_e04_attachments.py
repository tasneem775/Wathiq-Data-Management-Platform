# -*- coding: utf-8 -*-
"""Builds 3 illustrative visual attachments (PNG) supporting DC.M.2-E04 / E04-A.

These are NOT real evidence — clearly-labeled illustrative audit-attachment
samples, generated as single-page reportlab canvases and rasterized to PNG
via PyMuPDF (fitz). No Word/PDF file is touched. No real people, no photos.

Output folder: 05_DC_M2_Draft_Evidence/DC.M.2-E04_Attachments/
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

OUT_DIR = "05_DC_M2_Draft_Evidence/DC.M.2-E04_Attachments"
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


def ar(text):
    return get_display(arabic_reshaper.reshape(text), base_dir="R")


def draw_seal(c, cx, cy, r=34):
    c.setFillColor(GOLD)
    c.circle(cx, cy, r, stroke=0, fill=1)
    c.setFillColor(GOLD_L)
    c.circle(cx, cy, r - 4, stroke=0, fill=1)
    c.setFont("Arabic-Bold", r * 1.05)
    c.setFillColor(NAVY)
    c.drawCentredString(cx, cy - r * 0.38, "M")


def rasterize(pdf_path, png_path, zoom=3.0):
    doc = fitz.open(pdf_path)
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    pix.save(png_path)
    doc.close()


# ============================================================
# 1) ATTENDANCE CERTIFICATE SAMPLE
# ============================================================
def build_certificate():
    W, H = 1200, 850
    tmp_pdf = os.path.join(TMP_DIR, "_cert.pdf")
    c = rl_canvas.Canvas(tmp_pdf, pagesize=(W, H))

    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # outer + inner decorative border
    c.setStrokeColor(NAVY)
    c.setLineWidth(3)
    c.rect(24, 24, W - 48, H - 48, stroke=1, fill=0)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.2)
    c.rect(34, 34, W - 68, H - 68, stroke=1, fill=0)

    # top navy ribbon
    c.setFillColor(NAVY)
    c.rect(34, H - 130, W - 68, 96, stroke=0, fill=1)
    draw_seal(c, 110, H - 82, r=30)
    c.setFont("Arabic-Bold", 26)
    c.setFillColor(WHITE)
    c.drawRightString(W - 60, H - 72, ar("هيئة الخدمات الحكومية الذكية (SGSA)"))
    c.setFont("Arabic", 13)
    c.setFillColor(GOLD_L)
    c.drawRightString(W - 60, H - 96, ar("هيئة الخدمات الحكومية الذكية (SGSA)"))

    # Title
    c.setFont("Arabic-Bold", 30)
    c.setFillColor(NAVY)
    c.drawCentredString(W / 2, H - 195, ar("شهادة حضور ورشة توعوية حول تصنيف البيانات"))

    c.setStrokeColor(GOLD)
    c.setLineWidth(1.4)
    c.line(W / 2 - 180, H - 214, W / 2 + 180, H - 214)

    # Body text
    c.setFont("Arabic", 15)
    c.setFillColor(GREY)
    c.drawCentredString(W / 2, H - 270, ar("تشهد هيئة الخدمات الحكومية الذكية بأن"))

    c.setFont("Arabic-Bold", 34)
    c.setFillColor(NAVY2)
    c.drawCentredString(W / 2, H - 325, ar("أحمد السالم"))

    c.setFont("Arabic", 15)
    c.setFillColor(GREY)
    c.drawCentredString(W / 2, H - 372, ar("قد حضر ورشة التوعية بعنوان"))

    c.setFont("Arabic-Bold", 20)
    c.setFillColor(NAVY)
    c.drawCentredString(W / 2, H - 408, ar("مفاهيم تصنيف البيانات"))

    c.setFont("Arabic", 14)
    c.setFillColor(GREY)
    c.drawCentredString(W / 2, H - 448, ar("ضمن أنشطة المرحلة الأولى من خطة تصنيف البيانات — مايو 2026"))

    # Approval row
    c.setStrokeColor(colors.HexColor("#C9C2AF"))
    c.setLineWidth(0.8)
    c.line(W / 2 - 470, 210, W / 2 - 90, 210)
    c.line(W / 2 + 90, 210, W / 2 + 470, 210)

    c.setFont("Arabic", 12.5)
    c.setFillColor(GREY)
    c.drawCentredString(W / 2 - 280, 190, ar("الاعتماد"))
    c.setFont("Arabic-Bold", 14)
    c.setFillColor(NAVY)
    c.drawCentredString(W / 2 - 280, 168, ar("مكتب إدارة البيانات (Data Management Office)"))

    c.setFont("Arabic", 12.5)
    c.setFillColor(GREY)
    c.drawCentredString(W / 2 + 280, 190, ar("التاريخ"))
    c.setFont("Arabic-Bold", 14)
    c.setFillColor(NAVY)
    c.drawCentredString(W / 2 + 280, 168, ar("مايو 2026"))

    # footer note
    c.setFont("Arabic", 10.5)
    c.setFillColor(GREY)
    c.drawCentredString(W / 2, 70,
        ar("نموذج توضيحي ضمن حزمة الأدلة، ويستبدل بالنموذج المعتمد عند التطبيق التشغيلي."))
    c.setFont("Arabic", 9)
    c.drawCentredString(W / 2, 52, ar("DC.M.2-E04-A — دليل داعم توضيحي — لا يمثل وثيقة رسمية نهائية"))

    c.save()
    rasterize(tmp_pdf, os.path.join(OUT_DIR, "DC.M.2-E04-A_Attendance_Certificate_Sample.png"))
    os.remove(tmp_pdf)


# ============================================================
# 2) WORKSHOP EXECUTION ILLUSTRATIVE IMAGE (no real people)
# ============================================================
def build_workshop_image():
    W, H = 1280, 720
    tmp_pdf = os.path.join(TMP_DIR, "_workshop.pdf")
    c = rl_canvas.Canvas(tmp_pdf, pagesize=(W, H))

    # room background
    c.setFillColor(colors.HexColor("#F1EEE7"))
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(colors.HexColor("#E7E2D6"))
    c.rect(0, 0, W, H * 0.30, stroke=0, fill=1)  # floor band

    # presentation screen
    screen_w, screen_h = 640, 340
    sx, sy = (W - screen_w) / 2, H - screen_h - 90
    c.setFillColor(colors.HexColor("#0E1220"))
    c.roundRect(sx - 10, sy - 10, screen_w + 20, screen_h + 20, 10, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.roundRect(sx, sy, screen_w, screen_h, 6, stroke=0, fill=1)

    c.setFillColor(GOLD)
    c.rect(sx + 40, sy + screen_h - 70, 60, 6, stroke=0, fill=1)
    c.setFont("Arabic-Bold", 34)
    c.setFillColor(WHITE)
    c.drawString(sx + 40, sy + screen_h - 120, ar("تصنيف البيانات"))
    c.setFont("Arabic", 15)
    c.setFillColor(GOLD_L)
    c.drawString(sx + 40, sy + screen_h - 150, ar("ورشة توعية — المرحلة الأولى"))

    # simple abstract slide content (bars + bullets), not real data
    bar_x = sx + 40
    bar_y = sy + 46
    for i, wfrac in enumerate([0.55, 0.8, 0.4]):
        yy = bar_y + i * 34
        c.setFillColor(colors.HexColor("#334066"))
        c.roundRect(bar_x, yy, (screen_w - 80), 18, 4, stroke=0, fill=1)
        c.setFillColor(GOLD)
        c.roundRect(bar_x, yy, (screen_w - 80) * wfrac, 18, 4, stroke=0, fill=1)

    # screen stand
    c.setFillColor(colors.HexColor("#B9C6DE"))
    c.rect(W / 2 - 8, sy - 60, 16, 50, stroke=0, fill=1)
    c.rect(W / 2 - 60, sy - 66, 120, 10, stroke=0, fill=1)

    # audience: generic flat avatar silhouettes, 3 rows x 6, identical/anonymous
    def avatar(cx, cy, scale=1.0):
        c.setFillColor(colors.HexColor("#7A8AA8"))
        c.circle(cx, cy + 16 * scale, 11 * scale, stroke=0, fill=1)
        c.setFillColor(colors.HexColor("#5B6B8C"))
        p = c.beginPath()
        p.moveTo(cx - 18 * scale, cy - 18 * scale)
        p.curveTo(cx - 18 * scale, cy + 6 * scale, cx - 14 * scale, cy + 8 * scale, cx, cy + 8 * scale)
        p.curveTo(cx + 14 * scale, cy + 8 * scale, cx + 18 * scale, cy + 6 * scale, cx + 18 * scale, cy - 18 * scale)
        p.close()
        c.drawPath(p, stroke=0, fill=1)

    rows = 3
    cols = 8
    start_y = H * 0.30 - 40
    row_gap = 46
    for r in range(rows):
        row_y = start_y - r * row_gap
        row_scale = 1.0 + r * 0.12
        n = cols - r  # fewer in back rows for a subtle perspective feel
        total_w = (n - 1) * (60 + r * 6)
        start_x = W / 2 - total_w / 2
        for i in range(n):
            avatar(start_x + i * (60 + r * 6), row_y, scale=row_scale)

    # caption strip
    c.setFillColor(NAVY)
    c.rect(0, 0, W, 46, stroke=0, fill=1)
    c.setFont("Arabic-Bold", 13)
    c.setFillColor(WHITE)
    c.drawCentredString(W / 2, 16, ar("نموذج توضيحي لتنفيذ ورشة توعية — DC.M.2-E04 — لا يمثل صورة فعلية"))

    c.save()
    rasterize(tmp_pdf, os.path.join(OUT_DIR, "DC.M.2-E04_Workshop_Execution_Screenshot.png"))
    os.remove(tmp_pdf)


# ============================================================
# 3) TRAINING MATERIAL COVER
# ============================================================
def build_training_cover():
    W, H = 850, 1200
    tmp_pdf = os.path.join(TMP_DIR, "_cover.pdf")
    c = rl_canvas.Canvas(tmp_pdf, pagesize=(W, H))

    # background
    c.setFillColor(NAVY)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(NAVY2)
    c.rect(0, 0, W, H * 0.42, stroke=0, fill=1)

    # gold accent band
    c.setFillColor(GOLD)
    c.rect(0, H * 0.42 - 6, W, 6, stroke=0, fill=1)

    # seal
    draw_seal(c, W / 2, H * 0.72, r=64)

    c.setFont("Arabic-Bold", 34)
    c.setFillColor(WHITE)
    c.drawCentredString(W / 2, H * 0.72 - 100, ar("هيئة الخدمات الحكومية الذكية (SGSA)"))
    c.setFont("Arabic", 14)
    c.setFillColor(GOLD_L)
    c.setFont("Arabic", 12)
    c.drawCentredString(W / 2, H * 0.72 - 128, ar("منصة ذكية لإدارة وقياس الامتثال لمتطلبات المكتب الوطني لإدارة البيانات (NDMO)"))

    # main title block
    c.setFont("Arabic-Bold", 46)
    c.setFillColor(WHITE)
    c.drawCentredString(W / 2, H * 0.42 + 120, ar("دليل التوعية"))
    c.drawCentredString(W / 2, H * 0.42 + 60, ar("بتصنيف البيانات"))

    c.setStrokeColor(GOLD)
    c.setLineWidth(1.4)
    c.line(W / 2 - 120, H * 0.42 + 30, W / 2 + 120, H * 0.42 + 30)

    # lower info block
    c.setFont("Arabic", 15)
    c.setFillColor(colors.HexColor("#C9D2E5"))
    c.drawCentredString(W / 2, 210, ar("إطار حوكمة البيانات الوطني (NDMO)"))
    c.setFont("Arabic-Bold", 17)
    c.setFillColor(GOLD_L)
    c.drawCentredString(W / 2, 178, ar("DC.M.2 — دليل داعم توضيحي"))

    c.setFont("Arabic", 10.5)
    c.setFillColor(colors.HexColor("#8C97B5"))
    c.drawCentredString(W / 2, 70, ar("نموذج غلاف توضيحي ضمن حزمة الأدلة — DC.M.2-E04"))

    c.save()
    rasterize(tmp_pdf, os.path.join(OUT_DIR, "DC.M.2-E04_Training_Material_Cover.png"))
    os.remove(tmp_pdf)


if __name__ == "__main__":
    build_certificate()
    build_workshop_image()
    build_training_cover()
    print("All 3 attachments saved to:", OUT_DIR)
