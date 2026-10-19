import re
import unicodedata


def normalize_name(value: str) -> str:
    """
    Normalize a product or brand name for matching.

    The original value is never modified in the source data.
    This function only creates a normalized matching key.
    """
    if value is None:
        return ""

    value = str(value).strip()

    if not value:
        return ""

    # Normalize Unicode characters.
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        char for char in value
        if not unicodedata.combining(char)
    )

    # Remove trademark/copyright symbols.
    value = re.sub(r"[®™©]", "", value)

    # Convert common separators to spaces.
    value = re.sub(r"[-_/]+", " ", value)

    # Remove remaining punctuation.
    value = re.sub(r"[^\w\s]", " ", value)

    # Collapse repeated whitespace.
    value = re.sub(r"\s+", " ", value)

    return value.strip().lower()


if __name__ == "__main__":
    test_values = [
        "L.A. Girl",
        "L'Oréal Paris",
        "Bath & Body Works",
        "Sekaler Heated Eyelash Curler – Rechargeable",
        "M.A.C",
    ]

    for value in test_values:
        print(f"{value!r} -> {normalize_name(value)!r}")