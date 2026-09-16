# Chassis / generation → oil-interval map (θ_interval)

**Schedules used:** `01_data/03_PMS/service_schedules/` (RG21, RG, RT56, RT88_93, GIDSS N/F)  
**Map:** `chassis_generation_interval_map.yaml`  
**Code:** `theta_interval.py` (wired from `theta.attach`)

## Simple vs extended

| Mode | What it does | Moves alloc €? |
|------|----------------|----------------|
| **off** | θ_interval = 1.0 | No |
| **simple** (default now) | LCV DBs (IUK, UMI) × oil-linked cats use **assumed SCR share** × schedule lift (15k vs 20k = ×1.333) | **No** until you add `schedule_assumed_mix` to `theta.require_basis` |
| **extended** | Same, but SCR share from `lcv_generation_mix_by_db.csv` when filled | **No** until `schedule_measured_mix` allowed |

Assumed shares (edit in YAML): IUK **15%** SCR, UMI **25%**, other LCV **10%**.  
Example: IUK oil_filter θ_interval ≈ `0.85×1 + 0.15×1.333` ≈ **1.05**.

## From your PDFs (locked)

- **RG21 / RZ4F-TC with SCR:** oil + oil filter **15,000 km**  
- **RG21 without SCR, RG, RT56, RT88_93, 4JJ3, RZ4E:** **20,000 km**  
- N-series GIDSS oil is shorter (7.5–10k) — CV path; not this D-Max lever

## Still needed for extended (real mix)

Fill `01_data/00_derived/lcv_generation_mix_by_db.csv` (see `.TEMPLATE.csv`) with SCR vs legacy share by DB — from reg-year cutoffs or chassis flags. Car park alone still has no generation split.
