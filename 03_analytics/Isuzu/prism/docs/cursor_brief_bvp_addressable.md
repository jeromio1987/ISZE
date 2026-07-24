# Cursor brief — BVP Addressable Basket (sales-driven scope expansion)

**Goal:** Expand the BVP dashboard from PMS-narrow (7 subgroups, ~€5.4M Genuine lifetime €) to BVP-catalog-wide (27 subgroups, ~€8.4M Genuine lifetime €) — but **scoped per distributor by their own lifetime Genuine sales** instead of a universal market-eligibility matrix.

**Why sales-driven, not regulatory-driven:**
- If a distributor has Genuine sales for a Genuine PN, that PN's BVP partner is automatically commercially viable for them (same fleet, same regulations).
- Zero Genuine sales of a PN by ALL distributors → not for our markets → exclude.
- Zero Genuine sales of a PN by ONE distributor while others sell → either out-of-market for that distributor OR Genuine is priced out (the latter is exactly when BVP is the answer — captured naturally because the addressable basket is per distributor).
- This auto-handles R90 / emission-spec / region without any explicit rule.

---

## Task 1 — `scripts/build_bvp_addressable_basket.py`

**Output:** `01_data/derived/bvp_addressable_basket.csv`

**Logic:**

```python
# Inputs
swx = pd.read_parquet('01_data/derived/sales_with_crossref.parquet')   # 34,972 rows
xref = pd.read_csv('01_data/derived/genuine_bvp_crossref.csv')          # 544 pairs

# Step 1: per distributor, distinct Genuine PNs they've sold (LIFETIME, all years)
gen_sold = (
    swx[swx['crossref_role'] == 'genuine']
    .groupby('distributor_code')['xref_genuine_pn']
    .apply(set).to_dict()
)

# Step 2: per distributor, distinct BVP PNs they've sold (lifetime)
bvp_sold = (
    swx[swx['crossref_role'] == 'bvp']
    .groupby('distributor_code')['xref_bvp_pn']
    .apply(set).to_dict()
)

# Step 3: for each distributor, build addressable BVP basket
rows = []
for dist, gen_set in gen_sold.items():
    addressable_bvp = xref[xref['genuine_pn'].isin(gen_set)]
    sold_bvp = bvp_sold.get(dist, set())
    for _, p in addressable_bvp.iterrows():
        rows.append({
            'distributor_code': dist,
            'genuine_pn': p['genuine_pn'],
            'bvp_pn': p['bvp_pn'],
            'product_subgroup': p['product_subgroup'],
            'product_family': p['product_family'],
            'vehicle_model': p['vehicle_model'],
            'engine_type': p['engine_type'],
            'origin': p['origin'],
            'pms_flag': p['pms_flag'],
            'currently_selling_bvp': p['bvp_pn'] in sold_bvp,
        })

out = pd.DataFrame(rows)
out.to_csv('01_data/derived/bvp_addressable_basket.csv', index=False)
```

**Output schema:**

| column | type | meaning |
|---|---|---|
| distributor_code | str | ARMENIA / ITUK / BELGIUM / … |
| genuine_pn | str | the Genuine PN this distributor has lifetime sales for |
| bvp_pn | str | paired BVP equivalent |
| product_subgroup | str | oil_filter / brake_pad / clutch_kit / urea_filter / … |
| product_family | str | PMS_Filters / Brakes / Clutch_Driveline / Suspension_Chassis / Belts_Cooling / Electrical / Cab_Misc |
| vehicle_model | str | comma-joined from catalog (N*R, F*S, TF*, …) |
| engine_type | str | comma-joined (4HK1, 6HK1, …) |
| origin | str | JAPAN / THAILAND / INDONESIA / … |
| pms_flag | bool | T = strict-PMS subgroup, F = wider wear/competitive |
| currently_selling_bvp | bool | T = this distributor has ANY lifetime BVP sales for this BVP PN, F = white-space opportunity |

**Verify fixture (`scripts/verify_derived_pipeline.py`):**

```yaml
bvp_addressable_basket:
  min_rows: 1500
  required_columns: [distributor_code, genuine_pn, bvp_pn, product_subgroup, currently_selling_bvp]
  distinct_distributors: ">= 25"
  distinct_subgroups: ">= 22"   # ~all 27 minus a few with zero sales
```

**Spot checks expected:**
- ITUK: ~85 of ~132 addressable BVP PNs `currently_selling_bvp=True` (64% lifetime penetration)
- ICELAND: 0 BVP currently sold → red-flag row
- PORTUGAL: should show >100% ratio anomaly preserved (more distinct BVP than addressable Genuine — investigate via the data, may indicate distributor sells BVP for vehicles serviced indirectly)

---

## Task 2 — Expand `modules/bvp_product_nav.py` taxonomy

**Current state:** `IN_SCOPE_SUBCATEGORIES` lists 7 (oil_filter / fuel_filter / air_filter / brake_pad / brake_shoe / clutch_disc / clutch_pressure_plate). Used as a hard filter throughout the dashboard.

**Change:**

1. **Drop `IN_SCOPE_SUBCATEGORIES` as a filter.** Replace with `is_addressable_for(distributor_code, subgroup)` which queries `bvp_addressable_basket.csv`.
2. **Expand `PRODUCT_GROUPS` from 3 to 8** product groups, covering all 27 BVP subgroups:

```python
PRODUCT_GROUPS = {
    "filters": {
        "label": "Filters",
        "product_family": "PMS_Filters",
        "subcategories": ["oil_filter", "fuel_filter", "air_filter", "blower_filter", "urea_filter"],
        "default_subgroup": "oil_filter",
        "sort": 1,
    },
    "brakes": {
        "label": "Brakes",
        "product_family": "Brakes",
        "subcategories": ["brake_pad", "brake_shoe", "brake_lining", "brake_rotor"],
        "default_subgroup": "brake_pad",
        "sort": 2,
    },
    "clutch": {
        "label": "Clutch & driveline",
        "product_family": "Clutch_Driveline",
        "subcategories": ["clutch_kit", "clutch_disc", "clutch_pressure_plate",
                          "clutch_booster", "release_bearing", "pilot_bearing", "center_bearing"],
        "default_subgroup": "clutch_kit",
        "sort": 3,
    },
    "suspension": {
        "label": "Suspension & chassis",
        "product_family": "Suspension_Chassis",
        "subcategories": ["shock_absorber", "leaf_spring", "bushing", "king_pin", "wheel_pin",
                          "hub_bearing", "hub_oil_seal"],
        "default_subgroup": "shock_absorber",
        "sort": 4,
    },
    "engine_cooling": {
        "label": "Engine & cooling",
        "product_family": "Belts_Cooling",
        "subcategories": ["fan_belt", "water_pump", "engine_mount"],
        "default_subgroup": "fan_belt",
        "sort": 5,
    },
    "electrical": {
        "label": "Electrical",
        "product_family": "Electrical",
        "subcategories": ["generator", "starter"],
        "default_subgroup": "generator",
        "sort": 6,
    },
    "cab": {
        "label": "Cab",
        "product_family": "Cab_Misc",
        "subcategories": ["wiper_blade"],
        "default_subgroup": "wiper_blade",
        "sort": 7,
    },
}
```

3. **Add subgroup labels** for the new entries — at minimum:
```python
SUBGROUP_LABELS.update({
    "blower_filter": "Cabin / blower filter",
    "urea_filter": "Urea (AdBlue) filter",
    "brake_lining": "Brake lining",
    "brake_rotor": "Brake rotor",
    "clutch_kit": "Clutch kit",
    "clutch_booster": "Clutch booster",
    "release_bearing": "Release bearing",
    "pilot_bearing": "Pilot bearing",
    "center_bearing": "Center bearing",
    "shock_absorber": "Shock absorber",
    "leaf_spring": "Leaf spring",
    "bushing": "Bushing",
    "king_pin": "King pin kit",
    "wheel_pin": "Wheel pin",
    "hub_bearing": "Hub bearing",
    "hub_oil_seal": "Hub oil seal",
    "fan_belt": "Fan belt",
    "water_pump": "Water pump",
    "engine_mount": "Engine foot rubber",
    "generator": "Generator",
    "starter": "Starter",
    "wiper_blade": "Wiper blade",
})
```

4. **New helper function:**
```python
@lru_cache(maxsize=None)
def _addressable_basket() -> pd.DataFrame:
    path = DERIVED_DIR / "bvp_addressable_basket.csv"
    return pd.read_csv(path) if path.exists() else pd.DataFrame()

def addressable_for(distributor_code: str) -> set[tuple[str, str]]:
    """Return {(subgroup, bvp_pn)} a distributor can address by lifetime Genuine sales."""
    df = _addressable_basket()
    if df.empty:
        return set()
    d = df[df["distributor_code"] == distributor_code]
    return set(zip(d["product_subgroup"], d["bvp_pn"]))

def is_addressable_subgroup(distributor_code: str, subgroup: str) -> bool:
    df = _addressable_basket()
    if df.empty:
        return False
    return ((df["distributor_code"] == distributor_code) & (df["product_subgroup"] == subgroup)).any()
```

5. **Update `attach_navigation_columns` and `filter_in_scope`** — the current ones filter on `IN_SCOPE_SUBCATEGORIES`. Either:
   - (a) Add `distributor_code` parameter and filter by addressable basket if provided, or
   - (b) Set `dashboard_scope=True` for all subgroups (so the dashboard sees the full 27), and rely on the addressable-basket join in the Streamlit page for the per-distributor scoping.

**Recommend approach (b)** — keeps the helper functions distributor-agnostic. The dashboard does the addressable filter at render time.

---

## Task 3 — Rebuild dependent derived files with the new taxonomy

Re-run in order (existing scripts, no code change needed once Task 2 is merged):

```powershell
cd $env:ISZE_ROOT\03_analytics\Isuzu\prism
python scripts\build_bvp_p0_p1.py            # dimension + crossref
python scripts\build_bvp_crossref_sales.py   # substitution_db, substitution_pair
python scripts\build_bvp_p2_mix.py           # mix_genuine_bvp_by_* (now covers 27 subgroups)
python scripts\build_bvp_p4_p5.py            # benchmark + aim
python scripts\build_bvp_addressable_basket.py   # ← NEW from Task 1
python scripts\verify_derived_pipeline.py
```

**Spot-check after rebuild:**
- `mix_genuine_bvp_pms.csv` should now have rows for `clutch_kit`, `shock_absorber`, `urea_filter`, `wiper_blade`, etc. (previously only 7 subgroups)
- `bvp_pn_dimension.csv` should have `dashboard_scope=True` for ~all 919 PNs (vs 317 today) — or keep the column but flip the filter to the addressable basket.

---

## What I'm NOT asking for

- ❌ R90 enrichment — not needed. Genuine sales is the eligibility proxy.
- ❌ Market eligibility matrix (EU / MEA / Asia / AUS-NZ rules) — not needed.
- ❌ Vehicle-age refinement — defer to phase 2.
- ❌ Origin-based filtering — informational only on the catalog tab.

---

## Acceptance criteria

1. `bvp_addressable_basket.csv` exists, passes verify fixture.
2. `mix_genuine_bvp_pms.csv` has rows for all 27 BVP subgroups (with zero-data subgroups omitted naturally — clutch_booster has €1k Genuine, that's fine).
3. `bvp_product_nav.py` exports 8 product groups; helpers `addressable_for(dist)` and `is_addressable_subgroup(dist, sg)` work.
4. Streamlit `4_BVP.py` group selector shows 8 groups (rendering pass — Claude follow-up).
