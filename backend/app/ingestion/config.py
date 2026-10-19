"""
config.py  --  Central settings  for: Ground-Truth Merit Engine
==============================================================================
Every tunable number / path lives here so that no other module has magic values.

Data source (from the project doc):
    Amazon Reviews 2023 (McAuley-Lab) -> categories "All_Beauty" and
    "Beauty_and_Personal_Care".
Two kinds of files exist per category (this is important):
    * REVIEW file  (raw_review_<Category>) -> one row per review.
      Columns confirmed from the sample files you shared:
        rating, title, text, images, asin, parent_asin, user_id,
        timestamp (epoch MILLISECONDS), helpful_vote, verified_purchase
      NOTE: there is NO brand/"store" column in the review file.
    * META file    (raw_meta_<Category>)   -> one row per product.
      This is where the brand-like `store` field lives (per the HF dataset card).
      It is joined to reviews through `parent_asin`.
"""
import os
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths (repo layout from the project doc: backend/app/ingestion/  +  data/)
# --------------------------------------------------------------------------- #
# config.py sits at <repo>/backend/app/ingestion/config.py -> repo root = parents[3]
REPO_ROOT = Path(os.getenv("GEO_REPO_ROOT", Path(__file__).resolve().parents[3]))
RAW_DIR = REPO_ROOT / "data" / "raw"                      # streamed / sample jsonl
PROCESSED_DIR = REPO_ROOT / "data" / "processed"          # cleaned parquet + duckdb
CLEAN_DIR = PROCESSED_DIR / "reviews_clean"               # one parquet per category
SENTIMENT_DIR = PROCESSED_DIR / "review_sentiment"        # one parquet per category
EXPORT_DIR = PROCESSED_DIR / "exports"                    # hand-off files for Persons 3/4/5
DB_PATH = PROCESSED_DIR / "merit_engine.duckdb"           # persistent DuckDB file

for _d in (RAW_DIR, PROCESSED_DIR, CLEAN_DIR, SENTIMENT_DIR, EXPORT_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------- #
# Hugging Face dataset + category configs (names taken from the dataset card)
# --------------------------------------------------------------------------- #
HF_REPO = "McAuley-Lab/Amazon-Reviews-2023"
HF_SPLIT = "full"   # the dataset card exposes a single split called "full"

# category label -> Hugging Face config names
CATEGORIES = {
    "All_Beauty": {
        "review_config": "raw_review_All_Beauty",
        "meta_config": "raw_meta_All_Beauty",
    },
    "Beauty_and_Personal_Care": {
        "review_config": "raw_review_Beauty_and_Personal_Care",
        "meta_config": "raw_meta_Beauty_and_Personal_Care",
    },
}

# Columns we keep while streaming (drops the heavy `images` list -> saves disk;
# images are not needed for merit / sentiment).
REVIEW_KEEP_COLS = [
    "rating", "title", "text", "asin", "parent_asin",
    "user_id", "timestamp", "helpful_vote", "verified_purchase",
]
# Metadata columns kept (names per HF dataset card sample record).
META_KEEP_COLS = [
    "parent_asin", "title", "store", "main_category",
    "average_rating", "rating_number",
]

# --------------------------------------------------------------------------- #
# Merit-score parameters  (doc: merit = rating x log(review volume) x recency decay)
# --------------------------------------------------------------------------- #
RECENCY_HALF_LIFE_DAYS = 365   # a review loses half its weight every 365 days (tunable)
MIN_REVIEWS_FOR_RANKING = 5    # entities below this are kept but NOT ranked/normalised
                               # (use 1 when testing on the tiny sample files)
LEADERBOARD_TOP_N = 100        # rows per category in each leaderboard
MOMENTUM_WINDOW_DAYS = 365     # "recent" vs "previous" window for trend momentum

# --------------------------------------------------------------------------- #
# Sentiment (VADER) parameters
# --------------------------------------------------------------------------- #
SENTIMENT_BATCH_SIZE = 50_000                 # rows read from parquet per batch
SENTIMENT_WORKERS = max(1, (os.cpu_count() or 2) - 1)
VADER_POS_THRESHOLD = 0.05   # standard VADER cut-offs: >= 0.05 positive,
VADER_NEG_THRESHOLD = -0.05  #                          <= -0.05 negative

# --------------------------------------------------------------------------- #
# Brand normalisation parameters (RapidFuzz)
# --------------------------------------------------------------------------- #
BRAND_FUZZY_THRESHOLD = 90    # 0-100 similarity needed to merge two brand names
# Values in `store` that really mean "missing"
STORE_MISSING_VALUES = {"", "none", "null", "n/a", "na", "unknown", "nan"}
# Marketing wrappers around a store name. VERIFY against real metadata using
# brand_normalizer.profile_store_values() -- these are generic guesses, not
# something confirmed from your sample files.
STORE_PREFIX_PATTERNS = [r"^visit the\s+", r"^brand:\s*", r"^by\s+"]
STORE_SUFFIX_PATTERNS = [r"\s+store$"]
# Trailing corporate / retail words removed before comparing names
# (so "Anker", "AnkerDirect", "Anker Innovations" collapse together -- doc example)
STORE_SUFFIX_WORDS = {
    "inc", "llc", "ltd", "co", "corp", "corporation", "company",
    "official", "direct", "store", "usa", "us", "international", "innovations",
}
# Suffixes that may be glued to the name with no space ("AnkerDirect")
STORE_GLUED_SUFFIXES = ("direct", "official")
