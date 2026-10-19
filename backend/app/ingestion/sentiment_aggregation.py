"""
sentiment_aggregation.py  --  VADER sentiment on real Amazon reviews
====================================================================
Doc requirement: "sentiment aggregation from real reviews" using VADER
(rule-based, CPU-only, no model weights).

Step A (score_category): score each review's `full_text` -> compound in [-1, 1]
        and write data/processed/review_sentiment/<category>.parquet
        (review_id, sentiment_compound).  Reviews with empty text get NULL.
Step B (aggregation) happens in merit_score.py, where these scores are averaged
        per product / brand together with the rating statistics.

Note: this file is named sentiment_aggregation.py (not review_sentiment.py) on
purpose -- the doc's folder tree gives nlp/review_sentiment.py to Person 3
(Krisha), who tags sentiment on LLM responses; this one is for Amazon reviews.
"""
from multiprocessing import Pool
from typing import List, Optional

import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm

from .config import (CLEAN_DIR, SENTIMENT_BATCH_SIZE, SENTIMENT_DIR,
                     SENTIMENT_WORKERS)

_analyzer = None   # one analyzer per worker process


def _init_worker() -> None:
    global _analyzer
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _analyzer = SentimentIntensityAnalyzer()


def _score_texts(texts: List[Optional[str]]) -> List[Optional[float]]:
    """VADER compound score per text; None for missing/blank text."""
    out = []
    for t in texts:
        out.append(_analyzer.polarity_scores(t)["compound"] if t and t.strip() else None)
    return out


def score_category(category: str) -> None:
    """Score all cleaned reviews of one category, streaming batch by batch."""
    src = CLEAN_DIR / f"{category}.parquet"
    dst = SENTIMENT_DIR / f"{category}.parquet"
    if not src.exists():
        raise FileNotFoundError(f"Run duckdb_pipeline.clean_reviews('{category}') first")

    schema = pa.schema([("review_id", pa.string()), ("sentiment_compound", pa.float64())])
    pf = pq.ParquetFile(src)
    total = pf.metadata.num_rows
    pool = Pool(SENTIMENT_WORKERS, initializer=_init_worker) if SENTIMENT_WORKERS > 1 else None
    if pool is None:
        _init_worker()

    with pq.ParquetWriter(dst, schema, compression="zstd") as writer, \
            tqdm(total=total, desc=f"VADER {category}", unit="rev") as bar:
        # only the two needed columns are read -> low memory
        for batch in pf.iter_batches(batch_size=SENTIMENT_BATCH_SIZE,
                                     columns=["review_id", "full_text"]):
            ids = batch.column("review_id").to_pylist()
            texts = batch.column("full_text").to_pylist()
            if pool is not None:      # split the batch into chunks for parallel workers
                step = max(1, len(texts) // (SENTIMENT_WORKERS * 4))
                chunks = [texts[i:i + step] for i in range(0, len(texts), step)]
                scores = [s for part in pool.map(_score_texts, chunks) for s in part]
            else:
                scores = _score_texts(texts)
            writer.write_table(pa.table({"review_id": ids, "sentiment_compound": scores}, schema=schema))
            bar.update(len(ids))
    if pool is not None:
        pool.close()
        pool.join()
    print(f"[sentiment] {category}: sentiment scores -> {dst.name}")
