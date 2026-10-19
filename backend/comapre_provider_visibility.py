
from pathlib import Path

import pandas as pd

EXPORT_DIR = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "processed"
    / "exports"
)

groq = pd.read_parquet(
    EXPORT_DIR / "brand_visibility_groq_all_beauty.parquet"
)
openrouter = pd.read_parquet(
    EXPORT_DIR / "brand_visibility_openrouter_all_beauty.parquet"
)

# Exact canonical store names matched by both providers.
comparison = groq.merge(
    openrouter,
    on="store",
    how="inner",
    suffixes=("_groq", "_openrouter"),
)

# Keep brands with actual visibility for both providers.
comparison = comparison[
    (comparison["visibility_score_groq"] > 0)
    & (comparison["visibility_score_openrouter"] > 0)
].copy()

comparison["visibility_difference_groq_minus_openrouter"] = (
    comparison["visibility_score_groq"]
    - comparison["visibility_score_openrouter"]
)

comparison = comparison.sort_values(
    "visibility_difference_groq_minus_openrouter",
    ascending=False,
)

print("Brands visible to both providers:", len(comparison))
print()

columns = [
    "store",
    "mention_count_groq",
    "mean_position_groq",
    "visibility_score_groq",
    "mention_count_openrouter",
    "mean_position_openrouter",
    "visibility_score_openrouter",
    "visibility_difference_groq_minus_openrouter",
]

if comparison.empty:
    print("No exact-match brands were visible to both providers.")
else:
    print("Largest Groq visibility advantages:")
    print(comparison.head(10)[columns].to_string(index=False))

    print("\nLargest OpenRouter visibility advantages:")
    print(
        comparison.tail(10)
        .sort_values(
            "visibility_difference_groq_minus_openrouter"
        )[columns]
        .to_string(index=False)
    )

    output_path = EXPORT_DIR / "provider_visibility_comparison_all_beauty.parquet"
    comparison.to_parquet(output_path, index=False)
    print("\nSaved:", output_path.name)