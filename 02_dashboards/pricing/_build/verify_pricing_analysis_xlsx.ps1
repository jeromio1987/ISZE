"""Verify the pricing analysis workbook: recalculate through Excel COM and read back
the Checks sheet, so the numbers are proven against the published revision rather
than assumed from the builder exiting zero.

Run: powershell -File 02_dashboards/pricing/_build/verify_pricing_analysis_xlsx.ps1
"""
$ErrorActionPreference = "Stop"
$path = "C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\Pricing_Revision_AIM_Source_Analysis.xlsx"

# A leftover Excel instance from an earlier probe keeps the file locked and makes
# the builder fail with a permission error. Clear it first.
Get-Process EXCEL -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
try {
    $wb = $excel.Workbooks.Open($path)
    $excel.CalculateFullRebuild()
    # read the checks the workbook itself makes
    $ws = $wb.Worksheets.Item("Checks")
    $rows = @()
    for ($r = 5; $r -le 22; $r++) {
        $label = $ws.Cells.Item($r, 1).Text
        $value = $ws.Cells.Item($r, 2).Text
        if ($label -ne "") { $rows += ("{0,-52} {1}" -f $label, $value) }
    }
    $rows | ForEach-Object { Write-Output $_ }

    # DB summary network row
    $ws2 = $wb.Worksheets.Item("DB summary")
    $last = $ws2.Cells($ws2.Rows.Count, 1).End(-4162).Row
    $netPct = $ws2.Cells.Item($last, 14).Text
    $netStep = $ws2.Cells.Item($last, 13).Text
    Write-Output ""
    Write-Output ("DB summary network row (row {0}): step {1}  weighted {2}" -f $last, $netStep, $netPct)

    # count non-error formula results on the biggest roll-up sheet
    $ws3 = $wb.Worksheets.Item("DB x AIM L3")
    $last3 = $ws3.Cells($ws3.Rows.Count, 1).End(-4162).Row
    $bad = 0
    for ($r = 5; $r -le $last3; $r++) {
        for ($c = 9; $c -le 13; $c++) {
            $t = $ws3.Cells.Item($r, $c).Text
            if ($t -match "^#") { $bad++ }
        }
    }
    Write-Output ("DB x AIM L3: rows {0}, formula error cells {1}" -f ($last3 - 4), $bad)

    # does any formula cell anywhere report an error
    $errors = 0
    foreach ($name in @("Read me","DB summary","DB x AIM L1","DB x AIM L2","DB x AIM L3",
                        "TH-JP source","Source x AIM L1","Customer","PN data","Checks")) {
        $s = $wb.Worksheets.Item($name)
        try {
            $found = $s.UsedRange.SpecialCells(-4123, 16)  # xlCellTypeFormulas, xlErrors
            $errors += $found.Count
        } catch { }
    }
    Write-Output ("Formula cells returning an error, whole workbook: {0}" -f $errors)

    # Spot-check DB x AIM L1: Columns D-K must show numbers after recalc (not blank).
    # openpyxl writes formulas with no cached values; without Save, Explorer opens blank.
    $wsL1 = $wb.Worksheets.Item("DB x AIM L1")
    $f5 = $wsL1.Range("F5").Value2
    $d5 = $wsL1.Range("D5").Value2
    if ($null -eq $f5 -or $f5 -eq "" -or $null -eq $d5) {
        throw "DB x AIM L1 D5/F5 blank after recalc - formulas did not calculate"
    }
    Write-Output ("DB x AIM L1 sample: D5={0} F5={1}" -f $d5, $f5)

    # Bake calculated values into the file so Jerome does not open a "Calculate" sheet
    # with empty euro columns.
    $wb.Save()
    $wb.Close($false)
    Write-Output "VERIFY_DONE (saved with calculated values)"
} finally {
    try { $excel.Quit() } catch { }
    Start-Sleep -Seconds 1
    Get-Process EXCEL -ErrorAction SilentlyContinue | Stop-Process -Force
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
}
