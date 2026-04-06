# SpecChain — EECS 4312 Course Project (Winter 2026)

## Application Studied

**Headspace: Meditate, Sleep, Relax** — a meditation and mental wellness app on the Google Play Store (`com.getsomeheadspace.android`). Headspace provides guided meditations, sleepcasts, breathing exercises, and focus tools.

## Dataset

- **Raw reviews collected:** 2,500
- **Cleaned reviews retained:** 2,375 (95% retention rate)
- **Source:** Google Play Store - English reviews
- **Collection script:** `src/01_collect_or_import.py` using the `google-play-scraper` Python library
- **Cleaning script:** `src/02_clean.py` 

Cleaning steps included: deduplication, removal of empty and extremely short reviews, lowercasing, contraction expansion, number-to-text conversion, emoji and punctuation removal, light stop-word removal, and relaxed lemmatization.

## Repository Structure

```
SpecChain/
├── data/
│   ├── reviews_raw.jsonl              # Raw scraped reviews
│   ├── reviews_clean.jsonl            # Cleaned reviews (2,375)
│   ├── dataset_metadata.json          # App info, dataset size, cleaning decisions
│   ├── review_groups_manual.json      # Manual review groups (5 groups)
│   ├── review_groups_auto.json        # Automated review groups (5 groups)
│   └── review_groups_hybrid.json      # Hybrid review groups (5 groups)
├── personas/
│   ├── personas_manual.json           # Manual personas (5)
│   ├── personas_auto.json             # Automated personas (5)
│   └── personas_hybrid.json           # Hybrid personas (5)
├── spec/
│   ├── spec_manual.md                 # Manual specification (14 requirements)
│   ├── spec_auto.md                   # Automated specification (15 requirements)
│   └── spec_hybrid.md                 # Hybrid specification (15 requirements)
├── tests/
│   ├── tests_manual.json              # Manual test scenarios (28 tests)
│   ├── tests_auto.json                # Automated test scenarios (30 tests)
│   └── tests_hybrid.json             # Hybrid test scenarios (30 tests)
├── metrics/
│   ├── metrics_manual.json            # Manual pipeline metrics
│   ├── metrics_auto.json              # Automated pipeline metrics
│   ├── metrics_hybrid.json            # Hybrid pipeline metrics
│   └── metrics_summary.json           # Combined comparison across all three
├── prompts/
│   └── prompt_auto.json               # LLM prompting strategy for automation
├── reflection/
│   └── reflection.md                  # Pipeline comparison and reflection
├── src/
│   ├── 00_validate_repo.py            # Checks all required files exist
│   ├── 01_collect_or_import.py        # Scrapes reviews from Google Play
│   ├── 02_clean.py                    # Cleans raw reviews (no external deps)
│   ├── 04_personas_manual.py          # Manual persona coding template
│   ├── 05_personas_auto.py            # Automated grouping + persona generation
│   ├── 06_spec_generate.py            # Automated specification generation
│   ├── 07_tests_generate.py           # Automated test generation
│   ├── 08_metrics.py                  # Metrics computation (all pipelines)
│   └── run_all.py                     # Runs the full automated pipeline
└── README.md
```

## How to Reproduce the Automated Pipeline

### Prerequisites

- Python 3.10 or later
- `groq` package: `pip install groq`
- `google-play-scraper` package (only needed for data collection): `pip install google-play-scraper`
- A Groq API key from [console.groq.com](https://console.groq.com/keys)

### Run the full automated pipeline

```bash
python3 src/run_all.py
```

The script will prompt you for your Groq API key, then execute the following steps in order:

1. `02_clean.py` — Cleans raw reviews → `data/reviews_clean.jsonl`
2. `05_personas_auto.py` — Groups reviews and generates personas - `data/review_groups_auto.json`, `personas/personas_auto.json`, `prompts/prompt_auto.json`
3. `06_spec_generate.py` — Generates specifications from personas - `spec/spec_auto.md`
4. `07_tests_generate.py` — Generates validation tests from specs - `tests/tests_auto.json`
5. `08_metrics.py` — Computes metrics → `metrics/metrics_auto.json`

### Run individual scripts

```bash
python3 src/02_clean.py                # Clean reviews only
python3 src/05_personas_auto.py        # Grouping + personas (requires GROQ_API_KEY)
python3 src/06_spec_generate.py        # Specifications (requires GROQ_API_KEY)
python3 src/07_tests_generate.py       # Tests (requires GROQ_API_KEY)
python3 src/08_metrics.py auto         # Metrics for automated pipeline
python3 src/08_metrics.py manual       # Metrics for manual pipeline
python3 src/08_metrics.py hybrid       # Metrics for hybrid pipeline
python3 src/08_metrics.py all          # All three + summary
```

### Validate repository structure

```bash
python3 src/00_validate_repo.py
```

## Metrics Summary

| Metric               | Manual | Automated | Hybrid |
|----------------------|--------|-----------|--------|
| Personas             | 5      | 5         | 5      |
| Requirements         | 14     | 15        | 15     |
| Tests                | 28     | 30        | 30     |
| Traceability links   | 136    | 65        | 65     |
| Review coverage      | 0.025  | 1.0       | 0.04   |
| Traceability ratio   | 1.0    | 1.0       | 1.0    |
| Testability rate     | 1.0    | 1.0       | 1.0    |
| Ambiguity ratio      | 0.143  | 0.067     | 0.067  |