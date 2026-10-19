# visibility_scores.py : Step 4, how visible is each brand in LLM answers?
import pandas as pd

SAVE = True   # change to True when the printout looks right

IN  = r"data\processed\exports\mentions_matched_p3.parquet"
OUT = r"data\processed\exports\brand_visibility_p3.parquet"

m = pd.read_parquet(IN)

# One key per real brand: merit name if matched, otherwise the LLM name.
# This also merges spellings that were aliased to the same brand.
m["brand_key"] = m["merit_name"].fillna(m["brand_norm"])

# Comparison prompts are head-to-head answers, so they are kept out of visibility.
m["is_cmp"] = (m["query_id"].astype(str).str.startswith("comparison_")
               | m["intent"].astype(str).eq("comparison"))
scope = m[~m["is_cmp"]]

# Denominator: number of responses (prompt x provider) in scope
resp_files = [r"data\processed\geo_gap_responses\all_beauty_groq.jsonl",
              r"data\processed\geo_gap_responses\all_beauty_openrouter.jsonl"]
resp = pd.concat([pd.read_json(f, lines=True) for f in resp_files])
resp_text = resp["response_text"].astype(str)
resp["valid"] = (resp_text.str.len() >= 50) & ~resp_text.str.contains("I should use the search tool")
resp_cmp = resp["query_id"].astype(str).str.startswith("comparison_") | resp["intent"].astype(str).eq("comparison")
N = int((resp["valid"] & ~resp_cmp).sum())
print("responses total:", len(resp), "| valid, non-comparison (N):", N)

# Keep real recommendations only: has a brand, and the brand was not named in the prompt
ment = scope[scope["brand_norm"].notna() & ~scope["in_prompt"].astype(bool)].copy()
ment["rank"] = ment["rank"].astype(float).clip(lower=1)

# One row per brand per response (keep its best rank)
ment = (ment.sort_values("rank")
            .drop_duplicates(["prompt_id", "provider", "brand_key"]))
ment["pos_w"] = 1 / ment["rank"]      # rank 1 = 1.0, rank 2 = 0.5, rank 4 = 0.25 ...

g = ment.groupby("brand_key").agg(
    mentions=("rank", "size"),
    avg_rank=("rank", "mean"),
    pos_sum=("pos_w", "sum"),
    n_providers=("provider", "nunique"),
    n_personas=("persona", "nunique"),
).reset_index()

g["coverage"]        = g["mentions"] / N                # share of responses that mention the brand
g["pos_weighted"]    = g["pos_sum"] / N                 # frequency and early placement combined
g["share_of_voice"]  = g["mentions"] / g["mentions"].sum()
g["visibility_index"] = 100 * g["pos_weighted"] / g["pos_weighted"].max()   # most visible brand = 100

# Attach merit info (one row per brand)
info = (m[["brand_key", "brand_canonical", "match_method", "merit_category",
           "merit_n_reviews", "merit_score", "merit_percentile"]]
        .drop_duplicates("brand_key"))
g = g.merge(info, on="brand_key", how="left")
g["brand"] = g["brand_canonical"].fillna(g["brand_key"])
g = g.drop(columns=["pos_sum"]).sort_values("visibility_index", ascending=False)

# ---------------- Report ----------------
print("responses in scope (N):", N)
print("rows removed: comparison =", int(m["is_cmp"].sum()),
      "| named in prompt =", int((scope["in_prompt"].astype(bool)).sum()),
      "| no brand =", int(scope["brand_norm"].isna().sum()))
print("distinct brands scored:", len(g), "| share of voice sums to", round(g["share_of_voice"].sum(), 3))
print("\n=== TOP 15 MOST VISIBLE ===")
print(g[["brand", "mentions", "avg_rank", "coverage", "visibility_index", "merit_score"]]
      .head(15).round(3).to_string(index=False))
print("\n=== Brands seen in only one response:", int((g["mentions"] == 1).sum()), "of", len(g))

if SAVE:
    g.to_parquet(OUT, index=False)
    print("\nsaved", len(g), "brands to", OUT)
else:
    print("\n(SAVE is False, nothing was saved)")

# ---------------- STEP 6: slices (print only) ----------------
ok = resp[resp["valid"] & ~resp_cmp]                    # valid non-comparison responses
names = g.set_index("brand_key")["brand"]
top_keys = g["brand_key"].head(12)

def slice_table(col):
    n = ok.groupby(col).size()
    c = ment.groupby(["brand_key", col]).size().unstack(fill_value=0)
    cov = c.div(n.reindex(c.columns), axis=1).reindex(top_keys).fillna(0).round(2)
    cov.index = names.reindex(cov.index).values
    print(f"\n=== COVERAGE by {col} (responses per slice: {n.to_dict()}) ===")
    print(cov.to_string())

for col in ["provider", "persona", "intent"]:
    slice_table(col)

# How much do the two providers agree on brand importance?
by_p = {p: ment[ment["provider"] == p].groupby("brand_key")["pos_w"].sum() / n_p
        for p, n_p in ok.groupby("provider").size().items()}
pv = pd.DataFrame(by_p).fillna(0)
print("\nSpearman agreement between providers (position-weighted visibility):",
      round(pv.corr(method="spearman").iloc[0, 1], 3))
print("brands seen by both providers:", int((pv > 0).all(axis=1).sum()), "of", len(pv))