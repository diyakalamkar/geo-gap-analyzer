
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ---------- Configuration ----------

st.set_page_config(
    page_title="GEO Visibility Suite",
    page_icon="🔎",
    layout="wide",
)

ROOT = Path(__file__).resolve().parent
EXPORTS = ROOT / "data" / "processed" / "exports"
WORKBOOK = EXPORTS / "P3_visibility_gap_results.xlsx"

st.title("GEO Visibility Suite")
st.caption(
    "Tracking beauty brand visibility in open-source LLM responses"
)


# ---------- Load validated data ----------

@st.cache_data
def load_data(path):
    gap = pd.read_excel(path, sheet_name="brand_gap")
    visibility = pd.read_excel(path, sheet_name="brand_visibility")
    provider = pd.read_excel(path, sheet_name="coverage_provider")
    persona = pd.read_excel(path, sheet_name="coverage_persona")
    intent = pd.read_excel(path, sheet_name="coverage_intent")
    bootstrap = pd.read_excel(path, sheet_name="bootstrap")
    sensitivity = pd.read_excel(path, sheet_name="sensitivity")

    return gap, visibility, provider, persona, intent, bootstrap, sensitivity


if not WORKBOOK.exists():
    st.error(
        f"Workbook not found: {WORKBOOK}\n\n"
        "Complete the Person 3 validation and Excel export first."
    )
    st.stop()

try:
    (
        gap,
        visibility,
        provider,
        persona,
        intent,
        bootstrap,
        sensitivity,
    ) = load_data(WORKBOOK)
except Exception as exc:
    st.error(f"Could not load the workbook: {exc}")
    st.stop()


# ---------- Navigation ----------

page = st.sidebar.radio(
    "Navigate",
    [
        "Overview",
        "Brand Visibility",
        "Merit vs Visibility",
        "Persona & Provider",
        "Validation",
    ],
)

st.sidebar.divider()
st.sidebar.caption("Analysis sample: 37 valid responses")
st.sidebar.caption("Sources: Groq + OpenRouter")
st.sidebar.caption("Local analysis — no deployment")


# ---------- Overview ----------

if page == "Overview":
    total = len(gap)
    mentioned = int((gap["mentions"].fillna(0) > 0).sum())
    invisible = int((gap["label"] == "invisible").sum())
    under = int((gap["label"] == "under-visible").sum())
    over = int((gap["label"] == "over-visible").sum())

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Brands compared", total)
    c2.metric("Brands mentioned", mentioned)
    c3.metric("Invisible", invisible)
    c4.metric("Under-visible", under)
    c5.metric("Over-visible", over)

    st.subheader("Brand gap distribution")

    counts = (
        gap["label"]
        .fillna("unclassified")
        .value_counts()
        .rename_axis("Category")
        .reset_index(name="Brands")
    )

    fig = px.bar(
        counts,
        x="Category",
        y="Brands",
        color="Category",
        text="Brands",
        title="How LLM visibility compares with Amazon-based merit",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Most visible beauty brands")

    top = visibility.sort_values(
        "visibility_index", ascending=False
    ).head(10)

    fig = px.bar(
        top.sort_values("visibility_index"),
        x="visibility_index",
        y="brand",
        orientation="h",
        text="visibility_index",
        hover_data=["mentions", "avg_rank", "coverage"],
        title="Top 10 brands by visibility index",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.info(
        "Visibility is measured from 37 valid non-comparison responses. "
        "The scores describe this sample, not every LLM or every beauty query."
    )


# ---------- Brand Visibility ----------

elif page == "Brand Visibility":
    st.subheader("Brand Visibility Explorer")

    search = st.text_input("Search brand name")
    minimum_mentions = st.slider(
        "Minimum number of mentions", 0, 37, 1
    )

    filtered = visibility[
        visibility["mentions"].fillna(0) >= minimum_mentions
    ].copy()

    if search:
        filtered = filtered[
            filtered["brand"].str.contains(
                search, case=False, na=False
            )
        ]

    columns = [
        col for col in [
            "brand", "mentions", "avg_rank", "coverage",
            "pos_weighted", "share_of_voice", "visibility_index",
            "merit_score", "match_method",
        ]
        if col in filtered.columns
    ]

    st.dataframe(
        filtered[columns].sort_values(
            "visibility_index", ascending=False
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download filtered brands (CSV)",
        filtered[columns].to_csv(index=False).encode("utf-8"),
        file_name="filtered_brand_visibility.csv",
        mime="text/csv",
    )


# ---------- Merit vs Visibility ----------

elif page == "Merit vs Visibility":
    st.subheader("Merit vs Visibility Gap")

    st.caption(
        "Positive gap means merit percentile exceeds visibility percentile. "
        "Negative gap means visibility exceeds merit."
    )

    labels = sorted(gap["label"].dropna().unique().tolist())
    selected = st.multiselect(
        "Filter by gap label",
        labels,
        default=labels,
    )
    minimum_reviews = st.number_input(
        "Minimum Amazon reviews",
        min_value=0,
        value=1000,
        step=500,
    )

    filtered = gap[
        gap["label"].isin(selected)
        & (gap["n_reviews"].fillna(0) >= minimum_reviews)
    ].copy()

    mentioned = filtered[
        (filtered["mentions"].fillna(0) > 0)
        & filtered["visibility_index"].notna()
        & filtered["merit_score"].notna()
    ]

    if not mentioned.empty:
        fig = px.scatter(
            mentioned,
            x="merit_score",
            y="visibility_index",
            color="label",
            size="mentions",
            hover_name="brand",
            hover_data=["n_reviews", "avg_rank", "gap"],
            title="Amazon-based merit vs LLM visibility",
            labels={
                "merit_score": "Amazon merit score (0–100)",
                "visibility_index": "Visibility index (0–100)",
            },
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No mentioned brands match these filters.")

    st.subheader("Potential counter-copy research candidates")

    candidates = filtered[
        filtered["label"].isin(["invisible", "under-visible"])
        & (filtered["n_reviews"].fillna(0) >= 1000)
    ].copy()

    if "counter_copy_candidate" in candidates.columns:
        candidates = candidates[
            candidates["counter_copy_candidate"].fillna(False).astype(bool)
        ]

    st.warning(
        "These are research candidates, not automatic content "
        "recommendations. Check product-category relevance before selecting "
        "a brand; the merit table also includes beauty-adjacent categories."
    )

    candidate_columns = [
        col for col in [
            "brand", "label", "merit_score", "n_reviews",
            "visibility_index", "gap", "mentions",
            "counter_copy_candidate", "evidence_note",
        ]
        if col in candidates.columns
    ]

    st.dataframe(
        candidates[candidate_columns].sort_values(
            "merit_score", ascending=False
        ),
        use_container_width=True,
        hide_index=True,
    )


# ---------- Persona & Provider ----------

elif page == "Persona & Provider":
    st.subheader("Coverage by Provider")

    st.caption(
        "Coverage represents the fraction of valid responses in which "
        "a brand appears. The underlying slice denominators can differ."
    )

    for title, frame in [
        ("Provider", provider),
        ("Persona", persona),
        ("Query type", intent),
    ]:
        st.markdown(f"**{title}**")
        st.dataframe(frame, use_container_width=True, hide_index=True)


# ---------- Validation ----------

elif page == "Validation":
    st.subheader("Robustness and Validation")

    st.markdown("**Bootstrap results**")
    st.dataframe(bootstrap, use_container_width=True, hide_index=True)

    st.markdown("**Sensitivity analysis**")
    st.dataframe(sensitivity, use_container_width=True, hide_index=True)

    st.caption(
        "The bootstrap resamples responses, not individual brand mentions. "
        "Interpret second-tier rankings and low-frequency brands cautiously."
    )

st.divider()
st.caption(
    "GEO Visibility Suite | Preliminary findings | "
    "Amazon merit is a proxy, not a complete measure of brand quality."
)
