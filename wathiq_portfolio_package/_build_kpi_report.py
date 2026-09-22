"""Builds the KPI Supporting Data Report (Excel) for the Wathiq governance portfolio package.

Synthetic case-study evidence only — not a real government document.
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT_PATH = "01_KPI_Supporting_Data_Report/KPI_Supporting_Data_Report.xlsx"

NAVY = "1F2A44"
GOLD = "B08D57"
LIGHT_GREY = "F2F2F2"
WHITE = "FFFFFF"

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

wb = Workbook()
ws = wb.active
ws.title = "KPI Supporting Data"
ws.sheet_view.showGridLines = False

thin = Side(style="thin", color="D9D9D9")
border = Border(left=thin, right=thin, top=thin, bottom=thin)

# ---- Title block ----
ws.merge_cells("A1:E1")
ws["A1"] = "KPI Supporting Data Report"
ws["A1"].font = Font(name="Calibri", size=16, bold=True, color=WHITE)
ws["A1"].fill = PatternFill("solid", fgColor=NAVY)
ws["A1"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
ws.row_dimensions[1].height = 30

ws.merge_cells("A2:E2")
ws["A2"] = "KPI Supporting Data Report — Data Classification Governance"
ws["A2"].font = Font(name="Calibri", size=12, bold=True, color=NAVY)
ws["A2"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
ws.row_dimensions[2].height = 20

meta_rows = [
    ("Entity (Synthetic Case Study)", "Smart Government Services Authority (SGSA)"),
    ("Department", "Data Management Office"),
    ("Framework", "NDMO Data Governance Framework"),
    ("Requirement Supported", "DC.M.3  •  DC.C.4.1  •  DC.M.12"),
    ("Maturity Reference", "DC.MQ.3 — Level 3 (Activation)"),
    ("Review Cycle", "1 May 2026 – 15 June 2026 (6 Weeks)"),
]
r = 4
for label, value in meta_rows:
    ws.cell(row=r, column=1, value=label).font = Font(name="Calibri", size=10, bold=True, color="595959")
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
    ws.cell(row=r, column=2, value=value).font = Font(name="Calibri", size=10, color="262626")
    r += 1

r += 1
table_header_row = r
headers = ["KPI Name", "Description", "Data Source", "Calculation Method", "Value"]
for c, h in enumerate(headers, start=1):
    cell = ws.cell(row=table_header_row, column=c, value=h)
    cell.font = Font(name="Calibri", size=11, bold=True, color=WHITE)
    cell.fill = PatternFill("solid", fgColor=NAVY)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = border
ws.row_dimensions[table_header_row].height = 22

r += 1
for i, (name, desc, source, calc, value) in enumerate(KPIS):
    row_fill = LIGHT_GREY if i % 2 == 0 else WHITE
    values = [name, desc, source, calc, value]
    for c, v in enumerate(values, start=1):
        cell = ws.cell(row=r, column=c, value=v)
        cell.border = border
        cell.alignment = Alignment(horizontal="left" if c != 5 else "center", vertical="center", wrap_text=True)
        cell.fill = PatternFill("solid", fgColor=row_fill)
        if c == 1:
            cell.font = Font(name="Calibri", size=10, bold=True, color=NAVY)
        elif c == 5:
            cell.font = Font(name="Calibri", size=11, bold=True, color="1F6F43")
        else:
            cell.font = Font(name="Calibri", size=10, color="262626")
    ws.row_dimensions[r].height = 42
    r += 1

r += 1
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
note = ws.cell(
    row=r,
    column=1,
    value=(
        "Note: This document is synthetic case-study evidence produced for the Wathiq governance "
        "portfolio demonstration. It does not represent an actual government entity, a real "
        "compliance submission, or verified production data."
    ),
)
note.font = Font(name="Calibri", size=8, italic=True, color="7F7F7F")
note.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
ws.row_dimensions[r].height = 28

widths = [22, 46, 30, 40, 12]
for i, w in enumerate(widths, start=1):
    ws.column_dimensions[get_column_letter(i)].width = w

wb.save(OUT_PATH)
print("Saved:", OUT_PATH)
