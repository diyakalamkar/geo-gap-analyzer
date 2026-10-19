
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = PROJECT_ROOT / "data" / "processed" / "exports"

PROVIDERS = ["groq", "openrouter"]

MERIT_MAX = 100.0
VISIBILITY_MAX = 4.0

for provider in PROVIDERS:
    input_path = (
        EXPORT_DIR / f"brand_comparison_{provider}_all_beauty.parquet"
    )
    output_path = (
        EXPORT_DIR / f"geo_gap_{provider}_all_beauty.parquet"
    )

    df = pd.read_parquet(input_path)

    df["normalized_merit"] = (
        df["ground_truth_merit_score"] / MERIT_MAX
    ).clip(0, 1)

    df["normalized_visibility"] = (
        df["visibility_score"] / VISIBILITY_MAX
    ).clip(0, 1)

    df["geo_gap"] = (
        df["normalized_merit"] - df["normalized_visibility"]
    )

    df["gap_status"] = "Balanced"
    df.loc[df["geo_gap"] > 0, "gap_status"] = "Under-visible"
    df.loc[df["geo_gap"] < 0, "gap_status"] = "Over-visible"

    df = df.sort_values("geo_gap", ascending=False)

    df.to_parquet(output_path, index=False)

    print(f"\n--- {provider.upper()} ---")
    print("Saved:", output_path.name)
    print("Brands evaluated:", len(df))

    print("\nTop 10 under-visible brands:")
    print(
        df.nlargest(10, "geo_gap")[
            [
                "store",
                "ground_truth_merit_score",
                "visibility_score",
                "normalized_merit",
                "normalized_visibility",
                "geo_gap",
            ]
        ].to_string(index=False)
    )

    print("\nTop 10 over-visible brands:")
    print(
        df.nsmallest(10, "geo_gap")[
            [
                "store",
                "ground_truth_merit_score",
                "visibility_score",
                "normalized_merit",
                "normalized_visibility",
                "geo_gap",
            ]
        ].to_string(index=False)
    )

print("\nGeo-Gap calculations completed.")