import os
import re
import json
import unicodedata

import duckdb
import pandas as pd

# Phase A: Load the final data (run from the project root)
BASE = r"data\processed\geo_gap_responses"


def load_jsonl(name):
    rows = []
    with open(os.path.join(BASE, name), encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return pd.DataFrame(rows)


resp = pd.concat(
    [load_jsonl("all_beauty_groq.jsonl"), load_jsonl("all_beauty_openrouter.jsonl")],
    ignore_index=True,
)  # FIX: removed the duplicate loader that read from the wrong folder

print("Total responses:", len(resp))
print(resp.groupby("provider").size())

# Phase B: Find short or failed responses
print(
    resp.assign(text_len=resp["response_text"].fillna("").astype(str).str.len())
    .sort_values("text_len")[["provider", "prompt_id", "text_len", "response_text"]]
    .head(20)
)

# Phase C: Re-count formats
def response_format(text):
    text = str(text)
    if re.search(r"\|.*\|", text):
        return "table"
    if re.search(r"(?m)^\s*(?:\d+[\.\)]|[-*•])\s+", text):
        return "list"
    if re.search(r"\*\*.+?\*\*", text):
        return "bold"
    return "other"


print(
    resp.assign(format=resp["response_text"].apply(response_format))
    .groupby(["provider", "format"])
    .size()
)

# Phase D: Table parser
def clean_cell(s):
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", str(s))   # markdown links
    s = re.sub(r"<[^>]+>", "", s)                          # html tags
    s = re.sub(r"[*_`]", "", s)                            # bold/italic/code marks
    return s.strip().strip("|").strip()


CRITERIA_HEADERS = {"criteria", "criterion", "aspect", "feature", "factor",
                    "attribute", "metric", "dimension", "comparison"}

def parse_tables(text):
    out = []
    headers, skip = None, False

    for line in str(text).splitlines():
        if "|" not in line:
            headers, skip = None, False
            continue

        cells = [clean_cell(c) for c in line.strip().strip("|").split("|")]

        if all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in cells):
            continue

        if not headers:
            headers = [c.lower() for c in cells]
            skip = headers[0] in CRITERIA_HEADERS
            continue

        if len(cells) != len(headers):
            headers, skip = None, False
            continue
        if skip:
            continue

        brand_idx = next((i for i, h in enumerate(headers) if h == "brand"), None)
        brand = cells[brand_idx] if brand_idx is not None else None

        name = cells[0]
        if re.fullmatch(r"\d+[\.\)]?", name) and len(cells) > 1:   # rank column
            name = cells[1]

        if name and name.lower() not in CRITERIA_HEADERS:
            out.append((name, brand or None))

    return out

# Phase E: List fallback
STOP = re.compile(r"(?i)^\s*#+\s*.*(tips?|notes?|important|how to|routine)")


def parse_list(text):
    out, stop = [], False

    for line in str(text).splitlines():
        if STOP.match(line):
            stop = True
        elif re.match(r"^\s*#+\s", line):
            stop = False

        if stop:
            continue

        m = re.match(r"^\s*(?:\d+[\.\)]|[-*•])\s+(.*)$", line)
        if not m:
            continue

        body = m.group(1)
        b = re.match(r"\*\*(.+?)\*\*", body)
        name = clean_cell(b.group(1) if b else re.split(r"\s[-–:]\s|:", body)[0])

        if name:
            out.append((name, None))

    return out


def extract(text):
    items = parse_tables(text)
    if items:
        return items, "table"

    items = parse_list(text)
    return (items, "list") if items else ([], "none")


resp["method"] = resp["response_text"].apply(lambda x: extract(x)[1])
resp["valid"] = ~(
       resp["response_text"].str.len().lt(50)
       | resp["response_text"].str.contains("I should use the search tool", na=False)
   )
print(resp.groupby(["provider", "method"]).size())
print("Invalid responses:", (~resp["valid"]).sum())

# Phase F: Turn products into brands
def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("\u2011", "-").replace("&", " and ")
    s = s.lower().replace("'", "").replace("\u2019", "")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


mp = r"data/processed/exports/merit_brand.parquet"
merit = duckdb.sql(
    f"SELECT category, brand_canonical, n_reviews, merit_score FROM '{mp}'"
).df()

explicit = {}
for txt in resp["response_text"]:
    for prod, br in parse_tables(txt):
        if br:
            explicit[norm(br)] = br

known = {
    norm(b)
    for b in merit.loc[merit["n_reviews"] >= 100, "brand_canonical"].dropna()
}

print("Explicit brands:", len(explicit))
print("Known brands:", len(known))

ALIAS = {
    "e l f cosmetics": "e l f",
    "nyx professional makeup": "nyx",
    "loreal paris": "loreal",
    "maybelline new york": "maybelline", 
    "ordinary": "the ordinary"
}
EXTRA_BRANDS = {"olaplex", "moroccanoil", "lush", "tatcha", "bioderma","avene", "klairs", "revolution beauty"}
explicit_short = {k for k in explicit if len(k.split()) <= 3}
candidates = known | EXTRA_BRANDS | explicit_short | set(ALIAS)

def resolve(product, brand):
    if brand and len(norm(brand).split()) <= 3:
        b = norm(brand)
        return ALIAS.get(b, b), "explicit"
    toks = norm(brand or product).split()
    for k in range(min(4, len(toks)), 0, -1):
        cand = " ".join(toks[:k])
        if cand in candidates:
            return ALIAS.get(cand, cand), "prefix"
    return None, "unresolved"


for p in [
    "CeraVe Hydrating Facial Cleanser",
    "The Ordinary Niacinamide 10% + Zinc 1%",
    "La Roche‑Posay Anthelios Melt‑in Milk",
    "Burt’s Bees Lip Balm (Original)",
]:
    print(p, "->", resolve(p, None))

# Phase G: Build the mentions table
JUNK = re.compile(r"(?i)(feedback|quality|focus|suitability|price point|best for|assessment|patch test|double-check|verify|check |consult|lack of|no verifiable|recommendation|for skincare|for makeup|for clean|typo|did you mean|you may|there may|since these|without verifiable|not suitable|product range|ingredient|fda|reviews|unclear|potential for|no customer|source|presence|recognition|availability|complexity|friendliness|product type|all-rounder|hydration / glow)")

def looks_like_junk(name):
    n = name.strip()
    return len(n.split()) > 8 or n[-1:] in ".?:!" or bool(JUNK.search(n))

rows, rejected = [], []
for _, r in resp.iterrows():
    if not r["valid"]:
        continue
    items, method = extract(r["response_text"])
    pnorm = " " + norm(r.get("prompt", "")) + " "
    seen, rank = set(), 0
    for prod, br in items:
        b, how = resolve(prod, br)
        # unresolved list items are mostly tips/labels; unresolved table items are kept unless they look like junk
        if how == "unresolved" and (method == "list" or looks_like_junk(prod)):
            rejected.append({"provider": r["provider"], "prompt_id": r["prompt_id"], "raw": prod, "method": method})
            continue
        key = b or norm(prod)
        if key in seen:
            continue
        seen.add(key)
        rank += 1
        rows.append({
            "prompt_id": r.get("prompt_id"), "query_id": r.get("query_id"),
            "provider": r.get("provider"), "model": r.get("model"),
            "persona": r.get("persona"), "intent": r.get("intent"),
            "rank": rank, "raw_product": prod, "raw_brand": br,
            "brand_norm": b, "resolve": how, "extract": method,
            "in_prompt": bool(b) and (" " + b + " ") in pnorm,
        })

mentions = pd.DataFrame(rows)
rejected = pd.DataFrame(rejected)
print("Total mentions:", len(mentions), "| rejected:", len(rejected))
print("Resolution counts:", mentions["resolve"].value_counts().to_dict())
# Phase H: Validate
print(mentions.groupby("provider")["prompt_id"].nunique())

print(
    mentions.groupby(["provider", "prompt_id"])
    .size()
    .groupby("provider")
)

# which parser produced the unresolved items?
print(pd.crosstab(mentions["extract"], mentions["resolve"]))

# the unresolved names
print(mentions.loc[mentions["resolve"] == "unresolved", "raw_product"].value_counts().head(60))

# top resolved brands
print(mentions["brand_norm"].value_counts().head(25))

# the 6 responses with no mentions
for i in resp.index[resp["method"] == "none"]:
    print("-----", i, resp.loc[i, "provider"], resp.loc[i, "query_id"])
    print(str(resp.loc[i, "response_text"])[:500])

#what was rejected (make sure no real brand is in here)
print(rejected["raw"].value_counts().head(40))

#valid responses that still have zero mentions
got = set(zip(mentions["provider"], mentions["prompt_id"]))
zero = resp[resp["valid"] & ~resp.apply(lambda r: (r["provider"], r["prompt_id"]) in got, axis=1)]
print(len(zero), "valid responses with no mentions")
for _, r in zero.iterrows():
    print("-----", r["provider"], r["query_id"], len(r["response_text"]))
    print(str(r["response_text"])[:400])

#mentions that only repeat the prompt, and unresolved leftovers
print("in_prompt:", mentions["in_prompt"].sum())
print(mentions.loc[mentions["resolve"] == "unresolved", "raw_product"].value_counts().head(30))

#look for one Groq response
print(resp[(resp["provider"] == "groq") & (resp["query_id"] == "recommendation_02_general")]["response_text"].iloc[0])

out = r"data\processed\exports"
mentions.to_parquet(out + r"\llm_mentions_p3.parquet", index=False)
(mentions.loc[mentions["resolve"] == "unresolved", "raw_product"]
 .value_counts().rename_axis("raw_product").reset_index(name="count")
 .to_csv(out + r"\unresolved_names_p3.csv", index=False))
rejected.to_csv(out + r"\rejected_p3.csv", index=False)
print("saved", len(mentions), "mentions")