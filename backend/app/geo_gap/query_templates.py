from dataclasses import dataclass
from typing import List
from pathlib import Path
import pandas as pd
import hashlib


@dataclass(frozen=True)
class GeoGapQuery:
    query_id: str
    intent: str
    persona: str
    template: str

# Controlled persona variations.
# These are prompt variations for testing LLM visibility;
# they do NOT contain ground-truth product names.
PROJECT_ROOT = Path(__file__).resolve().parents[3]

MERIT_BRAND_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "exports"
    / "merit_brand.parquet"
)

CATEGORY_LABELS = {
    "All_Beauty": "beauty and personal care products",
    "Beauty_and_Personal_Care": "beauty and personal care products",
    "beauty products": "beauty products",
    "beauty and personal care products": "beauty and personal care products",
}

def load_brands(category: str, n: int = 20) -> list[str]:
    """Load top merit-ranked brands for a category."""

    df = pd.read_parquet(MERIT_BRAND_PATH)

    brands = (
        df[
            (df["category"] == category)
            & (df["merit_score"] > 0)
            & df["brand_canonical"].notna()
        ]
        .copy()
    )

    # Remove obvious malformed metadata-style entries.
    brands = brands[
        ~brands["brand_canonical"]
        .str.contains(
            r"^Format:|Format: (?:Audio CD|Theatrical Release)",
            case=False,
            regex=True,
            na=False,
        )
    ]

    brands = (
        brands
        .sort_values("merit_score", ascending=False)
        .drop_duplicates("brand_canonical")
        .head(n)
    )

    return brands["brand_canonical"].tolist()

def make_prompt_id(prompt: str) -> str:
    """Create a stable ID from the prompt text."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]

PERSONAS = [
    {
        "id": "general",
        "context": "",
    },
    {
        "id": "budget_conscious",
        "context": (
            "I am looking for good options that offer strong value "
            "for money and are reasonably priced."
        ),
    },
    {
        "id": "beginner",
        "context": (
            "I am a beginner and would prefer products that are "
            "easy to understand and suitable for someone starting out."
        ),
    },
    {
        "id": "sensitive_skin",
        "context": (
            "I have sensitive skin, so I prefer gentle products and "
            "would like recommendations suitable for sensitive skin."
        ),
    },
]

QUERY_TEMPLATES: List[GeoGapQuery] = [
    GeoGapQuery(
        query_id="discovery_01",
        intent="category_discovery",
        persona="general",
        template=(
            "What are some well-regarded {category} "
            "that customers commonly recommend?\n\n"
            "Return 5-10 recommendations in a markdown table "
            "with a 'Product' column."
        ),
    ),
    GeoGapQuery(
        query_id="recommendation_01",
        intent="product_recommendation",
        persona="general",
        template=(
            "What {category} would you recommend to a customer "
            "looking for reliable and well-reviewed options?\n\n"
            "Return 5-10 recommendations in a markdown table "
            "with a 'Product' column."
        ),
    ),
    GeoGapQuery(
        query_id="recommendation_02",
        intent="product_recommendation",
        persona="general",
        template=(
            "Which {category} have strong customer feedback "
            "and are worth considering?\n\n"
            "Return 5-10 recommendations in a markdown table "
            "with a 'Product' column."
        ),
    ),
    GeoGapQuery(
        query_id="problem_01",
        intent="problem_based",
        persona="general",
        template=(
            "I am looking for {category} with good customer "
            "satisfaction. What products should I consider?\n\n"
            "Return 5-10 recommendations in a markdown table "
            "with a 'Product' column."
        ),
    ),
    GeoGapQuery(
        query_id="comparison_01",
        intent="comparison",
        persona="general",
        template=(
            "Which brand would you recommend for {category}: "
            "{brand_a} or {brand_b}? "
            "Compare the two brands based on customer feedback, "
            "product quality, and overall suitability.\n\n"
            "Give a clear recommendation and briefly explain why."
        ),
    ),
    GeoGapQuery(
        query_id="brand_01",
        intent="brand_discovery",
        persona="general",
        template=(
            "Which brands are commonly recommended for {category}?\n\n"
            "Return 5-10 brand recommendations in a markdown table "
            "with a 'Brand' column. List one brand per row. "
            "Do not list product types or individual products."
        ),
    ),
]


def build_queries(category: str):
    """Build the full intent × persona query set with evaluation metadata."""

    target_brands = load_brands(category, n=20)
    category_label = CATEGORY_LABELS.get(category, category)

    queries = []

    # Create deterministic brand pairs from the merit-ranked list.
    comparison_pairs = [
        (target_brands[0], target_brands[1]),
        (target_brands[2], target_brands[3]),
        (target_brands[4], target_brands[5]),
        (target_brands[6], target_brands[7]),
        (target_brands[8], target_brands[9]),
    ]

    for base_query in QUERY_TEMPLATES:
        for persona in PERSONAS:
            persona_name = persona["id"]
            persona_text = persona["context"]

            if base_query.query_id == "comparison_01":
                for pair_index, (brand_a, brand_b) in enumerate(
                    comparison_pairs, start=1
                ):
                    prompt = base_query.template.format(
                        category=category_label,
                        brand_a=brand_a,
                        brand_b=brand_b,
                    )

                    if persona_text:
                        prompt = f"{prompt}\n\n{persona_text}"

                    prompt_id = make_prompt_id(prompt)

                    queries.append(
                        {
                            "query_id": (
                                f"{base_query.query_id}_"
                                f"pair_{pair_index}_"
                                f"{persona_name}"
                            ),
                            "base_query_id": base_query.query_id,
                            "intent": base_query.intent,
                            "persona": persona_name,
                            "category": category,
                            "prompt": prompt,
                            "prompt_id": prompt_id,
                            "target_brands": target_brands,
                            "comparison_brands": [brand_a, brand_b],
                        }
                    )

            else:
                prompt = base_query.template.format(
                    category=category_label
                )

                if persona_text:
                    prompt = f"{prompt}\n\n{persona_text}"

                prompt_id = make_prompt_id(prompt)

                queries.append(
                    {
                        "query_id": f"{base_query.query_id}_{persona_name}",
                        "base_query_id": base_query.query_id,
                        "intent": base_query.intent,
                        "persona": persona_name,
                        "category": category,
                        "prompt": prompt,
                        "prompt_id": prompt_id,
                        "target_brands": target_brands,
                    }
                )

    return queries


if __name__ == "__main__":
    for category in [
        "beauty products",
        "beauty and personal care products",
    ]:
        print("=" * 70)
        print(f"CATEGORY: {category}")
        print("=" * 70)

        queries = build_queries(category)

        print(f"Total queries generated: {len(queries)}")
        print()

        for query in queries:
            print(
                f"[{query['query_id']}] "
                f"{query['intent']} | "
                f"{query['persona']}"
            )
            print(query["prompt"])
            print()