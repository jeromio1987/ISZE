$src = 'C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920\08_Draft_to_MH_2026-10-11\ISZE_Parts_Price_Revision_Workbook_Oct2026.xlsx'
$dst = 'C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\ISZE_Parts_Price_Revision_Workbook_Oct2026_clearer_labels_2026-10-15.xlsx'
Copy-Item $src $dst -Force
$dq = [char]34
$A6 = "Hold at today's price where a distributor buys under 45% of what its trucks need in that parts category (1 = on, 0 = off). See the note on the yellow cell."
$A7 = "Small extra where the UK online shop KS International sells the same Isuzu part number more than 5% above our reference dealer price (1 = on, 0 = off). See the note on the yellow cell."
$A8 = "Hold at today's price where our reference dealer price is more than 60% above KS International for the same part number (1 = on, 0 = off). Off by default. See the note on the yellow cell."
$A9 = "Keep brake pad kits at today's price (1 = on, 0 = off). Decided 30 September 2026."
$B6 = "What this does: for each distributor and parts category we measure what share of its trucks' expected need the distributor buys from us (capture rate, calendar 2025). Under 45% means it mostly buys elsewhere already, so a higher list price there mostly costs us volume. With the switch on, those lines pay today's price. The rest of the book carries the difference, so the total stays on the target. 1 = on (default), 0 = off."
$B7 = "Reference dealer price = our list price plus the projected average distributor margin of 37% and dealer margin of 27,5% (policy paper of 2 October 2026, provisional). KS International is a UK online shop. We use it because it can be searched with our own Isuzu part number, it shows the public end customer price, and it was checked in September 2026. Eucon does not say whether its prices are trade or retail, and the other sites only give category averages." + "`n`n" + "What this switch does: where KS sells the same part number more than 5% above our reference dealer price, the part gets a small extra on top of its normal increase. The extra is the increase that would bring our reference dealer price up to 15% above the shop, capped at 10 points where we saw the shop price for that part and 6 points where it is derived. It applies to 5 part numbers (EUR 245,000 billed, about EUR 21,000 extra before rescaling). The total stays on the target, so the other parts carry slightly less. 1 = on (default), 0 = off."
$B8 = "Same comparison as the switch above, the other way round. Where our reference dealer price is more than 60% above the KS International price for the same part number, the part is held at today's price. Off by default, because those parts did not react more in the dealer data. With the switch on it would hold 20 part numbers (EUR 1.84 million billed), for example the front brake rotor (EUR 703,000 billed), where we sit far above the shop. The rest of the book carries the difference. 1 = on, 0 = off (default)."
$B9 = "Decided 30 September 2026: the 29 brake pad kits keep today's price in every market. The other parts carry the difference so the book still lands on the target. 1 = on (default), 0 = off."
$R10 = "3. A small extra for 5 part numbers where the UK online shop KS International sells the same part number more than 5% above our reference dealer price (our list price plus a projected average distributor margin of 37% and dealer margin of 27,5%). The extra is capped at the evidence limits already in the pricing configuration: 10 points where we saw the shop price for that part, 6 points where it is derived."
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false; $xl.DisplayAlerts = $false
try {
  $wb = $xl.Workbooks.Open($dst, 0, $false)
  $xl.Calculation = -4135
  $s = $wb.Worksheets.Item('Summary')
  "before: A7 = " + $s.Range('A7').Value2.Substring(0, 60) + " | comments on B6:B9: " + $s.Comments.Count
  $s.Range('A6').Value2 = $A6; $s.Range('A7').Value2 = $A7; $s.Range('A8').Value2 = $A8; $s.Range('A9').Value2 = $A9
  $s.Range('A6:A9').WrapText = $true
  [void]$s.Rows('6:9').AutoFit()
  foreach ($p in @(@('B6', $B6), @('B7', $B7), @('B8', $B8), @('B9', $B9))) {
    $c = $s.Range($p[0]).AddComment($p[1])
    $c.Shape.Width = 380
    $c.Shape.Height = [math]::Min(330, 24 + 15 * [math]::Ceiling($p[1].Length / 62))
  }
  $wb.Worksheets.Item('Read me').Range('A10').Value2 = $R10
  $wb.Save()
  "saved; Summary rows 6-9 heights: " + (($s.Range('A6:A9').Rows | ForEach-Object { $_.RowHeight }) -join ', ')
  $wb.Close($true)
} finally { $xl.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($xl) }
(Get-Item $dst).Length
