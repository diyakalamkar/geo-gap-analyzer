import re
from typing import List, Dict


def clean_markdown_product_name(value: str) -> str:
    value = value.strip()

    value = re.sub(r"\*\*(.*?)\*\*", r"\1", value)
    value = re.sub(r"__(.*?)__", r"\1", value)
    value = re.sub(r"\*([^*]+)\*", r"\1", value)

    value = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        value,
    )

    value = re.sub(r"<br\s*/?>", " ", value, flags=re.IGNORECASE)

    return value.strip()


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


def extract_standard_product_tables(
    response_text: str,
) -> List[Dict]:
    """
    Extract products from tables where a column is explicitly
    named Product or Item.
    """

    products = []

    lines = response_text.splitlines()

    active_product_table = False
    product_column_index = None
    current_product_position = 0

    for line in lines:
        stripped = line.strip()

        if not stripped.startswith("|"):
            active_product_table = False
            product_column_index = None
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

        if (
            "product" in normalized_headers
            or "item" in normalized_headers
        ):
            if "product" in normalized_headers:
                product_column_index = (
                    normalized_headers.index("product")
                )
            else:
                product_column_index = (
                    normalized_headers.index("item")
                )

            active_product_table = True
            current_product_position = 0
            continue

        if not active_product_table:
            continue

        if product_column_index is None:
            continue

        if product_column_index >= len(cells):
            continue

        product_name = clean_markdown_product_name(
            cells[product_column_index]
        )

        if not product_name:
            continue

        current_product_position += 1

        products.append(
            {
                "product_name": product_name,
                "position": current_product_position,
            }
        )

    return products


def extract_comparison_products(
    response_text: str,
) -> List[Dict]:
    """
    Extract products from comparison tables where the product
    column contains wording such as 'high-rated picks'.
    """

    products = []

    lines = response_text.splitlines()

    active_comparison_table = False
    product_column_index = None
    current_product_position = 0

    for line in lines:
        stripped = line.strip()

        if not stripped.startswith("|"):
            active_comparison_table = False
            product_column_index = None
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

        comparison_column_index = None

        for index, header in enumerate(normalized_headers):
            if (
                "high rated picks" in header
                or "high rated pick" in header
                or "typical high rated picks" in header
            ):
                comparison_column_index = index
                break

        if comparison_column_index is not None:
            product_column_index = comparison_column_index
            active_comparison_table = True
            current_product_position = 0
            continue

        if not active_comparison_table:
            continue

        if product_column_index is None:
            continue

        if product_column_index >= len(cells):
            continue

        cell_value = cells[product_column_index]

        # Remove markdown emphasis before splitting.
        cell_value = re.sub(
            r"\*([^*]+)\*",
            r"\1",
            cell_value,
        )

        # Products in this response are separated by commas.
        candidates = [
            candidate.strip()
            for candidate in cell_value.split(",")
        ]

        for candidate in candidates:
            candidate = clean_markdown_product_name(
                candidate
            )

            if not candidate:
                continue

            current_product_position += 1

            products.append(
                {
                    "product_name": candidate,
                    "position": current_product_position,
                }
            )

    return products


def extract_products_from_response(
    query_id: str,
    response_text: str,
) -> List[Dict]:

    products = extract_standard_product_tables(
        response_text
    )

    if not products:
        products = extract_comparison_products(
            response_text
        )

    for product in products:
        product["query_id"] = query_id

    return products


if __name__ == "__main__":
    from app.geo_gap.response_store import load_responses

    responses = load_responses(
        "beauty_products_groq.jsonl"
    )

    for response in responses:
        print("=" * 80)
        print("Query:", response["query_id"])

        products = extract_products_from_response(
            response["query_id"],
            response["response_text"],
        )

        print("Extracted products:", len(products))

        for product in products:
            print(
                f"{product['position']}. "
                f"{product['product_name']}"
            )