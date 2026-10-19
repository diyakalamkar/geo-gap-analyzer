"""
leaderboards_and_trends.py  --  Category leaderboards + review-recency trend views
==================================================================================
phase for : "Category-level merit leaderboards,
sentiment aggregation from review text, review-recency trend views".

Tables created in DuckDB (and exported as Parquet + CSV for the other modules):
    leaderboard_product          top-N products per category by merit_score
    leaderboard_brand            top-N brands   per category (only if brand data exists)
    trend_category_monthly       reviews / avg rating / avg sentiment per category per month
    trend_entity_quarterly       same per quarter, for the leaderboard products only
    recency_momentum_product     last-N-days vs previous-N-days: volume growth & rating change
"""
import duckdb

from .config import EXPORT_DIR, LEADERBOARD_TOP_N, MOMENTUM_WINDOW_DAYS
from .duckdb_pipeline import _sql_path
from .merit_score import _tables


def build_leaderboards(con: duckdb.DuckDBPyConnection, top_n: int = LEADERBOARD_TOP_N) -> None:
    has_dim = "product_dim" in _tables(con)
    title_col = "d.product_title" if has_dim else "CAST(NULL AS VARCHAR)"
    store_col = "d.store" if has_dim else "CAST(NULL AS VARCHAR)"
    dim_join = ("LEFT JOIN product_dim d ON d.category = m.category AND d.parent_asin = m.parent_asin"
                if has_dim else "")
    con.execute(f"""
        CREATE OR REPLACE TABLE leaderboard_product AS
        SELECT m.category, m.merit_rank_in_category AS rank, m.parent_asin,
               {title_col} AS product_title, {store_col} AS store,
               m.merit_score, m.merit_raw, m.n_reviews, m.avg_rating,
               m.recency_weighted_rating, m.recency_factor, m.avg_sentiment,
               m.pct_positive, m.pct_neutral, m.pct_negative
        FROM merit_product m {dim_join}
        WHERE m.meets_min_reviews AND m.merit_rank_in_category <= {int(top_n)}
        ORDER BY m.category, rank
    """)
    if "merit_brand" in _tables(con):
        con.execute(f"""
            CREATE OR REPLACE TABLE leaderboard_brand AS
            SELECT category, merit_rank_in_category AS rank, brand_canonical, n_products,
                   merit_score, merit_raw, n_reviews, avg_rating, recency_weighted_rating,
                   recency_factor, avg_sentiment, pct_positive, pct_neutral, pct_negative
            FROM merit_brand
            WHERE meets_min_reviews AND merit_rank_in_category <= {int(top_n)}
            ORDER BY category, rank
        """)


def build_trend_views(con: duckdb.DuckDBPyConnection, window_days: int = MOMENTUM_WINDOW_DAYS) -> None:
    # category-level monthly trend
    con.execute("""
        CREATE OR REPLACE TABLE trend_category_monthly AS
        SELECT category, date_trunc('month', review_ts)::DATE AS month,
               count(*) AS n_reviews, avg(rating) AS avg_rating, avg(sentiment_compound) AS avg_sentiment
        FROM reviews_enriched GROUP BY 1, 2 ORDER BY 1, 2
    """)
    # quarterly trend, restricted to leaderboard products (keeps the table small on full data)
    con.execute("""
        CREATE OR REPLACE TABLE trend_entity_quarterly AS
        SELECT e.category, e.parent_asin, date_trunc('quarter', e.review_ts)::DATE AS quarter,
               count(*) AS n_reviews, avg(e.rating) AS avg_rating, avg(e.sentiment_compound) AS avg_sentiment
        FROM reviews_enriched e
        JOIN leaderboard_product l ON l.category = e.category AND l.parent_asin = e.parent_asin
        GROUP BY 1, 2, 3 ORDER BY 1, 2, 3
    """)
    # momentum: recent window vs the window right before it (relative to category reference date)
    con.execute(f"""
        CREATE OR REPLACE TABLE recency_momentum_product AS
        WITH w AS (
            SELECT e.category, e.parent_asin, e.rating, e.sentiment_compound,
                   CASE WHEN e.review_ts >  d.ref_ts - INTERVAL '{int(window_days)} days' THEN 'recent'
                        WHEN e.review_ts >  d.ref_ts - INTERVAL '{2 * int(window_days)} days' THEN 'previous'
                   END AS win
            FROM reviews_enriched e JOIN category_ref_date d USING (category)
        )
        SELECT category, parent_asin,
               count(*) FILTER (WHERE win = 'recent')                   AS n_recent,
               count(*) FILTER (WHERE win = 'previous')                 AS n_previous,
               avg(rating) FILTER (WHERE win = 'recent')                AS rating_recent,
               avg(rating) FILTER (WHERE win = 'previous')              AS rating_previous,
               avg(rating) FILTER (WHERE win = 'recent')
                 - avg(rating) FILTER (WHERE win = 'previous')          AS rating_change,
               avg(sentiment_compound) FILTER (WHERE win = 'recent')    AS sentiment_recent,
               avg(sentiment_compound) FILTER (WHERE win = 'previous')  AS sentiment_previous,
               -- >1 means review volume is growing; NULL when there is no previous-window data
               count(*) FILTER (WHERE win = 'recent')::DOUBLE
                 / nullif(count(*) FILTER (WHERE win = 'previous'), 0)  AS volume_ratio
        FROM w WHERE win IS NOT NULL GROUP BY 1, 2
    """)


EXPORT_TABLES = ["merit_product", "merit_brand", "leaderboard_product", "leaderboard_brand",
                 "trend_category_monthly", "trend_entity_quarterly",
                 "recency_momentum_product", "brand_map", "product_brand", "product_dim"]


def export_handoff_files(con: duckdb.DuckDBPyConnection) -> None:
    """Write every existing output table to data/processed/exports/ as Parquet (+ CSV for small ones)."""
    existing = _tables(con)
    for t in EXPORT_TABLES:
        if t not in existing:
            continue
        con.execute(f"COPY {t} TO '{_sql_path(EXPORT_DIR / (t + '.parquet'))}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        if t.startswith("leaderboard") or t == "trend_category_monthly":
            con.execute(f"COPY {t} TO '{_sql_path(EXPORT_DIR / (t + '.csv'))}' (HEADER, DELIMITER ',')")
        print(f"[export] {t} -> exports/{t}.parquet")
