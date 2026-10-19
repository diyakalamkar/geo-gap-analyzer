# match_ground_truth.py : Step 3, link each LLM brand to the merit table
import re, unicodedata
import duckdb
import pandas as pd
from rapidfuzz import process, fuzz

SAVE = True    # first runs: review only. Change to True when the checks look good.

MENTIONS = r"data\processed\exports\llm_mentions_p3.parquet"
MERIT    = r"data/processed/exports/merit_brand.parquet"
OUT      = r"data\processed\exports\mentions_matched_p3.parquet"

# Same normalising function as in mention_extractor.py (do not change it)
def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("\u2011", "-").replace("&", " and ")
    s = s.lower().replace("'", "").replace("\u2019", "")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

# Manual links:  "LLM brand (normalised)": "merit name (normalised)"
# Fill this in after reading the UNMATCHED list below. Example (check the real merit name first):
#   "loreal": "loreal paris",
ALIAS = {
    "loreal": "loreal paris",
    "nyx": "nyx professional makeup",
    "aquaphor healing ointment": "aquaphor",
    "dior beauty": "dior",
    "inkey list": "the inkey list",
    "okeeffes hand cream": "okeeffes",
}

# ---------------- 1. Load ----------------
mentions = pd.read_parquet(MENTIONS)
merit = duckdb.sql(f"""
    SELECT category, brand_canonical, n_reviews, avg_rating, merit_score,
           merit_rank_in_category, merit_percentile
    FROM '{MERIT}'
""").df()
merit["norm_name"] = merit["brand_canonical"].map(norm)

# If a brand appears in both categories, keep the version with more reviews
merit = merit.sort_values("n_reviews", ascending=False).drop_duplicates(["norm_name", "category"])
cats = merit.groupby("norm_name")["category"].apply(lambda s: ",".join(sorted(s))).rename("categories_found")
primary = merit.drop_duplicates("norm_name").merge(cats, left_on="norm_name", right_index=True)
known = set(primary["norm_name"])

# ---------------- 2. Match each distinct LLM brand ----------------
brands = sorted(mentions["brand_norm"].dropna().unique())
rows = []
for b in brands:
    if b in ALIAS and ALIAS[b] in known:
        rows.append((b, ALIAS[b], "alias"))
    elif b in known:
        rows.append((b, b, "exact"))
    else:
        rows.append((b, None, "unmatched"))
bm = pd.DataFrame(rows, columns=["brand_norm", "merit_name", "match_method"])

bad = [k for k, v in ALIAS.items() if v not in known]
if bad:
    print("WARNING: these ALIAS targets are not in merit:", bad)

cols = ["norm_name", "brand_canonical", "category", "n_reviews", "avg_rating",
        "merit_score", "merit_rank_in_category", "merit_percentile", "categories_found"]
bm = bm.merge(
    primary[cols].rename(columns={"norm_name": "merit_name", "category": "merit_category",
                                  "n_reviews": "merit_n_reviews", "avg_rating": "merit_avg_rating"}),
    on="merit_name", how="left")

# ---------------- 3. Attach to every mention ----------------
out = mentions.merge(bm, on="brand_norm", how="left")
assert len(out) == len(mentions), "join created duplicate rows"

# ---------------- 4. Report ----------------
valid = out[out["brand_norm"].notna()]
matched = bm["match_method"] != "unmatched"
print("\n=== SUMMARY ===")
print("distinct LLM brands:", len(bm), "| matched:", int(matched.sum()), "| unmatched:", int((~matched).sum()))
print(bm["match_method"].value_counts().to_dict())
print("mentions with a brand:", len(valid), "| share matched:", round((valid["match_method"] != "unmatched").mean(), 3))
print("matched but no merit score (under 5 reviews):", int((matched & bm["merit_score"].isna()).sum()))

TARGETS = ["AIBRIT", "Afnan", "AngelicMisto", "B.O.B BARS OVER BOTTLES", "BORELTH", "FERYES", "FantaLook",
           "Jestilo", "LLTGMV", "Loanzeg", "Lume", "MilyBest", "OETNAISAN", "OMELASH", "ProBliva",
           "Reboncel", "Sekaler", "Svvimer", "WhaleLife", "gruciso"]
print("\n=== CHECK: prompt brands missing from merit (should be []) ===")
print([t for t in TARGETS if norm(t) not in known])

print("\n=== CHECK: top 20 brands and what they matched to ===")
top = valid["brand_norm"].value_counts().head(20).index
print(bm[bm["brand_norm"].isin(top)][["brand_norm", "brand_canonical", "merit_category",
                                      "merit_n_reviews", "merit_score", "match_method"]].to_string(index=False))

print("\n=== UNMATCHED brands (most mentioned first) ===")
cnt = valid["brand_norm"].value_counts()
un = bm[~matched].assign(n_mentions=lambda d: d["brand_norm"].map(cnt)).sort_values("n_mentions", ascending=False)
print(un[["brand_norm", "n_mentions"]].to_string(index=False))

print("\n=== SUGGESTIONS for unmatched (review only, never accept blindly) ===")
choices = primary["norm_name"].tolist()
for b in un["brand_norm"]:
    hits = process.extract(b, choices, scorer=fuzz.ratio, limit=3, score_cutoff=85)
    if hits:
        print(b, "->", [(h[0], round(h[1])) for h in hits])

# ---------------- LOOKUP: spelling variants in merit (review only) ----------------
LOOKUP = ["oreal", "nyx", "roche", "olaplex", "aquaphor", "dior", "inkey", "keeffe", "bioderma"]
for t in LOOKUP:
    hit = primary[primary["norm_name"].str.contains(t, na=False)]
    print("\n---", t, "---")
    print("LOOKUP PART!!!")
    print(hit.sort_values("n_reviews", ascending=False)
             [["norm_name", "brand_canonical", "category", "n_reviews", "merit_score"]]
             .head(8).to_string(index=False))


# ---------------- 5. Save (one file) ----------------
if SAVE:
    out.to_parquet(OUT, index=True)
    print("\nsaved", len(out), "rows to", OUT)
else:
    print("\n(SAVE is False, nothing was saved)")