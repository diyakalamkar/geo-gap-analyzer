"""
hf_stream_loader.py  --  Streamed category pulls from Hugging Face
==================================================================
Doc requirement: "Stream 2-3 categories from HF" using `datasets` with
streaming=True, filtered by category config (e.g. raw_review_All_Beauty) so the
full 10B+ row dataset is never loaded into memory / disk.

Writes newline-delimited JSON into data/raw/ :
    data/raw/<Category>.jsonl         (reviews)
    data/raw/meta_<Category>.jsonl    (item metadata -> brand `store` field)
"""
import json
from pathlib import Path
from typing import Optional

from tqdm import tqdm

from .config import (CATEGORIES, HF_REPO, HF_SPLIT, META_KEEP_COLS, RAW_DIR,
                     REVIEW_KEEP_COLS)


def stream_category(category: str, kind: str = "review",
                    max_rows: Optional[int] = None,
                    out_dir: Path = RAW_DIR) -> Path:
    """
    Stream one category ("review" or "meta") from Hugging Face to a local jsonl.

    max_rows=None -> whole category (Beauty_and_Personal_Care has ~23.9M reviews:
                     expect a very large file + long download).
    max_rows=N    -> first N rows only. NOTE: this is the head of the file, not a
                     random sample, so it can be biased; use only for dev runs.
    """
    from datasets import load_dataset  # imported here so other modules work without it

    if category not in CATEGORIES:
        raise ValueError(f"Unknown category {category!r}; choose from {list(CATEGORIES)}")
    if kind not in ("review", "meta"):
        raise ValueError("kind must be 'review' or 'meta'")

    config_name = CATEGORIES[category][f"{kind}_config"]
    keep_cols = REVIEW_KEEP_COLS if kind == "review" else META_KEEP_COLS
    out_path = out_dir / (f"{category}.jsonl" if kind == "review" else f"meta_{category}.jsonl")
    tmp_path = out_path.with_suffix(".jsonl.part")   # write to .part then rename (no half files)

    # streaming=True -> rows are fetched lazily, nothing is fully downloaded
    stream = load_dataset(HF_REPO, config_name, split=HF_SPLIT, streaming=True)

    written = 0
    with open(tmp_path, "w", encoding="utf-8") as fh:
        for i, row in enumerate(tqdm(stream, desc=f"{config_name}", unit="rows")):
            if max_rows is not None and i >= max_rows:
                break
            record = {c: row.get(c) for c in keep_cols}   # keep only needed columns
            if record.get("parent_asin") is None:          # cannot be joined/aggregated
                continue
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1
    tmp_path.replace(out_path)
    print(f"[hf_stream_loader] {config_name}: wrote {written:,} rows -> {out_path}")
    return out_path


def stream_all(max_rows: Optional[int] = None, include_meta: bool = True) -> None:
    """Stream reviews (and optionally metadata) for every configured category."""
    for category in CATEGORIES:
        stream_category(category, "review", max_rows)
        if include_meta:
            # metadata is ~1 row per product, so it is not capped by max_rows
            stream_category(category, "meta", None)


if __name__ == "__main__":
    stream_all(max_rows=100_000)   # dev-sized default; pass None for the full pull
