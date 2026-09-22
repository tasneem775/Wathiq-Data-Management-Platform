"""Builds the Data Classification Improvement Evidence (Word) for the Wathiq governance portfolio package.

Synthetic case-study evidence only — not a real government document.
"""
import docx
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT_PATH = "02_Improvement_Evidence/Data_Classification_Improvement_Evidence.docx"

NAVY = RGBColor(0x1F, 0x2A, 0x44)
GOLD = RGBColor(0xB0, 0x8D, 0x57)
GREY = RGBColor(0x59, 0x59, 0x59)
GREEN = RGBColor(0x1F, 0x6F, 0x43)

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


def set_cell_background(cell, color_hex):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), color_hex)
    cell._tc.get_or_add_tcPr().append(shd)


def add_meta_row(table, label, value):
    row = table.add_row()
    row.cells[0].text = ""
    row.cells[1].text = ""
    p1 = row.cells[0].paragraphs[0]
    r1 = p1.add_run(label)
    r1.font.bold = True
    r1.font.size = Pt(9)
    r1.font.color.rgb = GREY
    p2 = row.cells[1].paragraphs[0]
    r2 = p2.add_run(value)
    r2.font.size = Pt(9)
    r2.font.color.rgb = RGBColor(0x26, 0x26, 0x26)


doc = docx.Document()

section = doc.sections[0]
section.left_margin = Cm(1.8)
section.right_margin = Cm(1.8)
section.top_margin = Cm(1.5)
section.bottom_margin = Cm(1.5)

style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(10)

# ---- Title bar (single-cell table used as a colored banner) ----
banner = doc.add_table(rows=1, cols=1)
banner.autofit = True
cell = banner.rows[0].cells[0]
set_cell_background(cell, "1F2A44")
cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
p = cell.paragraphs[0]
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
run = p.add_run("Data Classification Improvement Evidence Log")
run.font.size = Pt(18)
run.font.bold = True
run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
cell.paragraphs[0].paragraph_format.space_before = Pt(6)
cell.paragraphs[0].paragraph_format.space_after = Pt(6)

doc.add_paragraph()

subtitle = doc.add_paragraph()
r = subtitle.add_run("Data Classification Improvement Evidence")
r.font.size = Pt(14)
r.font.bold = True
r.font.color.rgb = NAVY

sub2 = doc.add_paragraph()
r = sub2.add_run("Continuous Improvement Log — Data Classification Governance")
r.font.size = Pt(11)
r.font.color.rgb = GOLD
r.italic = True

doc.add_paragraph()

meta_table = doc.add_table(rows=0, cols=2)
meta_table.autofit = True
meta_table.columns[0].width = Cm(5)
meta_table.columns[1].width = Cm(11)
add_meta_row(meta_table, "Entity (Synthetic Case Study)", "Smart Government Services Authority (SGSA)")
add_meta_row(meta_table, "Department", "Data Management Office")
add_meta_row(meta_table, "Framework", "NDMO Data Governance Framework")
add_meta_row(meta_table, "Requirement Supported", "DC.M.4 — Data Classification Plan Review Report")
add_meta_row(meta_table, "Maturity Reference", "DC.MQ.1 — Continuous Improvement of the Classification Plan")
add_meta_row(meta_table, "Review Cycle Referenced", "1 May 2026 – 15 June 2026 (6 Weeks)")

doc.add_paragraph()

intro = doc.add_paragraph()
r = intro.add_run(
    "This log records the improvement actions implemented following the 1 May – 15 June 2026 "
    "classification review cycle, in which all 30 classified assets (18 data sets and 12 "
    "records) were reviewed, resulting in 26 confirmed classifications, 3 classification "
    "changes (downgrades), and 1 asset requiring no further action."
)
r.font.size = Pt(9.5)
r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

doc.add_paragraph()

# ---- Improvement table ----
headers = ["Improvement Area", "Previous State", "Implemented Improvement", "Supporting Evidence", "Status"]
table = doc.add_table(rows=1, cols=5)
table.style = "Table Grid"
widths = [Cm(3.2), Cm(4.3), Cm(4.8), Cm(4.0), Cm(1.8)]
for i, w in enumerate(widths):
    table.columns[i].width = w

hdr_cells = table.rows[0].cells
for i, h in enumerate(headers):
    hdr_cells[i].text = ""
    set_cell_background(hdr_cells[i], "1F2A44")
    hdr_cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    p = hdr_cells[i].paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(h)
    r.font.bold = True
    r.font.size = Pt(9.5)
    r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

for idx, (area, prev, impl, evidence, status) in enumerate(ROWS):
    row = table.add_row()
    values = [area, prev, impl, evidence, status]
    for c, v in enumerate(values):
        cell = row.cells[c]
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        if idx % 2 == 0:
            set_cell_background(cell, "F2F2F2")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c == 4 else WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(v)
        run.font.size = Pt(8.5)
        if c == 0:
            run.font.bold = True
            run.font.color.rgb = NAVY
        elif c == 4:
            run.font.bold = True
            run.font.color.rgb = GREEN
        else:
            run.font.color.rgb = RGBColor(0x26, 0x26, 0x26)

for row in table.rows:
    tr = row._tr
    trPr = tr.get_or_add_trPr()
    cant_split = OxmlElement("w:cantSplit")
    trPr.append(cant_split)

doc.add_paragraph()
doc.add_paragraph()

note = doc.add_paragraph()
r = note.add_run(
    "Note: This document is synthetic case-study evidence produced for the Wathiq governance "
    "portfolio demonstration. It does not represent an actual government entity, a real "
    "compliance submission, or verified production data."
)
r.font.size = Pt(7.5)
r.italic = True
r.font.color.rgb = RGBColor(0x7F, 0x7F, 0x7F)

doc.save(OUT_PATH)
print("Saved:", OUT_PATH)
