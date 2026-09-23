"""Cloud checkout without the UIO / FY27 workbooks still builds from derived files."""

from __future__ import annotations

import common as C


def test_ireland_carpark_uio_has_2025_2026() -> None:
    p = C.load_profile("IRELAND")
    uio = C.load_uio(p)
    assert uio["total"][2025] > 0
    assert uio["total"][2026] > 0
    assert "md" not in uio  # exclude_uio_segments: [md]


def test_ituk_not_iuk() -> None:
    ituk = C.load_profile("ITUK")
    iuk = C.load_profile("IUK")
    assert ituk["sold_to"] == 2575
    assert iuk["sold_to"] == 2574
    fy = C.load_fy27(ituk)
    assert fy["s2d_target"]["s2d_imputed"] is True
    assert fy["actual"]["fy26"] is not None


def test_portugal_pbi_uses_yaml_not_stale_summary() -> None:
    p = C.load_profile("PORTUGAL")
    assert p["pbi"]["sales"] == [140000, 151000, 153000]
    assert 92 in (p.get("sold_to_aliases") or [])


def test_ireland_skips_gps_pct() -> None:
    p = C.load_profile("IRELAND")
    gps = C.load_segmented_gps(p)
    assert gps is not None
    assert gps["show_pct"] is False
    assert (p.get("deck") or {}).get("skip_gps_pct") is True
