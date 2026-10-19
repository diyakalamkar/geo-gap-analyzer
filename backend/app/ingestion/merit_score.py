"""
merit_score.py  --  Ground-truth merit score per product and per brand
=======================================================================
merit score = rating x log(review volume) x recency decay

Concrete, documented implementation (all inside DuckDB SQL):
    reference date      = latest review date in that category (NOT today's date,
                          so results are reproducible on a frozen dataset)
    recency weight      = 0.5 ^ (review_age_days / RECENCY_HALF_LIFE_DAYS)  per review
    recency_factor      = mean of those weights over the entity's reviews  (0..1]
    merit_raw           = avg_rating x ln(1 + n_reviews) x recency_factor
    merit_score (0-100) = min-max of merit_raw within a category, computed only
                          over entities with n_reviews >= MIN_REVIEWS_FOR_RANKING
Extra columns are produced for Person 3 (gap score) and the dashboard:
    recency_weighted_rating, verified_share, total_helpful_votes,
    avg_sentiment, pct_positive / pct_neutral / pct_negative (VADER),
    merit_rank_in_category, merit_percentile.

Two grains are built:
    merit_product : per (category, parent_asin)          -- always available
    merit_brand   : per (category, brand_canonical)      -- only if metadata was loaded
                    (reviews are pooled per brand, not an average of product scores)
"""
import duckdb

from .config import (CLEAN_DIR, MIN_REVIEWS_FOR_RANKING, RECENCY_HALF_LIFE_DAYS,
                     SENTIMENT_DIR, VADER_NEG_THRESHOLD, VADER_POS_THRESHOLD)
from .duckdb_pipeline import _sql_path


def _tables(con) -> set:
    return {r[0] for r in con.execute("SHOW TABLES").fetchall()}


def build_base_views(con: duckdb.DuckDBPyConnection) -> None:
    """Create reviews_enriched (reviews + sentiment + brand) and category_ref_date."""
    con.execute(f"CREATE OR REPLACE VIEW reviews_clean AS "
                f"SELECT * FROM read_parquet('{_sql_path(CLEAN_DIR / '*.parquet')}')")
    con.execute(f"CREATE OR REPLACE VIEW review_sentiment AS "
                f"SELECT * FROM read_parquet('{_sql_path(SENTIMENT_DIR / '*.parquet')}')")

    has_brand = "product_brand" in _tables(con)
    brand_join = ("LEFT JOIN product_brand b ON b.category = r.category AND b.parent_asin = r.parent_asin"
                  if has_brand else "")
    brand_col = "b.brand_canonical" if has_brand else "CAST(NULL AS VARCHAR)"
    con.execute(f"""
        CREATE OR REPLACE TABLE reviews_enriched AS
        SELECT r.review_id, r.category, r.parent_asin, {brand_col} AS brand_canonical,
               r.rating, r.review_ts, r.helpful_vote, r.verified_purchase,
               s.sentiment_compound
        FROM reviews_clean r
        LEFT JOIN review_sentiment s USING (review_id)
        {brand_join}
    """)
    # reference date per category = newest review in that category
    con.execute("""
        CREATE OR REPLACE TABLE category_ref_date AS
        SELECT category, max(review_ts) AS ref_ts FROM reviews_clean GROUP BY category
    """)


def build_merit_table(con: duckdb.DuckDBPyConnection, grain: str,
                      half_life_days: float = RECENCY_HALF_LIFE_DAYS,
                      min_reviews: int = MIN_REVIEWS_FOR_RANKING) -> None:
    """Create table merit_product (grain='product') or merit_brand (grain='brand')."""
    if grain == "product":
        key, extra, where, table = "parent_asin", "", "", "merit_product"
    elif grain == "brand":
        key, extra, where, table = ("brand_canonical",
                                    ", count(DISTINCT parent_asin) AS n_products",
                                    "WHERE e.brand_canonical IS NOT NULL", "merit_brand")
    else:
        raise ValueError("grain must be 'product' or 'brand'")

    con.execute(f"""
        CREATE OR REPLACE TABLE {table} AS
        WITH base AS (
            SELECT e.category, e.{key}, e.parent_asin, e.rating, e.review_ts,
                   e.helpful_vote, e.verified_purchase, e.sentiment_compound,
                   -- per-review recency weight: halves every {half_life_days} days
                   power(0.5, greatest(date_diff('day', e.review_ts, d.ref_ts), 0) / {float(half_life_days)}) AS recency_w
            FROM reviews_enriched e
            JOIN category_ref_date d USING (category)
            {where}
        ),
        agg AS (
            SELECT category, {key}
                   {extra},
                   count(*)                                         AS n_reviews,
                   avg(rating)                                      AS avg_rating,
                   sum(rating * recency_w) / sum(recency_w)         AS recency_weighted_rating,
                   avg(recency_w)                                   AS recency_factor,
                   ln(1 + count(*))                                 AS log_volume,
                   avg(verified_purchase::INT)                      AS verified_share,
                   sum(helpful_vote)                                AS total_helpful_votes,
                   min(review_ts)                                   AS first_review_ts,
                   max(review_ts)                                   AS last_review_ts,
                   avg(sentiment_compound)                          AS avg_sentiment,
                   avg(CASE WHEN sentiment_compound IS NULL THEN NULL
                            WHEN sentiment_compound >= {VADER_POS_THRESHOLD} THEN 1.0 ELSE 0.0 END) AS pct_positive,
                   avg(CASE WHEN sentiment_compound IS NULL THEN NULL
                            WHEN sentiment_compound <= {VADER_NEG_THRESHOLD} THEN 1.0 ELSE 0.0 END) AS pct_negative
            FROM base
            GROUP BY category, {key}
        ),
        scored AS (
            SELECT *,
                   avg_rating * log_volume * recency_factor         AS merit_raw,
                   (n_reviews >= {int(min_reviews)})                AS meets_min_reviews
            FROM agg
        )
        SELECT *,
               1.0 - coalesce(pct_positive, 0) - coalesce(pct_negative, 0) AS pct_neutral,
               -- min-max normalisation to 0-100, computed only over qualifying entities
               CASE WHEN NOT meets_min_reviews THEN NULL
                    WHEN max(merit_raw) FILTER (WHERE meets_min_reviews) OVER w
                       = min(merit_raw) FILTER (WHERE meets_min_reviews) OVER w THEN 50.0
                    ELSE 100.0 * (merit_raw - min(merit_raw) FILTER (WHERE meets_min_reviews) OVER w)
                         / (max(merit_raw) FILTER (WHERE meets_min_reviews) OVER w
                            - min(merit_raw) FILTER (WHERE meets_min_reviews) OVER w)
               END AS merit_score,
               CASE WHEN meets_min_reviews
                    THEN rank() OVER (PARTITION BY category, meets_min_reviews ORDER BY merit_raw DESC) END AS merit_rank_in_category,
               CASE WHEN meets_min_reviews
                    THEN percent_rank() OVER (PARTITION BY category, meets_min_reviews ORDER BY merit_raw) END AS merit_percentile
        FROM scored
        WINDOW w AS (PARTITION BY category)
    """)
    n = con.execute(f"SELECT count(*), count(*) FILTER (WHERE meets_min_reviews) FROM {table}").fetchone()
    print(f"[merit_score] {table}: {n[0]:,} entities, {n[1]:,} ranked (>= {min_reviews} reviews)")
