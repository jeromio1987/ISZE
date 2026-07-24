# Build full ISZE derived pipeline (P0-P5) then run deterministic verification.
# Use after Cursor agent changes or monthly data refresh.
$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

Write-Host "=== ISZE pipeline: build + verify ===" -ForegroundColor Cyan

$scripts = @(
    'scripts/build_sales_fact_from_cy.py',
    'scripts/build_bvp_p0_p1.py',
    'scripts/build_pr00_classification.py',
    'scripts/build_aim_pn_classification.py',
    'scripts/build_fig_key_dimension.py',
    'scripts/build_sales_by_fig_key.py',
    'scripts/build_bvp_crossref_sales.py',
    'scripts/build_bvp_p2_mix.py',
    'scripts/build_bvp_p4_p5.py',
    'scripts/enrich_gps_spu_v9.py',
    'scripts/build_aim_gps_matrix.py',
    'scripts/audit_mislabelled_skus.py',
    'scripts/build_competitiveness_autodoc_risk.py',
    'scripts/build_bvp_addressable_basket.py',
    'scripts/build_pms_opportunity_matrix.py',
    'scripts/build_pms_db_summary.py',
    'scripts/build_network_percentile.py',
    'scripts/build_ituk_pms_pn_audit.py',
    'scripts/build_strategic_contracts.py'
)

$postVerify = @(
    'scripts/build_dealer_sellout_aim_gps.py',
    'scripts/build_isze_dashboard_json.py',
    'scripts/build_gps_integrity_audit.py',
    'scripts/patch_dashboard_integrity.py',
    'scripts/inject_dashboard_overlays.py',
    # decision-model layer (2026-06-10)
    'scripts/build_wallet_waterfall.py',
    'scripts/build_revenue_runway.py',
    'scripts/build_defection_alerts.py',
    'scripts/build_attach_rates.py',
    'scripts/build_dealer_leakage.py',
    'scripts/build_price_volume_elasticity.py',
    # ops early-warning list (2026-07-17) — consumes defection_alerts (above),
    # vor_seasonality (build_strategic_contracts) and pms_capture_by_db, so it
    # must run after them. db_aftersales_risk.csv is optional context here: the
    # builder degrades to a blank risk-score column if it was never built.
    'scripts/build_early_warning.py',
    # metrics-as-code: snapshot must run AFTER all builders
    'scripts/build_metrics_snapshot.py'
)

foreach ($s in $scripts) {
    Write-Host "`n>> python $s" -ForegroundColor Yellow
    python $s
    if ($LASTEXITCODE -ne 0) {
        Write-Host "BUILD FAILED: $s (exit $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

Write-Host "`n>> python scripts/verify_derived_pipeline.py" -ForegroundColor Yellow
python scripts/verify_derived_pipeline.py
$verifyExit = $LASTEXITCODE

if ($verifyExit -eq 0) {
    foreach ($s in $postVerify) {
        Write-Host "`n>> python $s" -ForegroundColor Yellow
        python $s
        if ($LASTEXITCODE -ne 0) {
            Write-Host "POST-VERIFY STEP FAILED: $s" -ForegroundColor Red
            exit $LASTEXITCODE
        }
    }
    Write-Host "`n>> python scripts/build_gpt_safe_export.py" -ForegroundColor Yellow
    python scripts/build_gpt_safe_export.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "`n>> python scripts/verify_facts_drift.py" -ForegroundColor Yellow
    python scripts/verify_facts_drift.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FACTS DRIFT DETECTED - see Data/derived/_facts_drift_report.md" -ForegroundColor Red
        Write-Host "Reconcile FACTS.md + prism/data/facts_anchor.yaml before quoting numbers." -ForegroundColor Red
        exit 1
    }
    Write-Host "`n=== VERIFICATION PASSED (incl. FACTS drift check) ===" -ForegroundColor Green
    Write-Host "Claude: read Data/derived/_verification_report.md before signing off."
} else {
    Write-Host "`n=== VERIFICATION FAILED ===" -ForegroundColor Red
    Write-Host "See Data/derived/_verification_report.md"
}

exit $verifyExit
