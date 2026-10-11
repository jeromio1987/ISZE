# Isuzu UK pickup file check, 11 October 2026

The file checked is the monthly demand workbook Isuzu UK pickup sent, named August 2026. It was not reshaped before the check. The checker reads the first sheet only. That sheet is calendar 2025, 4,248 part rows. The second sheet, 2026 through August, 3,641 part rows, was checked separately. Both were rejected.

What the file actually is: one row per part, with a column for each month (JAN, FEB, MAR, and so on), a description, an average and a total. No dealer, no single month, no euro amount, no coverage note.

What stopped the file, on both sheets:

- No reporting month in the form YYYY-MM.
- No coverage note (which sites are in, which are left out, the date range, and whether returns are included).
- No distributor id on the rows, so none of them match the drop.
- No quantity column. The month columns are numbers, and the checker does not treat those columns as the quantity.

A blank dealer name was recorded and did not stop the file. A catalogue match was not run. There is no previous accepted month to compare a jump against. Nine rules are still listed and do not run, because their wording was not in the film or the Plan B paper.

The workbook has no euros, so it cannot be set against what we billed line by line. The published FY2026 comparison for Isuzu UK pickup was passed through the same stock formula the checker uses: what we billed, minus warranty, minus sales to dealer.

- Billed €5,951,968
- Warranty €1,335,647
- Sales to dealer €5,983,188
- Stock on that formula: −€1,368,867

The published stock column on that same comparison is −€31,220. That figure is billed minus sales to dealer, with the warranty still inside the billed number. It is not the result of parking warranty first.
