"""
run_pipeline.py  --  Orchestrates the whole Person-1 pipeline, end to end
=========================================================================
Run from the `backend/` folder:

    python -m app.ingestion.run_pipeline --sample                 # tiny sample files
    python -m app.ingestion.run_pipeline --stream --max-rows 200000   # pull from HF, then run
    python -m app.ingestion.run_pipeline --stream                 # FULL categories (huge)

Steps
  1 (optional) stream reviews + metadata from Hugging Face   -> data/raw/
  2 clean reviews with DuckDB -> Parquet                     -> data/processed/reviews_clean/
  3 load metadata (if present) + normalise brands            -> brand_map, product_brand
  4 VADER sentiment per review                               -> data/processed/review_sentiment/
  5 merit score (product [+ brand]), leaderboards, trends    -> DuckDB tables
  6 export hand-off files                                    -> data/processed/exports/
"""
import argparse

from . import config
from .brand_normalizer import normalize_brands
from .duckdb_pipeline import (clean_reviews, find_local_file, get_connection,
                              load_product_dim)
from .leaderboards_and_trends import (build_leaderboards, build_trend_views,
                                      export_handoff_files)
from .merit_score import build_base_views, build_merit_table
from .sentiment_aggregation import score_category


def main() -> None:
    ap = argparse.ArgumentParser(description="Ground-Truth Merit Engine pipeline")
    ap.add_argument("--stream", action="store_true", help="stream categories from Hugging Face first")
    ap.add_argument("--max-rows", type=int, default=None, help="cap streamed review rows per category")
    ap.add_argument("--no-meta", action="store_true", help="skip metadata (=> no brand-level merit)")
    ap.add_argument("--sample", action="store_true",
                    help="tiny-sample mode: MIN_REVIEWS_FOR_RANKING = 1")
    ap.add_argument("--min-reviews", type=int, default=None)
    ap.add_argument("--half-life-days", type=float, default=config.RECENCY_HALF_LIFE_DAYS)
    ap.add_argument("--top-n", type=int, default=config.LEADERBOARD_TOP_N)
    args = ap.parse_args()

    min_reviews = args.min_reviews or (1 if args.sample else config.MIN_REVIEWS_FOR_RANKING)

    if args.stream:                                              # step 1
        from .hf_stream_loader import stream_all
        stream_all(max_rows=args.max_rows, include_meta=not args.no_meta)

    con = get_connection()
    processed = []
    for category in config.CATEGORIES:
        if find_local_file(config.RAW_DIR, category) is None:
            print(f"[run] skipping {category}: no review file in {config.RAW_DIR}")
            continue
        clean_reviews(category)                                  # step 2
        if not args.no_meta and load_product_dim(con, category): # step 3
            normalize_brands(con, category)
        score_category(category)                                 # step 4
        processed.append(category)

    if not processed:
        raise SystemExit("Nothing to process: put review jsonl files in data/raw/ or use --stream")

    build_base_views(con)                                        # step 5
    build_merit_table(con, "product", args.half_life_days, min_reviews)
    if "product_brand" in {r[0] for r in con.execute("SHOW TABLES").fetchall()}:
        build_merit_table(con, "brand", args.half_life_days, min_reviews)
    build_leaderboards(con, args.top_n)
    build_trend_views(con)
    export_handoff_files(con)                                    # step 6
    con.close()
    print("[run] done. Categories processed:", processed)


if __name__ == "__main__":   # guard is REQUIRED (multiprocessing on Windows/macOS)
    main()
