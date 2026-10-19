from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class LLMProductMention:
    product_name: str
    brand_name: Optional[str] = None
    position: Optional[int] = None


@dataclass
class LLMResponse:
    provider: str
    model: str
    category: str
    query_id: str
    intent: str
    prompt: str
    response_text: str
    product_mentions: List[LLMProductMention]

    prompt_id: Optional[str] = None
    base_query_id: Optional[str] = None
    persona: Optional[str] = None
    target_brands: Optional[List[str]] = None
    comparison_brands: Optional[List[str]] = None
    run_id: Optional[str] = None
    timestamp_utc: Optional[str] = None

    def to_dict(self):
        data = asdict(self)

        data["product_mentions"] = [
            asdict(product)
            for product in self.product_mentions
        ]

        return data


if __name__ == "__main__":
    response = LLMResponse(
        provider="test",
        model="test-model",
        category="beauty products",
        query_id="recommendation_01",
        intent="product_recommendation",
        prompt="What beauty products would you recommend?",
        response_text="I recommend Product A and Product B.",
        product_mentions=[
            LLMProductMention(
                product_name="Product A",
                brand_name="Brand A",
                position=1,
            ),
            LLMProductMention(
                product_name="Product B",
                brand_name="Brand B",
                position=2,
            ),
        ],
    )

    print(response.to_dict())