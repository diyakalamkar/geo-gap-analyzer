# validate_p3.py : Step 7, how trustworthy are the numbers? (prints only, saves nothing)
import numpy as np
import pandas as pd

MENT = r"data\processed\exports\mentions_matched_p3.parquet"
GAP  = r"data\processed\exports\brand_gap_p3.parquet"
RESP = [r"data\processed\geo_gap_responses\all_beauty_groq.jsonl",
        r"data\processed\geo_gap_responses\all_beauty_openrouter.jsonl"]

# ---------- responses in scope (same rule as Step 4) ----------
resp = pd.concat([pd.read_json(f, lines=True) for f in RESP], ignore_index=True)
txt = resp["response_text"].astype(str)
resp["valid"] = (txt.str.len() >= 50) & ~txt.str.contains("I should use the search tool")
cmp_ = resp["query_id"].astype(str).str.startswith("comparison_") | resp["intent"].astype(str).eq("comparison")
ok = resp[resp["valid"] & ~cmp_][["prompt_id", "provider"]].drop_duplicates()
N = len(ok)

m = pd.read_parquet(MENT)
m["brand_key"] = m["merit_name"].fillna(m["brand_norm"])
m["name"] = m["brand_canonical"].fillna(m["brand_norm"])
names = m.drop_duplicates("brand_key").set_index("brand_key")["name"]
is_cmp = m["query_id"].astype(str).str.startswith("comparison_") | m["intent"].astype(str).eq("comparison")
ment = m[~is_cmp & m["brand_norm"].notna() & ~m["in_prompt"].astype(bool)].copy()
ment["rank"] = ment["rank"].astype(float).clip(lower=1)
ment = ment.sort_values("rank").drop_duplicates(["prompt_id", "provider", "brand_key"])
ment["w"] = 1 / ment["rank"]

# response x brand matrix of 1/rank (responses with no brand are all-zero rows)
W = ment.pivot_table(index=["prompt_id", "provider"], columns="brand_key",
                     values="w", aggfunc="sum", fill_value=0)
W = W.reindex(pd.MultiIndex.from_frame(ok), fill_value=0)
arr = W.to_numpy()
print("responses N:", N, "| brands:", arr.shape[1])
print("CHECK weight total (the two numbers must be equal):", round(arr.sum(), 3), round(ment["w"].sum(), 3))

# ---------- 1. Bootstrap: how stable is visibility if we re-draw the 37 responses? ----------
rng = np.random.default_rng(42)
B = 1000
vi = np.empty((B, arr.shape[1]))
for b in range(B):
    s = arr[rng.integers(0, N, N)].sum(axis=0)
    vi[b] = 100 * s / s.max()
vi = pd.DataFrame(vi, columns=W.columns)
full = pd.Series(arr.sum(0), index=W.columns)
top = full.sort_values(ascending=False).head(12).index
winners = vi.idxmax(axis=1)
tbl = pd.DataFrame({
    "visibility_index": (100 * full / full.max())[top],
    "low_5pct": vi[top].quantile(0.05),
    "high_95pct": vi[top].quantile(0.95),
    "pct_times_#1": [(winners == k).mean() * 100 for k in top],
}).round(1)
tbl.index = names.reindex(tbl.index).values
print("\n=== 1. BOOTSTRAP (1000 re-draws of the responses) ===")
print(tbl.to_string())

# ---------- 2. Do gap labels survive different settings? ----------
g = pd.read_parquet(GAP)
vis_ = g[g["mentions"] > 0].copy()

def pct(s):
    return (s.rank(method="min") - 1) / (len(s) - 1) * 100

def labels(min_ev, lim):
    rel = vis_[vis_["n_reviews"] >= min_ev]
    gap = pct(rel["merit_score"]) - pct(rel["visibility_index"])
    out = pd.Series("low-evidence", index=vis_.index, dtype=object)
    out[rel.index] = np.select([gap > lim, gap < -lim], ["under-visible", "over-visible"], "aligned")
    return out

base = labels(1000, 25)
print("\n=== 2. LABEL SENSITIVITY ===")
print("rebuilt baseline equals the saved labels:", round((base == vis_["label"]).mean() * 100), "%")
flagged = base.isin(["under-visible", "over-visible"])
rows = []
for ev in (500, 1000, 2000):
    for lim in (15, 25, 35):
        L = labels(ev, lim)
        rows.append((ev, lim, int((L == "under-visible").sum()), int((L == "over-visible").sum()),
                     round((L[flagged] == base[flagged]).mean() * 100)))
print(pd.DataFrame(rows, columns=["min_reviews", "gap_limit", "n_under", "n_over",
                                  "%_baseline_flags_kept"]).to_string(index=False))

# ---------- 3. Manual spot check of 20 random mentions ----------
CHECK_ROW = 0     # change 0..19 to read the raw response behind another row
sample = m[m["brand_norm"].notna()].sample(20, random_state=1)
print("\n=== 3. SPOT CHECK: does raw_product -> brand_canonical look right? ===")
print(sample[["provider", "prompt_id", "rank", "raw_product", "raw_brand",
              "brand_norm", "brand_canonical", "match_method"]].to_string(index=False))
r0 = sample.iloc[CHECK_ROW]
raw = resp[(resp["prompt_id"] == r0["prompt_id"]) & (resp["provider"] == r0["provider"])]["response_text"].iloc[0]
print(f"\n--- raw response behind row {CHECK_ROW} ({r0['provider']}, {r0['prompt_id']}) ---")
print(raw[:1800])



# ---------------- STEP 8: loose-end check + export ----------------
EXPORT = True     # run once with False, read section 4, then set True
OUT_XLSX = r"data\processed\exports\P3_visibility_gap_results.xlsx"

# (a) brands named in the prompts must never count as organic visibility
T = ["aibrit", "afnan", "angelicmisto", "b o b bars over bottles", "borelth", "feryes", "fantalook",
     "jestilo", "lltgmv", "loanzeg", "lume", "milybest", "oetnaisan", "omelash", "probliva",
     "reboncel", "sekaler", "svvimer", "whalelife", "gruciso"]
tm = m[m["brand_key"].isin(T)].assign(is_comparison=is_cmp)
print("\n=== 4. TARGET BRANDS: where do they appear? ===")
print(tm.groupby(["brand_key", "is_comparison", "in_prompt"]).size().rename("rows").to_string())
organic = tm[~tm["is_comparison"] & ~tm["in_prompt"].astype(bool)]
print("target-brand rows inside the visibility scope (should be 0):", len(organic))

# (b) one Excel workbook with everything a teammate needs
if EXPORT:
    okr = resp[resp["valid"] & ~cmp_]
    n_prov = okr.groupby("provider").size().to_dict()

    def cov_table(col, k=20):
        n = okr.groupby(col).size()
        c = ment.groupby(["brand_key", col]).size().unstack(fill_value=0)
        t = c.div(n.reindex(c.columns), axis=1)
        top_k = full.sort_values(ascending=False).head(k).index
        t = t.reindex(top_k).fillna(0).round(2)
        t.insert(0, "brand", names.reindex(t.index).values)
        return t.reset_index(drop=True)

    sens = pd.DataFrame(
        [(ev, lim,
          int((labels(ev, lim) == "under-visible").sum()),
          int((labels(ev, lim) == "over-visible").sum()),
          round((labels(ev, lim)[flagged] == base[flagged]).mean() * 100))
         for ev in (500, 1000, 2000) for lim in (15, 25, 35)],
        columns=["min_reviews", "gap_limit", "n_under", "n_over", "pct_baseline_flags_kept"])

    gp = g.copy()
    gp["counter_copy_candidate"] = gp["label"].isin(["invisible", "under-visible"])
    gp["evidence_note"] = np.where(gp["mentions"] == 1, "single mention - tentative", "")
    order = {"invisible": 0, "under-visible": 1, "over-visible": 2, "aligned": 3, "low-evidence": 4}
    gp["_o"] = gp["label"].map(order)
    gp = gp.sort_values(["_o", "merit_score"], ascending=[True, False])
    gap_cols = ["brand", "label", "counter_copy_candidate", "evidence_note", "n_reviews", "avg_rating",
                "merit_score", "merit_pct", "mentions", "coverage", "avg_rank", "visibility_index", "gap"]

    vis_full = pd.read_parquet(r"data\processed\exports\brand_visibility_p3.parquet")
    vis_cols = ["brand", "mentions", "avg_rank", "coverage", "pos_weighted", "share_of_voice",
                "visibility_index", "n_providers", "n_personas", "match_method",
                "merit_n_reviews", "merit_score"]

    readme = pd.DataFrame([
        ("Purpose", "Person 3 results of the GEO Visibility Suite: how visible each beauty brand is in LLM answers versus how good it is on Amazon (merit)."),
        ("Scope", f"{N} valid, non-comparison responses ({n_prov}). Comparison prompts and brands named inside the prompt are excluded. One count per brand per response (best rank)."),
        ("Merit", "Amazon Reviews 2023 (Beauty_and_Personal_Care): average rating x log(1 + review count) x recency, scaled 0-100. Depends on review volume, so brands with few Amazon reviews score very low."),
        ("visibility_index", "100 x position-weighted mentions / the top brand's value. Position weight = 1/rank. CeraVe = 100."),
        ("coverage", "Share of the in-scope responses that mention the brand."),
        ("gap", "Only for mentioned brands with >= 1000 reviews: merit percentile minus visibility percentile, both ranked among those brands. Positive = deserves more visibility."),
        ("label", "invisible = never mentioned; low-evidence = mentioned but < 1000 Amazon reviews (merit unreliable); under-visible gap > +25; over-visible gap < -25; aligned otherwise."),
        ("Settings", "Comparison set = top 300 brands by review count + all mentioned brands (333). MIN_EVIDENCE = 1000 reviews. GAP_LIMIT = 25 percentile points."),
        ("counter_copy_candidate", "True for invisible and under-visible brands. Needs a human relevance check: the invisible set includes non-skincare/makeup brands (wigs, nails, bags) that the prompts rarely ask about."),
        ("Sheets", "brand_gap (333 brands), brand_visibility (all mentioned brands), coverage_provider / coverage_persona / coverage_intent (top 20 brands), bootstrap (stability of top 12), sensitivity (label stability)."),
        ("Limitation 1", f"Only {N} responses: one response is worth about {100/N:.1f} coverage points; many brands appear once. Only the top brands are stable."),
        ("Limitation 2", "OpenRouter responses come from a router that mixes unidentified models."),
        ("Limitation 3", "Merit measures Amazon popularity-weighted quality; prestige and dermatology brands (La Roche-Posay, Tatcha, EltaMD) have too few Amazon reviews and are labelled low-evidence."),
        ("Limitation 4", "Persona and query type are tied to the prompt wording, so slice differences are descriptive, not causal."),
        ("Limitation 5", "Olaplex, Bioderma and Klairs are mentioned by LLMs but have no merit score in the Amazon data."),
    ], columns=["item", "description"])

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xw:
        readme.to_excel(xw, sheet_name="README", index=False)
        gp[gap_cols].round(2).to_excel(xw, sheet_name="brand_gap", index=False)
        vis_full[vis_cols].round(3).to_excel(xw, sheet_name="brand_visibility", index=False)
        cov_table("provider").to_excel(xw, sheet_name="coverage_provider", index=False)
        cov_table("persona").to_excel(xw, sheet_name="coverage_persona", index=False)
        cov_table("intent").to_excel(xw, sheet_name="coverage_intent", index=False)
        tbl.reset_index().rename(columns={"index": "brand"}).to_excel(xw, sheet_name="bootstrap", index=False)
        sens.to_excel(xw, sheet_name="sensitivity", index=False)
        xw.sheets["README"].column_dimensions["A"].width = 26
        xw.sheets["README"].column_dimensions["B"].width = 130
    print("\nsaved", OUT_XLSX)
