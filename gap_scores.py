# gap_scores.py : Step 5 (version 2)
import re, unicodedata
import duckdb
import pandas as pd
from scipy.stats import spearmanr

SAVE = True
TOP_N = 300                               # brands people actually buy (by review count)
CATEGORY = "Beauty_and_Personal_Care"
GAP_LIMIT = 25                            # beyond +/-25 percentile points = real mismatch
MIN_EVIDENCE = 1000                       # fewer reviews than this = merit score not reliable
EXCLUDE = {"generic", "amazon basics"}    # not real brands; add more here after reading the lists

MERIT = r"data/processed/exports/merit_brand.parquet"
VIS   = r"data\processed\exports\brand_visibility_p3.parquet"
OUT   = r"data\processed\exports\brand_gap_p3.parquet"

def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("\u2011", "-").replace("&", " and ")
    s = s.lower().replace("'", "").replace("\u2019", "")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def pct(s):                                # rank percentile 0-100, lowest = 0, highest = 100
    return (s.rank(method="min") - 1) / (len(s) - 1) * 100

# 1. Merit side
merit = duckdb.sql(f"""
    SELECT brand_canonical, n_reviews, avg_rating, merit_score
    FROM '{MERIT}'
    WHERE category = '{CATEGORY}' AND merit_score IS NOT NULL
""").df()
merit["norm_name"] = merit["brand_canonical"].map(norm)
merit = merit[~merit["norm_name"].isin(EXCLUDE)]
merit = merit.sort_values("n_reviews", ascending=False).drop_duplicates("norm_name")

# 2. Visibility side (Step 4)
vis = pd.read_parquet(VIS)[["brand_key", "mentions", "avg_rank", "coverage", "visibility_index"]]

# 3. Comparison set = top N brands by reviews + every brand the LLMs mentioned
top = merit.head(TOP_N)
seen = merit[merit["norm_name"].isin(vis["brand_key"])]
df = (pd.concat([top, seen]).drop_duplicates("norm_name")
        .merge(vis, left_on="norm_name", right_on="brand_key", how="left")
        .reset_index(drop=True))
for c in ["mentions", "coverage", "visibility_index"]:
    df[c] = df[c].fillna(0)

# 4. Scores
df["merit_pct"] = pct(df["merit_score"])                    # strength within the comparison set
reliable = (df["mentions"] > 0) & (df["n_reviews"] >= MIN_EVIDENCE)
r = df[reliable]
df["gap"] = float("nan")                                    # only for mentioned brands with reliable merit
df.loc[reliable, "gap"] = pct(r["merit_score"]) - pct(r["visibility_index"])   # >0 deserves more visibility

def label(x):
    if x["mentions"] == 0:               return "invisible"
    if x["n_reviews"] < MIN_EVIDENCE:    return "low-evidence"
    if x["gap"] > GAP_LIMIT:             return "under-visible"
    if x["gap"] < -GAP_LIMIT:            return "over-visible"
    return "aligned"
df["label"] = df.apply(label, axis=1)
df = df.rename(columns={"brand_canonical": "brand"}).sort_values("merit_score", ascending=False)

# 5. Report
cols = ["brand", "n_reviews", "merit_score", "mentions", "visibility_index", "gap"]
print("brands in set:", len(df), "| mentioned:", int((df["mentions"] > 0).sum()),
      "| reliable and mentioned:", int(reliable.sum()))
print(df["label"].value_counts().to_dict())
rho, _ = spearmanr(r["merit_score"], r["visibility_index"])
print("\nSpearman merit vs visibility (mentioned brands with >=", MIN_EVIDENCE, "reviews, n =", len(r), "):", round(rho, 3))

print("\n=== INVISIBLE brands with the highest merit ===")
print(df[df["label"] == "invisible"][cols].head(20).round(1).to_string(index=False))
print("\n=== OVER-VISIBLE ===")
print(df[df["label"] == "over-visible"].sort_values("gap")[cols].round(1).to_string(index=False))
print("\n=== UNDER-VISIBLE ===")
print(df[df["label"] == "under-visible"].sort_values("gap", ascending=False)[cols].round(1).to_string(index=False))
print("\n=== ALIGNED ===")
print(df[df["label"] == "aligned"][cols].round(1).to_string(index=False))
print("\n=== LOW-EVIDENCE (mentioned, but Amazon has <", MIN_EVIDENCE, "reviews) ===")
print(df[df["label"] == "low-evidence"].sort_values("mentions", ascending=False)[cols].head(15).round(1).to_string(index=False))

lost = vis[~vis["brand_key"].isin(df["norm_name"])]
print("\nmentioned brands with no merit score:", lost["brand_key"].tolist())

if SAVE:
    df.to_parquet(OUT, index=False)
    print("\nsaved", len(df), "rows to", OUT)
else:
    print("\n(SAVE is False, nothing was saved)")


