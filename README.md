# GEO-Gap Analyzer — Tracking Beauty Brand Visibility in LLM Responses

**Analyzing the gap between brand merit and generative AI visibility.**

GEO-Gap Analyzer is a research-oriented analytics platform that evaluates how large language models (LLMs) recommend beauty brands and products, and whether those recommendations align with an Amazon-based measure of brand merit.

The project combines large-scale e-commerce review analysis, sentiment analysis, brand normalization, merit scoring, multi-provider LLM probing, mention extraction, and visibility-gap analysis in an interactive React dashboard.

Rather than measuring only how highly rated a brand is, the project investigates whether that brand is actually surfaced when consumers ask LLMs for beauty recommendations.

---

## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Objectives](#objectives)
- [Dataset](#dataset)
- [System Architecture](#system-architecture)
- [Methodology](#methodology)
- [Dashboard Features](#dashboard-features)
- [Key Findings](#key-findings)
- [Installation and Setup](#installation-and-setup)
- [Running the Application](#running-the-application)
- [Environment Variables](#environment-variables)
- [Data Outputs](#data-outputs)
- [Validation and Testing](#validation-and-testing)
- [Acknowledgements](#acknowledgements)

---

## Overview

Consumers increasingly use generative AI tools to discover products, compare brands, and obtain personalized recommendations. However, a brand's product quality, customer satisfaction, or market presence does not guarantee that an LLM will recommend it.

GEO-Gap Analyzer studies this difference through **Generative Engine Optimization (GEO)**, focusing on brand visibility in LLM-generated answers.

The system establishes an Amazon-based merit benchmark, generates controlled prompts, collects responses from multiple LLM providers, extracts and matches brand mentions, and compares observed visibility against the benchmark.

The project includes an interactive dashboard for examining brand-level visibility, provider differences, category trends, and GEO-Gap classifications.

The implementation is designed as a local research and analytics pipeline. Deployment and a production-hosted dashboard are outside the current project scope.

## Problem Statement

Traditional product evaluation relies on indicators such as customer ratings, review volume, and recency. These indicators provide useful evidence about product and brand performance, but they do not explain whether generative AI systems make those brands visible to potential customers.

A brand with strong customer feedback may receive little or no representation in LLM-generated recommendations. Conversely, a frequently recommended brand may not rank as highly under the project's merit calculation.

The problem addressed by GEO-Gap Analyzer is:

> How can we quantify the visibility of beauty brands in LLM-generated responses, compare that visibility with an Amazon-based merit benchmark, and identify brands that are underrepresented or disproportionately represented?

The project approaches this problem using structured prompts, multi-provider response collection, brand matching, normalized visibility metrics, and an interactive analytical dashboard.

## Objectives

- Build an Amazon-based product and brand merit benchmark.
- Process large beauty review datasets efficiently.
- Normalize brand names to improve consistency across datasets.
- Calculate sentiment, merit scores, rankings, and trend indicators.
- Generate controlled prompts representing different consumer personas and query intents.
- Collect responses from multiple LLM providers.
- Extract brand and product mentions from generated answers.
- Match extracted mentions against the benchmark without relying solely on unsafe substring matches.
- Quantify brand visibility and compare it with merit.
- Identify invisible, under-visible, aligned, over-visible, and low-evidence brands.
- Explore differences between providers, personas, and query types through a React dashboard.

---

## Dataset

### Source

The primary data source is the [Amazon Reviews 2023 dataset](https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023), published by McAuley Lab.

The project uses two beauty-related categories:

| Dataset category | Original reviews | Clean reviews |
|---|---:|---:|
| All_Beauty | 701,528 | 694,252 |
| Beauty_and_Personal_Care | 23,911,390 | 23,668,864 |
| **Total** | **24,612,918** | **24,363,116** |

These are the review counts supplied by the project processing pipeline.

### Review data

The review records contain fields such as:

- `asin` — product identifier.
- `parent_asin` — parent product identifier.
- `rating` — customer rating.
- `text` — review text.
- `title` — review title.
- `timestamp` — review timestamp.
- `helpful_vote` — helpfulness votes.
- `verified_purchase` — purchase verification indicator.
- `user_id` — reviewer identifier.
- `images` — associated image information.

### Product metadata

The metadata includes:

- `parent_asin`
- `title`
- `store`
- `main_category`
- `average_rating`
- `rating_number`

This metadata connects products to their descriptive information and provides the basis for identifying brands and calculating benchmark metrics.

### Data processing

The review datasets are large, so the processing pipeline uses DuckDB with memory-conscious settings rather than loading all review records into memory simultaneously.

The cleaning stage removes unsuitable records and prepares the data for downstream analysis. The project then constructs product and brand mappings from normalized store and brand names.

Processed product counts:

| Category | Products |
|---|---:|
| All_Beauty | 112,590 |
| Beauty_and_Personal_Care | 1,028,914 |

### Brand normalization

Brand names are not always represented consistently across product metadata and LLM answers. Differences can include capitalization, punctuation, spelling, and alternate brand names.

The normalization pipeline uses text-processing rules and RapidFuzz similarity matching, with a configured threshold of 90 for the relevant matching stage.

The resulting `brand_map` and `product_brand` mappings help standardize brand identities across the pipeline.

### Sentiment analysis

The project uses VADER sentiment analysis to derive sentiment scores from review text.

| Category | Reviews processed | Average sentiment |
|---|---:|---:|
| All_Beauty | 694,252 | 0.5174 |
| Beauty_and_Personal_Care | 23,668,864 | 0.5483 |

No null sentiment values were reported in these processed datasets.

Sentiment is one component of the analysis; it is not treated as a direct measurement of LLM visibility.

---

## System Architecture

The system follows a sequential data-processing and analysis pipeline.

```text
Amazon Reviews + Product Metadata
                |
                v
       Data Cleaning (DuckDB)
                |
                v
       Brand Normalization
                |
                v
        VADER Sentiment
                |
                v
       Merit Score Calculation
                |
                v
       Product / Brand Rankings
                |
                v
       Controlled Prompt Engine
                |
                v
       LLM Provider Integrations
          /             \
       Groq           OpenRouter
          \             /
                v
       Response Collection
                |
                v
     Brand / Product Extraction
                |
                v
       Ground-Truth Matching
                |
                v
       Visibility Score Calculation
                |
                v
       GEO-Gap Classification
                |
                v
       Interactive React Dashboard
```

The data-processing pipeline and the dashboard serve different purposes. The backend generates and validates analytical outputs; the frontend presents those outputs for exploration.

---

## Methodology

### 1. Merit and ground-truth generation

The project calculates product and brand merit using the following conceptual formula:

**Merit score = Average rating × log(1 + review volume) × recency factor**

The recency factor uses half-life weighting:

```text
recency_factor = 0.5 ^ (review_age_days / RECENCY_HALF_LIFE_DAYS)
```

This formulation combines customer ratings, review volume, and recency.

Entities with at least five reviews are eligible for ranking. Eligible scores are normalized to a 0–100 scale.

Reported benchmark outputs include:

| Metric | Result |
|---|---:|
| Product entities | 1,141,296 |
| Ranked product entities | 416,927 |
| Brand entities | 147,299 |
| Ranked brand entities | 86,216 |

The benchmark is used as a reference for evaluating observed LLM visibility. It should not be interpreted as a complete or universal measure of brand quality.

### 2. Prompt generation

The prompt engine generates controlled questions for the beauty domain. It incorporates user personas, query intent, and prompt metadata to support structured comparisons.

The four personas used in the Person 3 analysis are:

- General
- Budget-conscious
- Beginner
- Sensitive-skin

The six query types are:

- Discovery
- Recommendation
- Recommendation variation
- Problem-based queries
- Comparison
- Brand discovery

The initial prompt-generation test loaded 20 brands and generated 40 unique prompts.

Each prompt can include identifiers and metadata such as `prompt_id`, `query_id`, `base_query_id`, `persona`, `category`, and the prompt text itself.

### 3. LLM response collection

The system integrates with Groq and OpenRouter to collect generated answers.

Provider integrations include error handling, timeout management, retry logic for temporary errors, and rate-limit handling. The orchestration layer uses Celery and Redis to coordinate background tasks and scheduled batches.

Responses are stored in JSONL format with metadata that connects each answer to its originating prompt and provider.

This traceability makes it possible to audit the input prompts, compare provider outputs, and reproduce downstream analysis from saved responses.

**Important:** Running the collection scripts may make live API calls. Existing response files should be reused when only the analysis or dashboard needs to be tested.

### 4. Mention extraction

The extraction stage identifies beauty brand and product mentions in LLM-generated text.

Depending on the response format, the pipeline can parse Markdown tables, numbered lists, or bullet lists. Extracted entries are normalized and assigned positions based on their order in the response.

Each brand is counted at most once per response for visibility calculations, using its best observed rank.

The extraction process also records prompt-related information so brands explicitly named by a prompt can be distinguished from brands recommended in the generated answer.

### 5. Ground-truth matching

Extracted brand mentions are matched against the normalized benchmark.

The matching workflow uses exact normalized matches, configured aliases, and manual review of fuzzy-match suggestions. Fuzzy similarity is not accepted automatically because unsafe matches can incorrectly associate one brand with another.

The output retains matching information for auditability and downstream scoring.

### 6. Visibility scoring

Visibility measures how frequently and how prominently brands appear in LLM-generated answers.

The core measures include:

- **Mentions:** Number of valid responses containing the brand.
- **Coverage:** Number of responses mentioning the brand divided by the number of valid responses.
- **Average rank:** Average position of the brand when it appears.
- **Position-weighted visibility:** Gives more weight to brands appearing earlier in a response.
- **Share of voice:** A brand's share of the total counted mentions.
- **Visibility index:** Position-weighted visibility scaled so the highest-scoring brand receives an index of 100.

A brand that appears repeatedly near the beginning of responses will generally have greater visibility than a brand that appears infrequently or much later.

### 7. GEO-Gap calculation

The GEO-Gap stage compares brand merit with observed visibility.

The Person 3 analysis uses merit and visibility percentiles to derive a gap for eligible mentioned brands:

```text
GEO-Gap = Merit percentile - Visibility percentile
```

A positive gap indicates that a brand's merit percentile is higher than its visibility percentile. A negative gap indicates that its visibility percentile is higher than its merit percentile.

The analysis uses the following classifications:

| Classification | Meaning |
|---|---|
| Invisible | The brand was not mentioned in the valid LLM responses. |
| Under-visible | Merit is substantially higher than visibility. |
| Aligned | Merit and visibility are reasonably close. |
| Over-visible | Visibility is substantially higher than merit. |
| Low-evidence | The brand was mentioned, but its Amazon review evidence is insufficient for a reliable merit comparison. |

For this analysis, the comparison set contains the top 300 brands by review count plus all mentioned brands, giving 333 brands after exclusions. The minimum evidence threshold is 1,000 Amazon reviews for the percentile-based gap classification, and the gap threshold is 25 points.

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data processing, scoring, matching, and analytics |
| DuckDB | Memory-conscious processing of large review datasets |
| Pandas | Tabular data processing |
| PyArrow / Parquet | Efficient analytical data storage |
| RapidFuzz | Fuzzy string matching for brand normalization |
| VADER | Review-text sentiment analysis |
| SciPy | Statistical analysis, including rank correlation |
| Hugging Face Datasets | Source for Amazon Reviews 2023 |
| Groq API | LLM response generation |
| OpenRouter API | Additional LLM provider integration |
| Celery | Background task orchestration |
| Redis | Task queue and broker |
| React | Interactive dashboard interface |
| TypeScript | Frontend development |
| Vite | Frontend development server and build tooling |
| Excel / OpenPyXL | Exporting analysis results to workbooks |

---

## Dashboard Features

The React dashboard brings the project's analytical outputs together in one interface.

### 1. Overview

Presents a high-level view of the analysis, key counts, and the relationship between brand merit and LLM visibility.

### 2. GeoGap Explorer

Explores brand-level GEO-Gap classifications and compares merit against visibility. The quadrant visualization helps identify brands that are under-visible, aligned, over-visible, or invisible.

Low-evidence brands require separate interpretation because their merit estimates are not sufficiently supported by Amazon review volume.

### 3. Provider Benchmark

Compares brand visibility across LLM providers. This view helps identify which brands appear across providers and where recommendation patterns differ.

Provider comparisons are observational: differences may reflect model behaviour, routing, or response variability.

### 4. Category Trends

Examines how recommendations vary across user personas and query intents. This view helps reveal contextual patterns, such as dermatology-oriented brands appearing in sensitive-skin prompts and drugstore brands appearing in budget-oriented prompts.

### 5. Brand and Product Analysis

Supports exploration of brand and product benchmark metrics, including merit scores, review evidence, and visibility-related outputs where available in the connected dataset.

---

## Key Findings

The project has produced several initial findings from its beauty-domain LLM probing experiments.

- **CeraVe dominates observed visibility.** In the Person 3 analysis, it achieved a visibility index of 100, coverage of approximately 0.865, and an average rank of 1.47.
- **The next tier is difficult to order reliably.** La Roche-Posay, The Ordinary, and Neutrogena overlap in the bootstrap uncertainty analysis.
- **Merit and visibility have a weak relationship.** The Person 3 analysis reported a Spearman correlation of 0.24 across 41 mentioned brands with at least 1,000 Amazon reviews.
- **Many benchmark brands remain invisible.** Of 333 brands in the Person 3 comparison set, 275 were classified as invisible.
- **Persona is associated with different recommendation patterns.** Sensitive-skin prompts surfaced brands such as La Roche-Posay, Aveeno, Vanicream, and Cetaphil, while budget prompts surfaced brands such as Neutrogena, The Ordinary, Maybelline, and e.l.f.

These findings are preliminary and should be interpreted alongside the sample size, benchmark limitations, and uncertainty analysis.

---

## Installation and Setup

### Prerequisites

Install or configure the following before running the project:

- Python and pip
- Node.js and npm
- Git
- Redis, if running the background task orchestration
- API credentials for the LLM providers, if collecting new responses

### 1. Clone the repository

```powershell
git clone (https://github.com/diyakalamkar/geo-gap-analyzer)
cd geo-gap-analyzer
```

### 2. Set up the Python environment

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the Python dependencies from the repository's dependency file, if available. For example:

```powershell
pip install -r requirements.txt
```

If the repository does not contain a `requirements.txt`, use its documented dependency list or project configuration rather than assuming this command is sufficient.

### 3. Install frontend dependencies

Run the following from the directory containing the frontend's `package.json`:

```powershell
npm install
```

If the frontend lives at the repository root, run the command there. If it is in a subdirectory, navigate to that subdirectory first.

### 4. Configure environment variables

Set the required API keys as described in the next section.

---

## Running the Application

### Start the React dashboard

Open PowerShell in the directory containing the frontend `package.json`:

```powershell
npm run dev
```

Vite will print the local development URL in the terminal. Open that URL in your browser.

If npm reports `ENOENT` for `package.json`, confirm that the terminal is in the correct directory:

```powershell
Get-Location
Get-ChildItem package.json
```

### Run the backend analysis

Activate the Python environment and use the project scripts corresponding to the stage you intend to run.

The analysis stages should run in dependency order:

1. Load and clean review data.
2. Normalize product and brand names.
3. Calculate sentiment and merit.
4. Generate or load prompt definitions.
5. Collect or load LLM responses.
6. Extract and match brand mentions.
7. Calculate visibility and GEO-Gap outputs.
8. Validate and export the results.

The large-scale processing and live API collection stages do not need to be repeated simply to launch the frontend. Where valid output files already exist, reuse them.

### Background task processing

If using Celery and Redis for new probing runs:

1. Start Redis.
2. Start a Celery worker.
3. Start Celery Beat if scheduled execution is required.
4. Ensure the required environment variables are set in the worker terminal.
5. Dispatch the intended batch using the repository's supported command.

Scheduled tasks will not execute unless the necessary services are running.

---

## Environment Variables

The provider integrations use API keys supplied through environment variables.

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Authentication for Groq |
| `OPENROUTER_API_KEY` | Authentication for OpenRouter |

For a temporary PowerShell session:

```powershell
$env:GROQ_API_KEY = Read-Host "Paste your Groq API key"
$env:OPENROUTER_API_KEY = Read-Host "Paste your OpenRouter API key"
```

Check that a key is present without displaying its contents:

```powershell
python -c "import os; print('Groq key configured:', bool(os.environ.get('GROQ_API_KEY')))"
python -c "import os; print('OpenRouter key configured:', bool(os.environ.get('OPENROUTER_API_KEY')))"
```

Never commit API keys, `.env` files containing secrets, or credentials to Git.

---

## Data Outputs

The project generates analytical files in Parquet and JSONL formats, with optional Excel exports.

Representative outputs include:

| Output | Purpose |
|---|---|
| `geo_gap_product_ground_truth.parquet` | Ranked product benchmark |
| `product_visibility.parquet` | Matched product visibility records |
| `brand_visibility.parquet` | Matched brand visibility records |
| `geo_gap_product.parquet` | Product-level GEO-Gap results |
| `geo_gap_brand.parquet` | Brand-level GEO-Gap results |
| `llm_brand_mentions.parquet` | Extracted brand mentions and matching details |
| `geo_gap_responses/` | Stored LLM responses in JSONL format |
| `P3_visibility_gap_results.xlsx` | Consolidated Person 3 workbook, when generated |

The analysis also produces `brand_gap_p3.parquet` and `brand_visibility_p3.parquet`, which contain the comparison-set labels and visibility measures used in that analysis.

These files are not necessarily interchangeable: they may represent different pipeline stages, sample sizes, thresholds, or analysis runs.

Generated data files may be excluded from Git because of their size or project-specific `.gitignore` rules. Check repository configuration and data-access arrangements before attempting to reproduce the full pipeline.

---

## Acknowledgements

- **McAuley Lab** for the [Amazon Reviews 2023 dataset](https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023).
- The developers and maintainers of the open-source data-processing, NLP, statistical, and frontend libraries used in the project.
- The LLM providers used to collect experimental responses.

---

## Disclaimer

GEO-Gap Analyzer is an experimental research and analytics project. Its rankings and visibility-gap classifications depend on the selected dataset, prompts, LLM providers, matching rules, and scoring methodology.

The outputs should be interpreted as evidence of observed recommendation patterns within the tested sample, not as a definitive measure of brand quality or a guarantee of future LLM recommendations.
