
from app.geo_gap.brand_extractor import (
    classify_brand_response,
    extract_brands_from_response,
)

tests = [
    (
        "valid_table",
        "| Brand |\n|---|\n| CeraVe |\n| Clinique |",
        "brand_table_found",
    ),
    (
        "provider_status",
        "User Safety: safe",
        "provider_status_response",
    ),
    (
        "empty",
        "",
        "empty_response",
    ),
    (
        "no_table",
        "I recommend CeraVe and Clinique.",
        "missing_brand_table",
    ),
]

for name, response, expected in tests:
    actual = classify_brand_response(response)
    passed = actual == expected
    print(f"{name}: {actual} - {'PASS' if passed else 'FAIL'}")

    if name == "valid_table":
        brands = extract_brands_from_response(
            "brand_01_test",
            response,
        )
        print("Extracted brands:", [b["brand_name"] for b in brands])