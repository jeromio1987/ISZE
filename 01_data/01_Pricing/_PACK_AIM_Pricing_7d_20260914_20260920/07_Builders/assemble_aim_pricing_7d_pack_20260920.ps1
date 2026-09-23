# Assemble last-7-days AIM + pricing pack.
# Writes BOTH Windows shortcuts (.lnk) AND full file copies (duplicates) into each subfolder.
# Run: powershell -NoProfile -File 01_data/91_build/assemble_aim_pricing_7d_pack_20260920.ps1
$ErrorActionPreference = "Stop"
$ISZE = "C:\Users\jerom\Desktop\claude\ISZE"
$PACK = Join-Path $ISZE "01_data\01_Pricing\_PACK_AIM_Pricing_7d_20260914_20260920"
$CopyDuplicates = $true

function New-Shortcut {
    param([string]$Target, [string]$LinkPath)
    if (-not (Test-Path -LiteralPath $Target)) {
        Write-Warning "MISSING target: $Target"
        return $false
    }
    $dir = Split-Path -Parent $LinkPath
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    if (Test-Path -LiteralPath $LinkPath) { Remove-Item -LiteralPath $LinkPath -Force }
    $w = New-Object -ComObject WScript.Shell
    $s = $w.CreateShortcut($LinkPath)
    $s.TargetPath = $Target
    $s.WorkingDirectory = Split-Path -Parent $Target
    $s.Save()
    return $true
}

# role, subfolder, relative path from ISZE, display name in pack
$items = @(
    @{ Role = "start"; Sub = "00_START_HERE"; Rel = "01_data\01_Pricing\BP_missing_for_price_simulation_20260920.xlsx"; Name = "BP_missing_for_price_simulation_20260920.xlsx" }
    @{ Role = "start"; Sub = "00_START_HERE"; Rel = "01_data\01_Pricing\OPEN_BP_missing_for_price_simulation_20260920.cmd"; Name = "OPEN_BP_missing.cmd" }
    @{ Role = "start"; Sub = "00_START_HERE"; Rel = "01_data\01_Pricing\AIM_class_status_overview_20260919.xlsx"; Name = "AIM_class_status_overview_20260919.xlsx" }
    @{ Role = "start"; Sub = "00_START_HERE"; Rel = "01_data\01_Pricing\OPEN_AIM_class_status_overview_20260919.cmd"; Name = "OPEN_AIM_class_status.cmd" }
    @{ Role = "start"; Sub = "00_START_HERE"; Rel = "01_data\90_INBOX\_EQ_HIT_SESSION_20260919_BRIEF.md"; Name = "EQ_HIT_SESSION_BRIEF.md" }
    @{ Role = "start"; Sub = "00_START_HERE"; Rel = "01_data\90_INBOX\OPEN_EQ_HIT_SESSION_20260919.cmd"; Name = "OPEN_EQ_HIT_SESSION.cmd" }
    @{ Role = "start"; Sub = "00_START_HERE"; Rel = "01_data\90_INBOX\AIM_EQ_DONE_BRIEF_20260920.md"; Name = "AIM_EQ_DONE_BRIEF_20260920.md" }

    @{ Role = "bp_impact"; Sub = "01_BP_impact"; Rel = "02_dashboards\pricing\ISZE_Price_BP_Weighted_Compare.html"; Name = "ISZE_Price_BP_Weighted_Compare.html" }
    @{ Role = "bp_impact"; Sub = "01_BP_impact"; Rel = "02_dashboards\pricing\OPEN_ISZE_Price_BP_Weighted_Compare.cmd"; Name = "OPEN_ISZE_Price_BP_Weighted_Compare.cmd" }
    @{ Role = "bp_impact"; Sub = "01_BP_impact"; Rel = "01_data\00_derived\price_bp_weighted_compare_pn.csv"; Name = "price_bp_weighted_compare_pn.csv" }
    @{ Role = "bp_impact"; Sub = "01_BP_impact"; Rel = "01_data\00_derived\price_bp_weighted_compare_meta.json"; Name = "price_bp_weighted_compare_meta.json" }
    @{ Role = "bp_impact"; Sub = "01_BP_impact"; Rel = "01_data\01_Pricing\Unpriced_lines_no_matching_price.xlsx"; Name = "Unpriced_lines_no_matching_price.xlsx" }
    @{ Role = "bp_impact"; Sub = "01_BP_impact"; Rel = "01_data\01_Pricing\BP_missing_for_price_simulation_20260920.xlsx"; Name = "BP_missing_for_price_simulation_20260920.xlsx" }
    @{ Role = "bp_impact"; Sub = "01_BP_impact"; Rel = "01_data\01_Pricing\Parts_needing_source_or_origin.xlsx"; Name = "Parts_needing_source_or_origin.xlsx" }
    @{ Role = "bp_impact"; Sub = "01_BP_impact"; Rel = "01_data\00_derived\bp_missing_complete_for_simulation_20260920.csv"; Name = "bp_missing_complete_for_simulation_20260920.csv" }
    @{ Role = "bp_impact"; Sub = "01_BP_impact"; Rel = "01_data\00_derived\bp_missing_old_for_simulation_20260920.csv"; Name = "bp_missing_old_for_simulation_20260920.csv" }
    @{ Role = "bp_impact"; Sub = "01_BP_impact"; Rel = "01_data\00_derived\bp_missing_new_for_simulation_20260920.csv"; Name = "bp_missing_new_for_simulation_20260920.csv" }

    @{ Role = "fob_fx"; Sub = "02_FOB_FX"; Rel = "01_data\01_Pricing\Pricing_Revision_AIM_FX_20261001.xlsx"; Name = "Pricing_Revision_AIM_FX_20261001.xlsx" }
    @{ Role = "fob_fx"; Sub = "02_FOB_FX"; Rel = "01_data\01_Pricing\OPEN_Pricing_Revision_AIM_FX_20261001.cmd"; Name = "OPEN_Pricing_Revision_AIM_FX_20261001.cmd" }
    @{ Role = "fob_fx"; Sub = "02_FOB_FX"; Rel = "02_dashboards\pricing\ISZE_Pricing_Revision_AIM_FX_20261001.html"; Name = "ISZE_Pricing_Revision_AIM_FX_20261001.html" }
    @{ Role = "fob_fx"; Sub = "02_FOB_FX"; Rel = "02_dashboards\pricing\OPEN_Pricing_Revision_AIM_FX_20261001.cmd"; Name = "OPEN_HTML_Pricing_Revision_AIM_FX.cmd" }

    @{ Role = "simulation"; Sub = "03_Simulation_stack"; Rel = "01_data\01_Pricing\ISZE_Pricing_Stack_Simulation_2026-09-19.xlsx"; Name = "ISZE_Pricing_Stack_Simulation_2026-09-19.xlsx" }
    @{ Role = "simulation"; Sub = "03_Simulation_stack"; Rel = "01_data\01_Pricing\OPEN_Pricing_Stack_Simulation.cmd"; Name = "OPEN_Pricing_Stack_Simulation.cmd" }
    @{ Role = "simulation"; Sub = "03_Simulation_stack"; Rel = "01_data\00_derived\pricing_stack_simulation_2026-09-19.json"; Name = "pricing_stack_simulation_2026-09-19.json" }
    @{ Role = "simulation"; Sub = "03_Simulation_stack"; Rel = "02_dashboards\pricing\PRICING_STACK_APPLIED_2026-09-19.html"; Name = "PRICING_STACK_APPLIED_2026-09-19.html" }
    @{ Role = "simulation"; Sub = "03_Simulation_stack"; Rel = "02_dashboards\pricing\OPEN_PRICING_STACK_APPLIED.cmd"; Name = "OPEN_PRICING_STACK_APPLIED.cmd" }
    @{ Role = "simulation"; Sub = "03_Simulation_stack"; Rel = "01_data\90_INBOX\PRICING_STACK_APPLIED_2026-09-19.md"; Name = "PRICING_STACK_APPLIED_2026-09-19.md" }
    @{ Role = "simulation"; Sub = "03_Simulation_stack"; Rel = "01_data\00_derived\pricing_stack_applied_2026-09-19.json"; Name = "pricing_stack_applied_2026-09-19.json" }
    @{ Role = "simulation"; Sub = "03_Simulation_stack"; Rel = "02_dashboards\pricing\ISZE_Pricing_Simulation_Spec_Basis.xlsx"; Name = "ISZE_Pricing_Simulation_Spec_Basis.xlsx" }
    @{ Role = "simulation"; Sub = "03_Simulation_stack"; Rel = "02_dashboards\pricing\OPEN_ISZE_Pricing_Simulation_Spec_Basis.cmd"; Name = "OPEN_ISZE_Pricing_Simulation_Spec_Basis.cmd" }

    @{ Role = "aim_revision"; Sub = "04_AIM_x_revision"; Rel = "01_data\01_Pricing\Pricing_Revision_AIM_Source_Analysis.xlsx"; Name = "Pricing_Revision_AIM_Source_Analysis.xlsx" }
    @{ Role = "aim_revision"; Sub = "04_AIM_x_revision"; Rel = "01_data\01_Pricing\OPEN_Pricing_Revision_AIM_Source_Analysis.cmd"; Name = "OPEN_Pricing_Revision_AIM_Source_Analysis.cmd" }
    @{ Role = "aim_revision"; Sub = "04_AIM_x_revision"; Rel = "02_dashboards\pricing\ISZE_Pricing_Revision_AIM_Source.html"; Name = "ISZE_Pricing_Revision_AIM_Source.html" }
    @{ Role = "aim_revision"; Sub = "04_AIM_x_revision"; Rel = "02_dashboards\pricing\OPEN_Pricing_Revision_AIM_Source.cmd"; Name = "OPEN_Pricing_Revision_AIM_Source.cmd" }
    @{ Role = "aim_revision"; Sub = "04_AIM_x_revision"; Rel = "01_data\00_derived\pricing_aim_source_cube.csv"; Name = "pricing_aim_source_cube.csv" }
    @{ Role = "aim_revision"; Sub = "04_AIM_x_revision"; Rel = "01_data\00_derived\pricing_aim_source_lines.parquet"; Name = "pricing_aim_source_lines.parquet" }
    @{ Role = "aim_revision"; Sub = "04_AIM_x_revision"; Rel = "01_data\00_derived\pricing_aim_source_meta.json"; Name = "pricing_aim_source_meta.json" }
    @{ Role = "aim_revision"; Sub = "04_AIM_x_revision"; Rel = "02_dashboards\pricing\ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.html"; Name = "ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.html" }
    @{ Role = "aim_revision"; Sub = "04_AIM_x_revision"; Rel = "02_dashboards\pricing\OPEN_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.cmd"; Name = "OPEN_Pricing_Revision_AIM_Source_PROTOTYPE_AllDB.cmd" }
    @{ Role = "aim_revision"; Sub = "04_AIM_x_revision"; Rel = "02_dashboards\pricing\ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.html"; Name = "ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.html" }
    @{ Role = "aim_revision"; Sub = "04_AIM_x_revision"; Rel = "02_dashboards\pricing\OPEN_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.cmd"; Name = "OPEN_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.cmd" }

    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "01_data\01_Pricing\Not_on_AIM_spine_4SIGNAL_APPLIED_agree2_3_20260919.xlsx"; Name = "Not_on_AIM_4SIGNAL_APPLIED.xlsx" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "01_data\01_Pricing\OPEN_Not_on_AIM_spine_4SIGNAL_APPLIED_20260919.cmd"; Name = "OPEN_4SIGNAL_APPLIED.cmd" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "01_data\01_Pricing\Not_on_AIM_spine_4SIGNAL_classify_20260919.xlsx"; Name = "Not_on_AIM_4SIGNAL_classify.xlsx" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "01_data\01_Pricing\OPEN_Not_on_AIM_spine_4SIGNAL_20260919.cmd"; Name = "OPEN_4SIGNAL_classify.cmd" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "01_data\01_Pricing\Not_on_AIM_spine_WORKLIST_classify_20260919.xlsx"; Name = "Not_on_AIM_WORKLIST.xlsx" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "01_data\01_Pricing\Not_on_AIM_spine_residual_after_tools_20260919.xlsx"; Name = "Not_on_AIM_residual_after_tools.xlsx" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "01_data\01_Pricing\EQ_HIT_SESSION_20260919.xlsx"; Name = "EQ_HIT_SESSION_20260919.xlsx" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "01_data\01_Pricing\AIM_class_status_overview_20260919.xlsx"; Name = "AIM_class_status_overview.xlsx" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "01_data\00_derived\aim_gap_4signal_agree2_3_patch_20260919.csv"; Name = "aim_gap_4signal_agree2_3_patch.csv" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "01_data\00_derived\aim_gap_high_conf_patch_residual_20260919.csv"; Name = "aim_gap_high_conf_patch.csv" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "01_data\00_derived\pricing_not_on_aim_4signal_20260919.csv"; Name = "pricing_not_on_aim_4signal.csv" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "01_data\00_derived\pricing_not_on_aim_spine_residual_AFTER_4signal_agree2_3_20260919.csv"; Name = "residual_AFTER_4signal_agree2_3.csv" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "01_data\00_derived\aim_pn_classification_20260920.csv"; Name = "aim_pn_classification_20260920.csv" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "01_data\00_derived\aim_master_v2.csv"; Name = "aim_master_v2.csv" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "01_data\90_INBOX\AIM_residual_Other_review_TRUE_OPEN_by_L12M_20260920.xlsx"; Name = "AIM_residual_TRUE_OPEN.xlsx" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "01_data\90_INBOX\OPEN_AIM_residual_Other_review_TRUE_OPEN_20260920.cmd"; Name = "OPEN_AIM_residual_TRUE_OPEN.cmd" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "01_data\90_INBOX\_EQ_HIT_SESSION_20260919_RESULTS.csv"; Name = "EQ_HIT_SESSION_RESULTS.csv" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "01_data\00_derived\AIM_Master_PN_Categories_Figkey_20260920.xlsx"; Name = "AIM_Master_PN_Categories_Figkey.xlsx" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "02_dashboards\sales\ISZE_AIM_Classification_Paper.html"; Name = "ISZE_AIM_Classification_Paper.html" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "02_dashboards\sales\OPEN_ISZE_AIM_Classification_Paper.cmd"; Name = "OPEN_ISZE_AIM_Classification_Paper.cmd" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "02_dashboards\pricing\ISZE_AIM_Repertoire_Map_2026-09-17.html"; Name = "ISZE_AIM_Repertoire_Map_2026-09-17.html" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "02_dashboards\pricing\OPEN_ISZE_AIM_Repertoire_Map.cmd"; Name = "OPEN_ISZE_AIM_Repertoire_Map.cmd" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "02_dashboards\pricing\ISZE_AIM_Repertoire_Spider_2026-09-17.html"; Name = "ISZE_AIM_Repertoire_Spider_2026-09-17.html" }
    @{ Role = "aim_class"; Sub = "05_AIM_classification"; Rel = "02_dashboards\pricing\OPEN_ISZE_AIM_Repertoire_Spider.cmd"; Name = "OPEN_ISZE_AIM_Repertoire_Spider.cmd" }

    @{ Role = "policy"; Sub = "06_Policy_decks"; Rel = "02_dashboards\pricing\ISZE_Pricing_Policy_Paper_REV3.html"; Name = "ISZE_Pricing_Policy_Paper_REV3.html" }
    @{ Role = "policy"; Sub = "06_Policy_decks"; Rel = "02_dashboards\pricing\OPEN_ISZE_Pricing_Policy_Paper_REV3.cmd"; Name = "OPEN_Policy_Paper_REV3.cmd" }
    @{ Role = "policy"; Sub = "06_Policy_decks"; Rel = "02_dashboards\pricing\ISZE_Pricing_Policy_Paper.html"; Name = "ISZE_Pricing_Policy_Paper.html" }
    @{ Role = "policy"; Sub = "06_Policy_decks"; Rel = "02_dashboards\pricing\OPEN_ISZE_Pricing_Policy_Paper.cmd"; Name = "OPEN_ISZE_Pricing_Policy_Paper.cmd" }
    @{ Role = "policy"; Sub = "06_Policy_decks"; Rel = "01_data\01_Pricing\ISZE_Pricing_Framework.xlsx"; Name = "ISZE_Pricing_Framework.xlsx" }
    @{ Role = "policy"; Sub = "06_Policy_decks"; Rel = "01_data\01_Pricing\OPEN_ISZE_Pricing_Framework.cmd"; Name = "OPEN_ISZE_Pricing_Framework.cmd" }
    @{ Role = "policy"; Sub = "06_Policy_decks"; Rel = "01_data\90_INBOX\pricing_system_by_family_2026-09-19.xlsx"; Name = "pricing_system_by_family.xlsx" }
    @{ Role = "policy"; Sub = "06_Policy_decks"; Rel = "01_data\90_INBOX\pricing_system_by_market_2026-09-19.xlsx"; Name = "pricing_system_by_market.xlsx" }
    @{ Role = "policy"; Sub = "06_Policy_decks"; Rel = "01_data\90_INBOX\pricing_system_formulas_margin_sort_2026-09-19.xlsx"; Name = "pricing_system_formulas_margin_sort.xlsx" }
    @{ Role = "policy"; Sub = "06_Policy_decks"; Rel = "01_data\90_INBOX\ISZE_Pricing_Policy_Management_v1.4.pptx"; Name = "ISZE_Pricing_Policy_Management_v1.4.pptx" }
    @{ Role = "policy"; Sub = "06_Policy_decks"; Rel = "01_data\90_INBOX\OPEN_Pricing_System.cmd"; Name = "OPEN_Pricing_System.cmd" }
    @{ Role = "policy"; Sub = "06_Policy_decks"; Rel = "01_data\01_Pricing\Price_Increase_5pct_Flat_REVIEW_2026-09-17.xlsx"; Name = "Price_Increase_5pct_Flat_REVIEW.xlsx" }
    @{ Role = "policy"; Sub = "06_Policy_decks"; Rel = "02_dashboards\pricing\ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html"; Name = "ISZE_Price_Increase_5pct_Flat_REVIEW.html" }

    @{ Role = "builder"; Sub = "07_Builders"; Rel = "01_data\91_build\build_price_bp_weighted_compare.py"; Name = "build_price_bp_weighted_compare.py" }
    @{ Role = "builder"; Sub = "07_Builders"; Rel = "01_data\91_build\build_pricing_stack_simulation_20260919.py"; Name = "build_pricing_stack_simulation_20260919.py" }
    @{ Role = "builder"; Sub = "07_Builders"; Rel = "01_data\91_build\score_not_on_aim_4signal_20260919.py"; Name = "score_not_on_aim_4signal_20260919.py" }
    @{ Role = "builder"; Sub = "07_Builders"; Rel = "01_data\91_build\build_bp_missing_for_simulation_20260920.py"; Name = "build_bp_missing_for_simulation_20260920.py" }
    @{ Role = "builder"; Sub = "07_Builders"; Rel = "01_data\91_build\build_pricing_aim_source_cube.py"; Name = "build_pricing_aim_source_cube.py" }
    @{ Role = "builder"; Sub = "07_Builders"; Rel = "02_dashboards\pricing\_build\build_pricing_fx_overlay_20261001.py"; Name = "build_pricing_fx_overlay_20261001.py" }
    @{ Role = "builder"; Sub = "07_Builders"; Rel = "02_dashboards\pricing\_build\build_pricing_revision_analysis_xlsx.py"; Name = "build_pricing_revision_analysis_xlsx.py" }
    @{ Role = "builder"; Sub = "07_Builders"; Rel = "01_data\91_build\assemble_aim_pricing_7d_pack_20260920.ps1"; Name = "assemble_aim_pricing_7d_pack_20260920.ps1" }
)

# Preserve INDEX.md text across wipe
$indexKeep = $null
$indexPath = Join-Path $PACK "INDEX.md"
if (Test-Path $indexPath) { $indexKeep = Get-Content -LiteralPath $indexPath -Raw }

if (Test-Path $PACK) {
    Get-ChildItem $PACK -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
}

$subs = @(
    "00_START_HERE", "01_BP_impact", "02_FOB_FX", "03_Simulation_stack",
    "04_AIM_x_revision", "05_AIM_classification", "06_Policy_decks", "07_Builders"
)
foreach ($s in $subs) {
    New-Item -ItemType Directory -Path (Join-Path $PACK $s) -Force | Out-Null
}

$manifest = New-Object System.Collections.Generic.List[object]
$ok = 0
$miss = 0
$copied = 0
$copyBytes = [int64]0
foreach ($it in $items) {
    $target = Join-Path $ISZE $it.Rel
    $subDir = Join-Path $PACK $it.Sub
    $link = Join-Path $subDir ($it.Name + ".lnk")
    $copyPath = Join-Path $subDir $it.Name
    $exists = Test-Path -LiteralPath $target
    $mtime = ""
    $bytes = [int64]0
    $copiedOk = $false
    if ($exists) {
        $fi = Get-Item -LiteralPath $target
        $mtime = $fi.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
        $bytes = [int64]$fi.Length
        if (New-Shortcut -Target $target -LinkPath $link) { $ok++ } else { $miss++ }
        if ($CopyDuplicates) {
            Copy-Item -LiteralPath $target -Destination $copyPath -Force
            if (Test-Path -LiteralPath $copyPath) {
                $copied++
                $copyBytes += [int64](Get-Item -LiteralPath $copyPath).Length
                $copiedOk = $true
            }
        }
    } else {
        $miss++
        Write-Warning "Skip missing: $($it.Rel)"
    }
    $manifest.Add([pscustomobject]@{
        role       = $it.Role
        subfolder  = $it.Sub
        link_name  = $it.Name + ".lnk"
        copy_name  = $it.Name
        copied     = $copiedOk
        source_rel = $it.Rel
        source_abs = $target
        exists     = $exists
        mtime      = $mtime
        bytes      = $bytes
    }) | Out-Null
}

$manifestPath = Join-Path $PACK "MANIFEST.csv"
$manifest | Export-Csv -Path $manifestPath -NoTypeInformation -Encoding UTF8

# INDEX
$note = @"

---

**Duplicates (2026-09-20):** each numbered folder now holds a **full copy** of every listed file **and** a ``.lnk`` shortcut to the live original. Open the copy in-folder, or the shortcut to jump to the source path.

"@
if ($indexKeep) {
    if ($indexKeep -notmatch 'full copy') {
        Set-Content -LiteralPath $indexPath -Value ($indexKeep.TrimEnd() + $note) -Encoding UTF8
    } else {
        Set-Content -LiteralPath $indexPath -Value $indexKeep -Encoding UTF8
    }
} else {
    @"
# AIM + pricing pack (14–20 Sep 2026)

Shortcuts **and full file copies** sit in each numbered folder.
See ``00_START_HERE`` and ``MANIFEST.csv``.
"@ | Set-Content -LiteralPath $indexPath -Encoding UTF8
}
Copy-Item -LiteralPath $indexPath -Destination (Join-Path $PACK "00_START_HERE\INDEX.md") -Force

@"
# START HERE

Read **INDEX.md** (way forward + map).

Each folder has **both** a ``.lnk`` shortcut to the live file **and a full duplicate** of that file.

Open the pack root: ``..\OPEN_PACK.cmd``
"@ | Set-Content -LiteralPath (Join-Path $PACK "00_START_HERE\README.md") -Encoding UTF8

$openPack = Join-Path $PACK "OPEN_PACK.cmd"
[IO.File]::WriteAllText($openPack, "@echo off`r`nexplorer `"%~dp0`"`r`n")

$parentOpen = Join-Path $ISZE "01_data\01_Pricing\OPEN_PACK_AIM_Pricing_7d.cmd"
[IO.File]::WriteAllText($parentOpen, "@echo off`r`nstart `"`" `"%~dp0_PACK_AIM_Pricing_7d_20260914_20260920\OPEN_PACK.cmd`"`r`n")

Write-Host "PACK=$PACK"
Write-Host "shortcuts_ok=$ok missing=$miss"
Write-Host "copies_ok=$copied copy_MB=$([math]::Round($copyBytes/1MB,1))"
Write-Host "manifest=$manifestPath"
