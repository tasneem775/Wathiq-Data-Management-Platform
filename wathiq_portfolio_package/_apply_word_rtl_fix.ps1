# Build tool — genuine Word-native RTL finishing pass for python-docx-generated .docx files.
#
# WHY THIS EXISTS: python-docx can only write raw w:bidi / w:bidiVisual OOXML elements. Even
# when those elements are present and schema-ordered correctly, real Microsoft Word has been
# observed to still render the paragraph/table as LTR (verified via COM: ParagraphFormat.
# ReadingOrder read back as 0/LTR on a from-python-docx file that nonetheless contained
# w:bidi). The only verified-reliable fix is to have Word itself set and persist the
# right-to-left reading order, since Word is both the writer and the reader that matters.
#
# WHAT IT DOES (formatting only — never touches text): opens the given .docx in real Word via
# COM, sets ParagraphFormat.ReadingOrder = wdReadingOrderRtl (1) on every paragraph in the main
# body (this also covers every table-cell paragraph, since Document.Paragraphs includes them),
# and on every header/footer paragraph across all sections, then saves in place (same path,
# same .docx format).
#
# USAGE:
#   powershell -File _apply_word_rtl_fix.ps1 -Path "06_DC_M12_KPI_Evidence\SomeFile.docx"
#
# Requires Microsoft Word installed and automatable on this machine.

param([Parameter(Mandatory = $true)][string]$Path)

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $resolvedPath = (Resolve-Path $Path).Path
    $doc = $word.Documents.Open($resolvedPath, $false, $false)  # ConfirmConversions=$false, ReadOnly=$false

    foreach ($sec in $doc.Sections) {
        # wdHeaderFooterPrimary=1, wdHeaderFooterFirstPage=2, wdHeaderFooterEvenPages=3
        foreach ($hfIndex in 1..3) {
            try {
                $hdr = $sec.Headers.Item($hfIndex)
                if ($hdr.Exists) {
                    foreach ($p in $hdr.Range.Paragraphs) {
                        $p.Range.ParagraphFormat.ReadingOrder = 1
                    }
                }
            } catch {}
            try {
                $ftr = $sec.Footers.Item($hfIndex)
                if ($ftr.Exists) {
                    foreach ($p in $ftr.Range.Paragraphs) {
                        $p.Range.ParagraphFormat.ReadingOrder = 1
                    }
                }
            } catch {}
        }
    }

    # Every paragraph in the main body, including every table-cell paragraph.
    foreach ($p in $doc.Paragraphs) {
        $p.Range.ParagraphFormat.ReadingOrder = 1
    }

    $doc.Save()
    Write-Output ("FIXED_AND_SAVED: " + $resolvedPath)
    $doc.Close($false)
} catch {
    Write-Output ("ERROR: " + $_.Exception.Message)
    exit 1
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
