import re
from typing import List, Dict


def clean_brand_name(value: str) -> str:
    value = value.strip()

    # Remove Markdown bold.
    value = re.sub(r"\*\*(.*?)\*\*", r"\1", value)

    # Remove Markdown italic markers.
    value = re.sub(
        r"\*([^*]+)\*",
        r"\1",
        value,
    )

    # Remove Markdown links.
    value = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        value,
    )

    # Remove HTML line-break tags.
    value = re.sub(
        r"<br\s*/?>",
        " ",
        value,
        flags=re.IGNORECASE,
    )

    # Remove everything from the first parenthesis onward.
    # The parenthetical text contains example products,
    # not part of the brand name.
    value = re.sub(
        r"\s*\(.*$",
        "",
        value,
    )

    # Remove leading/trailing bullet characters.
    value = re.sub(
        r"^[•●▪◦*-]\s*",
        "",
        value,
    )

    return value.strip()


def classify_brand_response(response_text: str) -> str:
    """Classify whether a brand-list response is usable for extraction."""

    text = (response_text or "").strip()

    if not text:
        return "empty_response"

    # Detect provider/status messages rather than brand-list answers.
    if re.fullmatch(
        r"User Safety:\s*safe",
        text,
        flags=re.IGNORECASE,
    ):
        return "provider_status_response"

    # Check for a Markdown table with a Brand column.
    for line in text.splitlines():
        stripped = line.strip()

        if not stripped.startswith("|"):
            continue

        cells = [
            cell.strip()
            for cell in stripped.strip("|").split("|")
        ]

        headers = [
            re.sub(r"[^a-z0-9]+", " ", cell.lower()).strip()
            for cell in cells
        ]

        if "brand" in headers:
            return "brand_table_found"

    return "missing_brand_table"

def is_separator_row(cells: List[str]) -> bool:
    if not cells:
        return False

    return all(
        re.fullmatch(
            r":?-+:?",
            cell.replace(" ", ""),
        )
        for cell in cells
    )


def extract_brands_from_response(
    query_id: str,
    response_text: str,
) -> List[Dict]:

    if not query_id.startswith("brand_01_"):
        return []

    brands = []

    lines = response_text.splitlines()

    active_brand_table = False
    brand_column_index = None
    current_position = 0

    for line in lines:
        stripped = line.strip()

        if not stripped.startswith("|"):
            active_brand_table = False
            brand_column_index = None
            continue

        cells = [
            cell.strip()
            for cell in stripped.strip("|").split("|")
        ]

        if not cells:
            continue

        if is_separator_row(cells):
            continue

        normalized_headers = [
            re.sub(
                r"[^a-z0-9]+",
                " ",
                cell.lower(),
            ).strip()
            for cell in cells
        ]

        if "brand" in normalized_headers:
            brand_column_index = normalized_headers.index("brand")
            active_brand_table = True
            current_position = 0
            continue

        if not active_brand_table:
            continue

        if brand_column_index is None:
            continue

        if brand_column_index >= len(cells):
            continue

        cell_value = cells[brand_column_index]

        # The response uses <br> to separate brands.
        candidates = re.split(
            r"<br\s*/?>",
            cell_value,
            flags=re.IGNORECASE,
        )

        for candidate in candidates:
            candidate = clean_brand_name(candidate)

            if not candidate:
                continue

            current_position += 1

            brands.append(
                {
                    "brand_name": candidate,
                    "position": current_position,
                    "query_id": query_id,
                }
            )

    return brands


if __name__ == "__main__":
    from app.geo_gap.response_store import load_responses

    responses = load_responses(
        "beauty_products_groq.jsonl"
    )

    for response in responses:
        if response["query_id"] != "brand_01":
            continue

        print("=" * 80)
        print("Query:", response["query_id"])

        brands = extract_brands_from_response(
            response["query_id"],
            response["response_text"],
        )

        print("Extracted brands:", len(brands))

        for brand in brands:
            print(
                f"{brand['position']}. "
                f"{brand['brand_name']}"
            )