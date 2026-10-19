"""Export Person 3's validated Excel workbook into JSON consumed by React."""
from pathlib import Path
import json
import math
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "data" / "processed" / "exports" / "P3_visibility_gap_results.xlsx"
OUT = ROOT / "src" / "data"


def clean(value):
    if value is None:
        return None
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def write_json(name, value):
    (OUT / name).write_text(
        json.dumps(clean(value), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main():
    if not WORKBOOK.exists():
        print(f"ERROR: Person 3 workbook not found: {WORKBOOK}", file=sys.stderr)
        print("Run validate_p3.py with EXPORT = True first.", file=sys.stderr)
        raise SystemExit(1)

    OUT.mkdir(parents=True, exist_ok=True)
    gap = pd.read_excel(WORKBOOK, sheet_name="brand_gap")
    visibility = pd.read_excel(WORKBOOK, sheet_name="brand_visibility")

    # Keep the existing component contracts while using Person 3's real outputs.
    if "brand_key" not in gap.columns:
        gap["brand_key"] = gap.get("norm_name", gap["brand"]).astype(str)
    if "norm_name" not in gap.columns:
        gap["norm_name"] = gap["brand_key"].astype(str)

    if "brand" not in visibility.columns:
        if "brand_canonical" in visibility.columns:
            visibility["brand"] = visibility["brand_canonical"]
        else:
            raise ValueError("brand_visibility sheet needs a 'brand' or 'brand_canonical' column")
    if "brand_canonical" not in visibility.columns:
        visibility["brand_canonical"] = visibility["brand"]

    write_json("p3BrandGap.json", gap.to_dict(orient="records"))
    write_json("p3BrandVisibility.json", visibility.to_dict(orient="records"))

    validation = {}
    for sheet in ("coverage_provider", "coverage_persona", "coverage_intent", "bootstrap", "sensitivity"):
        validation[sheet] = pd.read_excel(WORKBOOK, sheet_name=sheet).to_dict(orient="records")
    validation["meta"] = {
        "workbook": WORKBOOK.name,
        "valid_responses": 37,
        "brands_compared": int(len(gap)),
        "brands_mentioned": int((pd.to_numeric(gap["mentions"], errors="coerce").fillna(0) > 0).sum()),
    }
    write_json("p3Validation.json", validation)
    print(f"Exported Person 3 data into {OUT}")
    print(f"  brand gap rows: {len(gap)}")
    print(f"  brand visibility rows: {len(visibility)}")
    print("  validation: provider/persona/intent/bootstrap/sensitivity")


if __name__ == "__main__":
    main()
