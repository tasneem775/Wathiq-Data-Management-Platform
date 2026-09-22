"""Builds the KPI Supporting Data Report (PDF) for the Wathiq governance portfolio package.

Synthetic case-study evidence only — not a real government document.
"""
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

OUT_PATH = "01_KPI_Supporting_Data_Report/KPI_Supporting_Data_Report.pdf"

NAVY = colors.HexColor("#1F2A44")
GOLD = colors.HexColor("#B08D57")
LIGHT_GREY = colors.HexColor("#F2F2F2")
GREEN = colors.HexColor("#1F6F43")

styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleBar", parent=styles["Normal"], textColor=colors.white,
                              fontName="Helvetica-Bold", fontSize=16, leading=20)
subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], textColor=NAVY,
                                  fontName="Helvetica-Bold", fontSize=12, leading=16)
meta_label_style = ParagraphStyle("MetaLabel", parent=styles["Normal"], textColor=colors.HexColor("#595959"),
                                    fontName="Helvetica-Bold", fontSize=9)
meta_value_style = ParagraphStyle("MetaValue", parent=styles["Normal"], textColor=colors.HexColor("#262626"),
                                    fontName="Helvetica", fontSize=9)
cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontName="Helvetica", fontSize=9, leading=12)
cell_bold_navy = ParagraphStyle("CellBoldNavy", parent=cell_style, textColor=NAVY, fontName="Helvetica-Bold")
cell_value_style = ParagraphStyle("CellValue", parent=cell_style, textColor=GREEN, fontName="Helvetica-Bold",
                                    alignment=1, fontSize=11)
note_style = ParagraphStyle("Note", parent=styles["Normal"], fontName="Helvetica-Oblique", fontSize=7.5,
                              textColor=colors.HexColor("#7F7F7F"), leading=10)

KPIS = [
    (
        "Review Coverage",
        "Percentage of classified data assets covered within the current review cycle.",
        "Data Classification Register (Synthetic Case Study)",
        "(Reviewed Assets ÷ Total Assets) × 100",
        "100%",
    ),
    (
        "Reviewed Assets",
        "Total number of data assets (data sets and records) processed through the review cycle.",
        "Review Cycle Records (Synthetic Case Study)",
        "Direct count of assets carried through the review workflow",
        "30",
    ),
    (
        "Classification Changes",
        "Number of assets whose classification level was modified as an outcome of the review.",
        "Review Decision Log (Synthetic Case Study)",
        "Count of assets with a “Modified / Downgraded” review outcome",
        "3",
    ),
    (
        "Review Duration",
        "Total elapsed time required to complete the full review cycle, start to close-out.",
        "Review Cycle Schedule (Synthetic Case Study)",
        "Close-out Date (15 Jun 2026) − Start Date (1 May 2026)",
        "6 Weeks",
    ),
    (
        "Data Owners Participation",
        "Number of data owners actively engaged during the review cycle across departments.",
        "Review Participation Log (Synthetic Case Study)",
        "Direct count of distinct participating data owners",
        "12",
    ),
]

doc = SimpleDocTemplate(
    OUT_PATH, pagesize=landscape(A4),
    leftMargin=18 * mm, rightMargin=18 * mm, topMargin=14 * mm, bottomMargin=14 * mm,
)

story = []

title_tbl = Table(
    [[Paragraph("KPI Supporting Data Report", title_style)]],
    colWidths=[doc.width],
)
title_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), NAVY),
    ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ("TOPPADDING", (0, 0), (-1, -1), 10),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
]))
story.append(title_tbl)
story.append(Spacer(1, 6))
story.append(Paragraph("KPI Supporting Data Report — Data Classification Governance", subtitle_style))
story.append(Spacer(1, 10))

meta_rows = [
    ("Entity (Synthetic Case Study)", "Smart Government Services Authority (SGSA)"),
    ("Department", "Data Management Office"),
    ("Framework", "NDMO Data Governance Framework"),
    ("Requirement Supported", "DC.M.3   •   DC.C.4.1   •   DC.M.12"),
    ("Maturity Reference", "DC.MQ.3 — Level 3 (Activation)"),
    ("Review Cycle", "1 May 2026 – 15 June 2026 (6 Weeks)"),
]
meta_data = [[Paragraph(l, meta_label_style), Paragraph(v, meta_value_style)] for l, v in meta_rows]
meta_tbl = Table(meta_data, colWidths=[55 * mm, doc.width - 55 * mm])
meta_tbl.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
]))
story.append(meta_tbl)
story.append(Spacer(1, 14))

header = ["KPI Name", "Description", "Data Source", "Calculation Method", "Value"]
data = [[Paragraph(h, ParagraphStyle("Head", parent=cell_style, textColor=colors.white,
                                      fontName="Helvetica-Bold", alignment=1)) for h in header]]
for name, desc, source, calc, value in KPIS:
    data.append([
        Paragraph(name, cell_bold_navy),
        Paragraph(desc, cell_style),
        Paragraph(source, cell_style),
        Paragraph(calc, cell_style),
        Paragraph(value, cell_value_style),
    ])

col_widths = [40 * mm, 90 * mm, 60 * mm, 70 * mm, 22 * mm]
kpi_tbl = Table(data, colWidths=col_widths, repeatRows=1)
style_cmds = [
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
]
for i in range(1, len(data)):
    if i % 2 == 0:
        style_cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GREY))
kpi_tbl.setStyle(TableStyle(style_cmds))
story.append(kpi_tbl)
story.append(Spacer(1, 14))

story.append(Paragraph(
    "Note: This document is synthetic case-study evidence produced for the Wathiq governance "
    "portfolio demonstration. It does not represent an actual government entity, a real "
    "compliance submission, or verified production data.",
    note_style,
))

doc.build(story)
print("Saved:", OUT_PATH)
