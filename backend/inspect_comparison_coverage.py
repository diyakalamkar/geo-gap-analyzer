
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = PROJECT_ROOT / "data" / "processed" / "exports"

PROVIDERS = ["groq", "openrouter"]

for provider in PROVIDERS:
    file_path = (
        EXPORT_DIR / f"brand_comparison_{provider}_all_beauty.parquet"
    )

    print("\n" + "=" * 65)
    print(f"PROVIDER: {provider.upper()}")
    print("=" * 65)

    if not file_path.exists():
        print(f"File not found: {file_path}")
        continue

    df = pd.read_parquet(file_path)

    print(f"\nFile: {file_path.name}")
    print(f"Total rows: {len(df):,}")
    print(f"Columns: {df.columns.tolist()}")

    required = [
        "store",
        "ground_truth_merit_score",
        "visibility_score",
    ]

    missing = [col for col in required if col not in df.columns]

    if missing:
        print(f"Missing required columns: {missing}")
        continue

    df["visibility_score"] = pd.to_numeric(
        df["visibility_score"], errors="coerce"
    )
    df["ground_truth_merit_score"] = pd.to_numeric(
        df["ground_truth_merit_score"], errors="coerce"
    )

    observed = df[df["visibility_score"] > 0].copy()
    zero_visibility = df[df["visibility_score"] == 0].copy()
    missing_visibility = df[df["visibility_score"].isna()].copy()

    print(f"\nUnique store names: {df['store'].nunique():,}")
    print(f"Rows with visibility > 0: {len(observed):,}")
    print(f"Unique observed brands: {observed['store'].nunique():,}")
    print(f"Rows with visibility = 0: {len(zero_visibility):,}")
    print(f"Rows with missing visibility: {len(missing_visibility):,}")
    print(
        "Missing merit scores:",
        df["ground_truth_merit_score"].isna().sum(),
    )

    print("\nDuplicate store-name rows:")
    print(int(df["store"].duplicated().sum()))

    print("\nObserved brands, sorted by visibility:")
    columns = [
        "store",
        "ground_truth_merit_score",
        "visibility_score",
    ]

    extra = [
        col for col in ["mention_count", "prompts_mentioned", "mean_position"]
        if col in df.columns
    ]
    columns.extend(extra)

    print(
        observed.sort_values("visibility_score", ascending=False)[columns]
        .to_string(index=False)
    )

    print("\nMerit summary for observed brands:")
    print(observed["ground_truth_merit_score"].describe().round(4))

    print("\nVisibility summary for observed brands:")
    print(observed["visibility_score"].describe().round(4))

print("\nInspection completed. No files were modified.")
