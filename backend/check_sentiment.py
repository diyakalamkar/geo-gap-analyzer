from pathlib import Path

import duckdb

BASE_DIR = Path(__file__).resolve().parents[1]
SENTIMENT_DIR = BASE_DIR / "data" / "processed" / "review_sentiment"

categories = [
    "All_Beauty",
    "Beauty_and_Personal_Care",
]

con = duckdb.connect()

for category in categories:
    path = SENTIMENT_DIR / f"{category}.parquet"

    print(f"\n=== {category} ===")
    print(f"File exists: {path.exists()}")
    print(f"Path: {path}")

    result = con.execute(
        """
        SELECT
            COUNT(*) AS total_rows,
            COUNT(review_id) AS review_ids,
            COUNT(sentiment_compound) AS scored_reviews,
            COUNT(*) - COUNT(sentiment_compound) AS null_sentiment,
            MIN(sentiment_compound) AS min_sentiment,
            MAX(sentiment_compound) AS max_sentiment,
            AVG(sentiment_compound) AS avg_sentiment
        FROM read_parquet(?)
        """,
        [str(path)],
    ).fetchone()

    print(f"Total rows:       {result[0]:,}")
    print(f"Review IDs:       {result[1]:,}")
    print(f"Scored reviews:   {result[2]:,}")
    print(f"NULL sentiment:   {result[3]:,}")
    print(f"Min sentiment:    {result[4]}")
    print(f"Max sentiment:    {result[5]}")
    print(f"Avg sentiment:    {result[6]}")

con.close()