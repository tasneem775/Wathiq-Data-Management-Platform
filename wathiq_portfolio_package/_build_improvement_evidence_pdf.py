"""Builds the Data Classification Improvement Evidence (PDF) for the Wathiq governance portfolio package.

Synthetic case-study evidence only — not a real government document.
"""
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

OUT_PATH = "02_Improvement_Evidence/Data_Classification_Improvement_Evidence.pdf"

NAVY = colors.HexColor("#1F2A44")
GOLD = colors.HexColor("#B08D57")
LIGHT_GREY = colors.HexColor("#F2F2F2")
GREEN = colors.HexColor("#1F6F43")

styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleBar", parent=styles["Normal"], textColor=colors.white,
                              fontName="Helvetica-Bold", fontSize=16, leading=20)
subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], textColor=NAVY,
                                  fontName="Helvetica-Bold", fontSize=13, leading=16)
subtitle2_style = ParagraphStyle("Subtitle2", parent=styles["Normal"], textColor=GOLD,
                                   fontName="Helvetica-Oblique", fontSize=10, leading=13)
meta_label_style = ParagraphStyle("MetaLabel", parent=styles["Normal"], textColor=colors.HexColor("#595959"),
                                    fontName="Helvetica-Bold", fontSize=9)
meta_value_style = ParagraphStyle("MetaValue", parent=styles["Normal"], textColor=colors.HexColor("#262626"),
                                    fontName="Helvetica", fontSize=9)
intro_style = ParagraphStyle("Intro", parent=styles["Normal"], fontName="Helvetica", fontSize=9,
                               textColor=colors.HexColor("#333333"), leading=13)
cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontName="Helvetica", fontSize=8.3, leading=11)
cell_bold_navy = ParagraphStyle("CellBoldNavy", parent=cell_style, textColor=NAVY, fontName="Helvetica-Bold")
cell_status_style = ParagraphStyle("CellStatus", parent=cell_style, textColor=GREEN, fontName="Helvetica-Bold",
                                     alignment=1)
note_style = ParagraphStyle("Note", parent=styles["Normal"], fontName="Helvetica-Oblique", fontSize=7.5,
                              textColor=colors.HexColor("#7F7F7F"), leading=10)

ROWS = [
    (
        "Classification Data Quality",
        "Asset metadata fields (owner, source system, classification date) were captured "
        "inconsistently across departments prior to the review cycle.",
        "A standardized metadata template was applied consistently across all 30 reviewed "
        "assets during the 1 May – 15 June 2026 review cycle.",
        "Review Cycle Records; KPI Supporting Data Report (Review Coverage: 100%)",
        "Completed",
    ),
    (
        "Classification Register Update (DC.C.5.1)",
        "The classification register reflected asset classification levels as they stood "
        "prior to the current review cycle outcome.",
        "The register was updated to reflect the 3 classification changes (downgrades) and "
        "the reconfirmed status of the remaining 26 assets resulting from the review cycle.",
        "Review Decision Log; Updated Classification Register Entries",
        "Completed",
    ),
    (
        "Compliance Monitoring",
        "Review activity was tracked without a consolidated KPI view spanning coverage, "
        "classification changes, and participation.",
        "A consolidated KPI Supporting Data Report was introduced, covering Review Coverage, "
        "Reviewed Assets, Classification Changes, Review Duration, and Data Owners Participation.",
        "KPI Supporting Data Report (supports DC.M.3 / DC.C.4.1 / DC.M.12)",
        "Completed",
    ),
    (
        "Periodic Review Cycle",
        "Classification review activity was not consistently structured within a defined, "
        "recurring cycle with clear start/close-out dates.",
        "A structured 6-week review cycle (1 May 2026 – 15 June 2026) was executed end to end, "
        "engaging 12 data owners across departments and covering all 30 classified assets "
        "(18 data sets, 12 records).",
        "Review Cycle Schedule; Data Owners Participation Log",
        "Completed",
    ),
]

doc = SimpleDocTemplate(
    OUT_PATH, pagesize=landscape(A4),
    leftMargin=18 * mm, rightMargin=18 * mm, topMargin=14 * mm, bottomMargin=14 * mm,
)
story = []

title_tbl = Table([[Paragraph("Data Classification Improvement Evidence Log", title_style)]], colWidths=[doc.width])
title_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), NAVY),
    ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ("TOPPADDING", (0, 0), (-1, -1), 10),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
]))
story.append(title_tbl)
story.append(Spacer(1, 6))
story.append(Paragraph("Data Classification Improvement Evidence", subtitle_style))
story.append(Paragraph("Continuous Improvement Log — Data Classification Governance", subtitle2_style))
story.append(Spacer(1, 10))

meta_rows = [
    ("Entity (Synthetic Case Study)", "Smart Government Services Authority (SGSA)"),
    ("Department", "Data Management Office"),
    ("Framework", "NDMO Data Governance Framework"),
    ("Requirement Supported", "DC.M.4 — Data Classification Plan Review Report"),
    ("Maturity Reference", "DC.MQ.1 — Continuous Improvement of the Classification Plan"),
    ("Review Cycle Referenced", "1 May 2026 – 15 June 2026 (6 Weeks)"),
]
meta_data = [[Paragraph(l, meta_label_style), Paragraph(v, meta_value_style)] for l, v in meta_rows]
meta_tbl = Table(meta_data, colWidths=[55 * mm, doc.width - 55 * mm])
meta_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
story.append(meta_tbl)
story.append(Spacer(1, 10))

story.append(Paragraph(
    "This log records the improvement actions implemented following the 1 May – 15 June 2026 "
    "classification review cycle, in which all 30 classified assets (18 data sets and 12 "
    "records) were reviewed, resulting in 26 confirmed classifications, 3 classification "
    "changes (downgrades), and 1 asset requiring no further action.",
    intro_style,
))
story.append(Spacer(1, 12))

header = ["Improvement Area", "Previous State", "Implemented Improvement", "Supporting Evidence", "Status"]
data = [[Paragraph(h, ParagraphStyle("Head", parent=cell_style, textColor=colors.white,
                                      fontName="Helvetica-Bold", alignment=1)) for h in header]]
for area, prev, impl, evidence, status in ROWS:
    data.append([
        Paragraph(area, cell_bold_navy),
        Paragraph(prev, cell_style),
        Paragraph(impl, cell_style),
        Paragraph(evidence, cell_style),
        Paragraph(status, cell_status_style),
    ])

col_widths = [42 * mm, 58 * mm, 62 * mm, 55 * mm, 22 * mm]
tbl = Table(data, colWidths=col_widths, repeatRows=1)
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
tbl.setStyle(TableStyle(style_cmds))
story.append(tbl)
story.append(Spacer(1, 14))

story.append(Paragraph(
    "Note: This document is synthetic case-study evidence produced for the Wathiq governance "
    "portfolio demonstration. It does not represent an actual government entity, a real "
    "compliance submission, or verified production data.",
    note_style,
))

doc.build(story)
print("Saved:", OUT_PATH)
