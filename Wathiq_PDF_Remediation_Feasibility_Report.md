# Wathiq PDF Remediation Feasibility Report
**Mode:** READ-ONLY forensic investigation. All experiments confined to `TEMP_PDF_REMEDIATION_TEST\` inside the session scratch folder. **The two original PDF files were never opened in write mode and were not modified, saved over, deleted, or renamed at any point in this task.**
**Date:** 2026-08-08

---

## 1. Executive Verdict

# **SAFE TO REMEDIATE**

A complete, correct, text-object-level fix was designed, tested, and forensically verified in an isolated scratch copy of each file. Every glyph required for "Wathiq" and "وثيق" was confirmed present in the documents' own embedded (subsetted) fonts — nothing needed to be invented, substituted, or newly embedded. Page count, page dimensions, fonts, image counts, and all text outside the two target phrases were verified byte-identical to the original on every page of both files. Rendered visual comparison shows correct RTL shaping, correct bold/regular formatting, no shift, no overlap, and no line-break change.

**Important scope note on "safe":** this verdict is about the *content and rendering* safety of the edit. The tool used to apply it (`pypdf`) rewrites the entire PDF object graph rather than patching only the target bytes in place — see Section 4 for what this does and does not affect. No remediation was applied to the real files; this is a feasibility finding only.

---

## 2. File 1 Analysis — `DC.M.3-E02_Data_Owner_Assignment_KPI_Calculation_Record_SGSA.pdf`

| Property | Value |
|---|---|
| Absolute path | `wathiq_portfolio_package\06_DC_M3_KPI_Evidence\DC.M.3-E02_Data_Owner_Assignment_KPI_Calculation_Record_SGSA.pdf` |
| SHA-256 (verified unchanged throughout this task) | `41fb2461703779b56c054270be401442c06bb57c5bb1bbba0c386f05597655b1` |
| Size | 1,398,187 bytes |
| Pages | 4 (all 595.28 × 841.89 pt / A4) |
| Text layer | Fully searchable — no OCR, no image-based text |
| Occurrence(s) | 1, on page 2 — a single paragraph line reading *"...ولا سجل ملاك البيانات ضمن **حزمة معيار (Meyar)** للمتطلب DC.M.2..."* |
| PDF structure | Simple `Tj` operator (not `TJ` — no per-glyph kerning array), operand is **one hex string `<...>` spanning the entire visual line** (66.97pt–538.25pt). This one Tj draws the whole paragraph line, not just the target phrase. |
| Font | `AAAAAA+ArialMT` (regular), TrueType, subsetted, embedded (`FontFile2`), simple 1-byte encoding via a (1,0) cmap subtable — **not** a Unicode cmap; resolved via the font's own `/ToUnicode` CMap |
| Font size | 9.5pt |
| Bounding box of the affected span | `(66.97, 117.82) – (538.25, 127.32)` |
| Recommended method | Byte-level substring replacement inside the hex-string operand of that one `Tj` call — both the ASCII "(Meyar)" bytes and the Arabic "معيار" glyph bytes, which sit adjacent in the same string |

**Glyph availability (font extracted and checked directly, not assumed):**

| Character needed | In font? |
|---|---|
| Latin `W, a, t, h, i, q` | ✅ All present — the font embeds the full printable ASCII range (0x20–0x7E) regardless of which letters were actually used in this document |
| Arabic `و` (isolated), `ث`, `ي` (medial), `ق` (final) — the exact presentation forms `arabic_reshaper`+`bidi` produce for "وثيق" | ✅ All 4 present, confirmed via reverse lookup in the font's own `/ToUnicode` CMap: U+FED6→byte 157, U+FEF4→byte 2, U+FE9B→byte 158, U+FEED→byte 154 |

**Measured impact of the length change:** "(Meyar)" (7 chars) → "(Wathiq)" (8 chars) widens that one `Tj` string by **+3.17pt** at 9.5pt font size (computed from the font's own `hmtx` advance widths — not estimated). The line's right edge moves from x=538.25 to x=541.43, still 53.85pt inside the 595.28pt page width. "معيار" (5 letters) → "وثيق" (4 letters) is 1 character *shorter*, so the two changes' net effect on line length is **within a few points either way** — confirmed empirically in Section 5, not just by calculation.

---

## 3. File 2 Analysis — `DC.C.4.1-E01_دليل_تتبع_وتحقق_تصنيف_الأصول_البيانية_SGSA.pdf`

| Property | Value |
|---|---|
| Absolute path | `wathiq_portfolio_package\06_DC_C4_1_KPI_Evidence\DC.C.4.1-E01_دليل_تتبع_وتحقق_تصنيف_الأصول_البيانية_SGSA.pdf` |
| SHA-256 (verified unchanged throughout this task) | `a08efc9e2a96eca2ddfb22f877370bd18e16deaedce5c9ee8db8b4fcf60902f6` |
| Size | 1,169,616 bytes |
| Pages | 4 |
| Text layer | Fully searchable, no OCR |
| Occurrence(s) | 3 — a repeating page **header** on pages 2, 3, and 4, identical text and identical position on each: `(Meyar) معيار`, bbox `(256.03, 73.05)–(339.23, 88.05)` on every occurrence |
| PDF structure | **Inconsistent encoding across pages within the same file** — pages 2 and 4 draw this header via a literal PDF string with backslash/octal escapes (`\(Meyar\) \011\002\004\201\030`); page 3 draws the identical text via a hex string (`<284d657961722920...>`) inside a much larger (23,887-byte) content stream. Both are simple, isolated `Tj` calls for a short standalone phrase (not a whole-paragraph line like File 1). |
| Font | `AAAAAA+Arial-BoldMT`, TrueType, subsetted, embedded, same 1-byte custom-cmap encoding scheme as File 1 |
| Font size | 15pt |
| Header location | Page-top navy banner — clearly a Header, not Body/Table/Footer/Metadata/Image |

**Glyph availability (font extracted and checked directly):**

| Character needed | In font? |
|---|---|
| Latin `W, a, t, h, i, q` | ✅ All present (byte codes 87, 97, 116, 104, 105, 113) |
| Arabic presentation forms for "وثيق" | ✅ All 4 present (U+FED6→byte 137, U+FEF4→byte 4, U+FE9B→byte 153, U+FEED→byte 28) |

**Recommended method:** two distinct byte-level substitutions are needed per occurrence (the literal-escaped form for pages 2/4, the hex form for page 3) — same logical replacement, different raw encoding.

---

## 4. Proposed Remediation Method

For both files, the safest available technique is a **targeted substring replacement inside the exact `Tj` string operand**, not a full-page redraw and not regenerating the PDF from its generator script (both were ruled out — see Section 6 of the companion feasibility work and the hard-stop rationale from the prior task):

1. Open the PDF read-only, locate the specific content-stream object (of possibly several per page) containing the target bytes.
2. Read the *raw, undecoded-but-defiltered* stream bytes (FlateDecode-decompressed, but not reparsed into abstract PDF operations) — this preserves the original operator/whitespace layout exactly.
3. Perform an exact byte-for-byte substring replacement:
   - `"(Meyar)"` → `"(Wathiq)"` (ASCII bytes, in whichever PDF string encoding that page uses — hex or literal-escaped)
   - `"معيار"` glyph bytes → `"وثيق"` glyph bytes, using byte codes read directly from that font's own `/ToUnicode` CMap (never invented or guessed)
4. Re-compress that one stream and write out a new PDF.

**What this method does *not* do:** it never touches the font program, never re-runs the document generator, never re-flows or redraws the page, and never touches any other content stream, page, or object except the one string being corrected.

**Disclosed limitation of the available tooling:** the library used to write the result (`pypdf`) re-serializes the *entire* PDF object graph on save, not just the one edited stream — this is why the resulting file's total size differs from the original by more than the edit itself would suggest (Section 5). The *rendered content* was exhaustively verified to be unaffected by this, but a purist byte-preserving incremental-update patch would need a lower-level tool than what's available in this environment. This should be disclosed to whoever authorizes the actual fix.

---

## 5. Scratch Experiment

All files below are inside `TEMP_PDF_REMEDIATION_TEST\` (outside `wathiq_portfolio_package\`):

| File | SHA-256 |
|---|---|
| `M3-E02_SCRATCH_TEST_FULL.pdf` | `c8541a7b830a70a4005752603164c1c609ff01ae13282ceda1e00f03ae39482b` |
| `C41-E01_SCRATCH_TEST_FULL.pdf` | `c9ea1e340ef3e5591985618d5618b3670ab188eee5ff52b75a4579884868b310` |

### Text differences (exhaustive — every page checked)

**File 1** — pages 1, 3, 4: **byte-identical extracted text** (0 diff). Page 2 (2184 chars both before/after): the *only* diff line is:
```
- ...( ﻟﻠﻤﺘﻄﻠﺐMeyar)  ﻭﻻ ﺳﺠﻞ ﻣﻼﻙ ﺍﻟﺒﻴﺎﻧﺎﺕ ﺿﻤﻦ ﺣﺰﻣﺔ ﻣﻌﻴﺎﺭDC.C.3.1
+ ...( ﻟﻠﻤﺘﻄﻠﺐWathiq)  ﻭﻻ ﺳﺠﻞ ﻣﻼﻙ ﺍﻟﺒﻴﺎﻧﺎﺕ ﺿﻤﻦ ﺣﺰﻣﺔ ﻭﺛﻴﻖDC.C.3.1
```
(reads correctly, right-to-left, as: *"...للمتطلب Wathiq) ... ضمن حزمة وثيق DC.C.3.1"*)

**File 2** — page 1: byte-identical. Pages 2, 3, 4 (370 / 2891 / 668 chars, unchanged length before/after on each page): the *only* diff on each is:
```
- (Meyar) ﻣﻌﻴﺎﺭ
+ (Wathiq) ﻭﺛﻴﻖ
```

### Structural differences
- Page count: 4 = 4 (both files, both before/after)
- Page dimensions: identical on every page, both files
- Image count: 0 = 0 on every page, both files (no images in either document)
- Font list per page: identical before/after (no font added, removed, or substituted)

### Visual differences
Both files' affected pages were rendered at 3× resolution (before and after) and visually inspected:
- File 1, page 2: line renders in place, correctly right-aligned within the paragraph, no visible shift, overlap, or rewrap of surrounding text.
- File 2, pages 2 and 4: the header banner renders as **"وثيق (Wathiq)"** in bold, in the same position, same size, same color, matching the styling already used correctly elsewhere in the package.
- File 2, page 3: the same header fix renders identically at the top of a page containing a large 30-row table — the table itself (all rows, columns, notes) is visually unaffected.

No shifted text, no missing text, no changed wrapping, no changed table width, no changed alignment, no changed RTL direction, no font substitution, no changed spacing, no changed page breaks, no changed images, no changed margins were found on any page of either file.

### Brand result
- `Meyar` (any case): 1→0 (File 1), 3→0 (File 2)
- `Wathiq`: 0→1 (File 1), 0→3 (File 2)
- `SGSA`: 3→3 (File 1), 1→1 (File 2) — **unchanged**

---

## 6. Safety Assessment

**File 1 — `DC.M.3-E02...pdf`**

| Check | Result |
|---|---|
| Only legacy brand changes | PASS |
| Evidence Codes unchanged | PASS — `DC.C.3.1`, `DC.M.2`, `DC.M.3`, `DC.M.5`, `DC-KPI-02` all confirmed present, unchanged, in the diff context |
| KPI unchanged | PASS |
| Dates unchanged | PASS (no date on the affected line) |
| Numbers unchanged | PASS |
| Tables unchanged | PASS (20-row data-owner table on this page confirmed unaffected in the diff) |
| Page count unchanged | PASS (4 = 4) |
| Layout preserved | PASS (visual render confirms) |
| RTL preserved | PASS |
| SGSA preserved | PASS (3 = 3 occurrences) |
| No unrelated text changes | PASS (single diff line, exact isolated substring) |

**File 2 — `DC.C.4.1-E01...pdf`**

| Check | Result |
|---|---|
| Only legacy brand changes | PASS |
| Evidence Codes unchanged | PASS — `DC.C.3.1`, `DC.C.3.2`, `DC.C.5.1`, `DC.C.4.1`, `KPI-DC-01` confirmed present, unchanged |
| KPI unchanged | PASS |
| Dates unchanged | PASS |
| Numbers unchanged | PASS (the "30 assets" figures on page 3 confirmed unaffected) |
| Tables unchanged | PASS (30-row matching table on page 3 confirmed unaffected) |
| Page count unchanged | PASS (4 = 4) |
| Layout preserved | PASS |
| RTL preserved | PASS |
| SGSA preserved | PASS (1 = 1 occurrence) |
| No unrelated text changes | PASS (identical single-line diff on all 3 affected pages) |

---

## 7. Final Recommendation

# **SAFE TO REMEDIATE — awaiting explicit remediation authorization.**

---

## Answers to the closing questions

1. **Report path:** `C:\Users\extra\Downloads\Wathiq-Data-Management-Platform\Wathiq_PDF_Remediation_Feasibility_Report.md`
2. **Verdict:** SAFE TO REMEDIATE
3. **Is the fix safely possible?** Yes — for both files, confirmed by an actual scratch-copy test and full forensic comparison (text, structure, visuals), not by inference alone.
4. **Why:** every glyph needed for "Wathiq"/"وثيق" was verified present in each document's own embedded font (no missing glyphs, no font patching needed); the required edit is a short, isolated substring inside a single `Tj` string per occurrence; scratch testing showed the change confined to exactly the target phrase on every page, with 0 unrelated differences in text, tables, codes, numbers, dates, page count, layout, RTL, or SGSA.
5. **Files that would be affected if remediation is executed:**
   - `wathiq_portfolio_package\06_DC_M3_KPI_Evidence\DC.M.3-E02_Data_Owner_Assignment_KPI_Calculation_Record_SGSA.pdf`
   - `wathiq_portfolio_package\06_DC_C4_1_KPI_Evidence\DC.C.4.1-E01_دليل_تتبع_وتحقق_تصنيف_الأصول_البيانية_SGSA.pdf`
   No other file needs to change.
6. **Original files confirmed unchanged:** yes — both SHA-256 hashes were re-verified identical at the end of this task (`41fb2461...5b1` and `a08efc9e...02f6`), matching their values from before this investigation began. All test artifacts exist only under `TEMP_PDF_REMEDIATION_TEST\`, outside `wathiq_portfolio_package\`.
