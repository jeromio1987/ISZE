from pathlib import Path

path = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29c_ids_ituk_pt\Isuzu Universe\05_AIM_Universe\tools\connect_real_feeds.py")
text = path.read_text(encoding="utf-8")

old_case = '''        "8983682091": {
            "case_id": "ITUK-EXH-ELIG",
            "name": "Exhaust pipe (eligible UK shop)",
            "category": "Exhaust",
            "unit": "piece",
            "tier": "Genuine",
            "description": "PIPE; EXH",
        },
    }'''

new_case = '''        "8983682091": {
            "case_id": "ITUK-EXH-ELIG",
            "name": "Exhaust pipe (eligible UK shop)",
            "category": "Exhaust",
            "unit": "piece",
            "tier": "Genuine",
            "description": "PIPE; EXH",
        },
        "8980806782": {
            "case_id": "ITUK-AXL-ELIG",
            "name": "Drive half axle shaft (eligible UK shop)",
            "category": "Axle / driveline",
            "unit": "piece",
            "tier": "Genuine",
            "description": "SHAFT; AXLE, HALF, RR",
        },
    }'''

if old_case not in text:
    raise SystemExit("CASE_META anchor not found")
text = text.replace(old_case, new_case, 1)

old_loop = '''    offers = []
    by_case = {}
    for _, row in ledger.iterrows():
        oid = str(row["obs_id"])
        st = stage_by_id.get(oid)
        if not st:
            continue
        pn = str(row["part_no"])
        meta = CASE_META.get(pn)
        if not meta:
            continue
        loader = str(row.get("loader") or "")
        kind = "Genuine" if loader == "ks_gen" else "Aftermarket"
        offer_id = f"KS-{oid[:10]}"
        observed = str(row.get("observed_at") or st.get("observed_date") or "")[:10]
        offers.append({
            "id": offer_id,
            "observation_id": oid,
            "seller": "KS International",
            "market": "UK",
            "part": pn,
            "price": float(row["price"]) if pd.notna(row.get("price")) else None,
            "currency": str(row.get("currency") or st.get("currency") or "GBP"),
            "tax": "excluded",
            "vat": 0,
            "vat_rate": 0,
            "net": float(row["price"]) if pd.notna(row.get("price")) else None,
            "url": _name(row.get("source_url")),
            "retrieved": observed,
            "freshness": (
                "Coverage-eligible KS listing: VAT excl, mainland carriage GBP 10 stated, "
                "exact_oem match. Delivery cost converted in the U19 evidence stage, not invented here."
            ),
            "match": "Exact Genuine part number",
            "match_status": "unresolved",
            "match_reason": (st.get("match") or {}).get("note"),
            "note": _name(row.get("description")) or meta["description"],
            "kind": kind,
            "approvalReady": False,
            "verification": (
                "price_observations.parquet exact_oem + "
                "market_data_gap_coverage_uk_wider_exact_20261007 eligible evidence row"
            ),
            "case_id": meta["case_id"],
            "observation_declarations": {
                "level": "public_advertised_retail",
                "unit": "piece",
                "match_basis": "exact_part_number",
                "role": "competitor",
                "amount_scope": "per_piece",
                "vat_rate_unit": "percent",
                "delivery_included": False,
                "delivery_cost_eur": st.get("delivery_cost_eur"),
                "fx_rates": {
                    "GBP": {
                        "rate": st.get("fx_to_eur"),
                        "date": st.get("fx_date"),
                    }
                },
            },
            "_ledger": {
                "loader": loader,
                "price_type": _name(row.get("price_type")),
                "vat": _name(row.get("vat")),
                "match_method": _name(row.get("match_method")),
                "delivery_included": _name(row.get("delivery_included")),
                "delivery_cost_amount": (
                    None if pd.isna(row.get("delivery_cost_amount"))
                    else float(row.get("delivery_cost_amount"))
                ),
                "delivery_cost_currency": _name(row.get("delivery_cost_currency")),
            },
        })
        by_case.setdefault(meta["case_id"], []).append(offer_id)'''

new_loop = '''    offers = []
    by_case = {}
    for _, row in ledger.iterrows():
        oid = str(row["obs_id"])
        st = stage_by_id.get(oid)
        if not st:
            continue
        pn = str(row["part_no"])
        meta = CASE_META.get(pn)
        if not meta:
            continue
        loader = str(row.get("loader") or "")
        source = str(st.get("source") or row.get("source") or "").strip()
        is_omega = loader == "omega" or source.lower() == "omega"
        is_ks = loader.startswith("ks_") or "ks-international" in source.lower()

        if loader == "ks_gen" or (
            is_omega and "genuine" in str(row.get("description") or "").lower()
        ):
            kind = "Genuine"
        elif loader == "ks_am" or is_omega:
            kind = "Aftermarket"
        else:
            kind = "Aftermarket"

        if is_omega:
            offer_id = f"OMEGA-{oid[:10]}"
            seller = "Omega Spare Parts"
            tax = "included" if str(st.get("tax") or row.get("vat") or "").lower() in (
                "included", "incl"
            ) else str(st.get("tax") or "included")
            vat_rate = float(st.get("vat_rate") if st.get("vat_rate") is not None else (
                row["vat_rate"] if pd.notna(row.get("vat_rate")) else 20
            ))
            delivery_included = True if st.get("delivery_included") is True or str(
                row.get("delivery_included") or ""
            ).lower() == "yes" else bool(st.get("delivery_included"))
            freshness = (
                "Coverage-eligible Omega listing: VAT incl 20% (Terms of Business), "
                "UK Free Economy Delivery GBP 0.00 from Store API cart quote, "
                "exact_oem match. Delivery included on the ledger after the Omega hunt; "
                "not invented here."
            )
        elif is_ks:
            offer_id = f"KS-{oid[:10]}"
            seller = "KS International"
            tax = "excluded"
            vat_rate = 0
            delivery_included = False
            freshness = (
                "Coverage-eligible KS listing: VAT excl, mainland carriage GBP 10 stated, "
                "exact_oem match. Delivery cost converted in the U19 evidence stage, not invented here."
            )
        else:
            # Unknown eligible host: keep stage fields, do not invent a shop brand story.
            offer_id = f"SHOP-{oid[:10]}"
            seller = _name(st.get("seller")) or _name(source) or "UK shop"
            tax = str(st.get("tax") or "excluded")
            vat_rate = float(st.get("vat_rate") or 0)
            delivery_included = bool(st.get("delivery_included"))
            freshness = (
                "Coverage-eligible UK shop listing from ledger + U19 stage. "
                "Tax and delivery taken from those files only."
            )

        price = float(row["price"]) if pd.notna(row.get("price")) else None
        # For VAT-included prices keep advertised amount; net is not recomputed here.
        net = price
        observed = str(row.get("observed_at") or st.get("observed_date") or "")[:10]
        decls = {
            "level": "public_advertised_retail",
            "unit": "piece",
            "match_basis": "exact_part_number",
            "role": "competitor",
            "amount_scope": "per_piece",
            "vat_rate_unit": "percent",
            "delivery_included": delivery_included,
            "fx_rates": {
                "GBP": {
                    "rate": st.get("fx_to_eur"),
                    "date": st.get("fx_date"),
                }
            },
        }
        if st.get("delivery_cost_eur") is not None:
            decls["delivery_cost_eur"] = st.get("delivery_cost_eur")
        if vat_rate:
            decls["vat_rate"] = vat_rate

        offers.append({
            "id": offer_id,
            "observation_id": oid,
            "seller": seller,
            "market": "UK",
            "part": pn,
            "price": price,
            "currency": str(row.get("currency") or st.get("currency") or "GBP"),
            "tax": tax,
            "vat": vat_rate,
            "vat_rate": vat_rate,
            "net": net,
            "url": _name(row.get("source_url")),
            "retrieved": observed,
            "freshness": freshness,
            "match": "Exact Genuine part number",
            "match_status": "unresolved",
            "match_reason": (st.get("match") or {}).get("note"),
            "note": _name(row.get("description")) or meta["description"],
            "kind": kind,
            "approvalReady": False,
            "verification": (
                "price_observations.parquet exact_oem + "
                "market_data_gap_coverage_uk_wider_exact_20261007 eligible evidence row"
            ),
            "case_id": meta["case_id"],
            "observation_declarations": decls,
            "_ledger": {
                "loader": loader,
                "price_type": _name(row.get("price_type")),
                "vat": _name(row.get("vat")),
                "match_method": _name(row.get("match_method")),
                "delivery_included": _name(row.get("delivery_included")),
                "delivery_cost_amount": (
                    None if pd.isna(row.get("delivery_cost_amount"))
                    else float(row.get("delivery_cost_amount"))
                ),
                "delivery_cost_currency": _name(row.get("delivery_cost_currency")),
                "source": source,
            },
        })
        by_case.setdefault(meta["case_id"], []).append(offer_id)'''

if old_loop not in text:
    raise SystemExit("offer loop anchor not found")
text = text.replace(old_loop, new_loop, 1)

text = text.replace(
    "coverage-eligible UK KS shop rows + Eucon survey",
    "coverage-eligible UK shop rows (KS + Omega) + Eucon survey",
)

path.write_text(text, encoding="utf-8")
print("patched", path)
print("has AXL", "ITUK-AXL-ELIG" in text)
print("has OMEGA branch", 'f"OMEGA-' in text)
