"""Distributor settings.

Two files are read and merged, in this order:

  04_tools/db_sales_review/db_profiles.yaml   the main registry (read-only for us)
  04_tools/db_bpr_deck/config/distributors.yaml   our overlay

Nothing here writes to the main registry.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .errors import BprError
from .paths import DATA_ROOT, ISZE_ROOT

_MAIN_REGISTRY = ISZE_ROOT / "04_tools" / "db_sales_review" / "db_profiles.yaml"
_OVERLAY = Path(__file__).resolve().parent / "config" / "distributors.yaml"


@dataclass
class DistConfig:
    """Everything the tool needs about one distributor."""

    key: str
    name: str
    country: str
    display: str
    segment: str
    # from the main registry
    gps_key: str | None = None
    pms_code: str | None = None
    sold_to: int | None = None
    payer: str | None = None
    watch: list[str] = field(default_factory=list)
    build_enabled: bool = True
    deck_opts: dict = field(default_factory=dict)
    # from our overlay
    kpi_name: str | None = None
    sellout_dir: str | None = None
    sellout_kind: str | None = None
    sellout_normalizer: str | None = None   # refresh script in 01_data/91_build, or null
    fleet_source: str = "band_counts"
    fleet_file: str | None = None
    blocks_off: list[str] = field(default_factory=list)
    # codes used by other systems, when they differ from the settings key
    billing_codes: str | None = None     # PRISM sap_sold_to_mapping.csv distributor_code
    gps_code: str | None = None          # gps_spu_by_distributor / uio file code
    kpi_names: list[str] = field(default_factory=list)   # every label this DB has in the KPI file

    @property
    def has_sellout(self) -> bool:
        return bool(self.sellout_dir and self.sellout_kind)

    @property
    def raw_sellout_dir(self) -> Path | None:
        if not self.sellout_dir:
            return None
        return DATA_ROOT / "12_raw" / "dealer_sales" / self.sellout_dir


def _read_yaml(path: Path) -> dict:
    if not path.is_file():
        raise BprError("E102", f"Settings file not found: {path.name}", path=path,
                       expected="an existing YAML settings file")
    try:
        with path.open(encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except Exception as exc:
        raise BprError("E202", f"The settings file could not be read: {exc}", path=path) from exc


def load_registries() -> tuple[dict, dict]:
    main = _read_yaml(_MAIN_REGISTRY).get("distributors") or {}
    overlay = _read_yaml(_OVERLAY)
    return main, overlay


def list_keys() -> list[str]:
    """Every distributor this tool can build, from either settings file.

    The main registry is the fuller record, but a distributor the review still covers may be
    missing from it. The overlay can therefore define one on its own, which is how UTI (Israel,
    the truck side) is set up: the sales-review registry has no UTI block, and this tool must not
    edit that file.
    """
    main, overlay = load_registries()
    return sorted(set(main.keys()) | set((overlay.get("distributors") or {}).keys()))


def load(key: str) -> DistConfig:
    key = (key or "").strip().upper()
    main, overlay = load_registries()
    extra = dict((overlay.get("distributors") or {}).get(key) or {})
    if key not in main and not extra:
        raise BprError(
            "E101",
            f"'{key}' is not a distributor in the settings file.",
            db=key,
            expected="one of: " + ", ".join(list_keys()),
            found=key,
        )
    if key not in main:
        # defined in the overlay alone: the overlay must then carry the identifying fields too
        missing = [f for f in ("name", "country", "display") if not extra.get(f)]
        if missing:
            raise BprError(
                "E101",
                f"{key} is set up in this tool's settings but is missing {', '.join(missing)}, "
                "and it has no block in the main distributor registry to fall back on.",
                db=key,
                expected="name, country and display in config/distributors.yaml",
                found=", ".join(sorted(extra.keys())),
            )
    base = dict(main.get(key) or {})
    pbi = base.pop("pbi", None)
    return DistConfig(
        key=key,
        name=base.get("name", key),
        country=base.get("country", ""),
        display=base.get("display", key),
        segment=base.get("segment", ""),
        gps_key=base.get("gps_key"),
        pms_code=base.get("pms_code"),
        sold_to=base.get("sold_to"),
        payer=base.get("payer"),
        watch=list(base.get("watch") or []),
        build_enabled=bool(base.get("build_enabled", True)),
        deck_opts=dict(base.get("deck") or {}),
        kpi_name=extra.get("kpi_name"),
        sellout_dir=extra.get("sellout_dir"),
        sellout_kind=extra.get("sellout_kind"),
        sellout_normalizer=extra.get("sellout_normalizer"),
        fleet_source=extra.get("fleet_source", "band_counts"),
        fleet_file=extra.get("fleet_file"),
        blocks_off=list(extra.get("blocks_off") or []),
        billing_codes=extra.get("billing_codes"),
        gps_code=extra.get("gps_code"),
        kpi_names=list(extra.get("kpi_names") or []),
    )


def overlay_defaults() -> dict:
    _, overlay = load_registries()
    return dict(overlay.get("defaults") or {})
