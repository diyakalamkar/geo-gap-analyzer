from app.ingestion.brand_normalizer import clean_store_name

test_values = [
    "Bath & Body Works",
    "Bath and Body Works",
    "MAYBELLINE",
    "Maybelline New York",
    "e.l.f.",
    "L'Oreal Paris",
    "Victoria's Secret",
    "The Body Shop",
    "SheaMoisture",
    "CoCo-Shop",
    "Unknown",
    "Generic",
    "NaN",
    "WILLBOND",
    "S-noilite",
    "AVON",
    "KISS",
    "Estee Lauder",
]

print(f"{'RAW':35} -> CLEANED")
print("-" * 60)

for value in test_values:
    print(f"{value:35} -> {clean_store_name(value)!r}")