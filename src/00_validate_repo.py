"""
00_validate_repo.py — Repository Structure Validator
EECS 4312 SpecChain Project — Task 7

This script checks whether all required folders and files exist in the
repository and prints a clear status message for each.

Usage:
  python src/00_validate_repo.py
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# All required files from the assignment specification
# ---------------------------------------------------------------------------
REQUIRED_FILES = [
    # Data files
    "data/reviews_raw.jsonl",
    "data/reviews_clean.jsonl",
    "data/dataset_metadata.json",
    "data/review_groups_manual.json",
    "data/review_groups_auto.json",
    "data/review_groups_hybrid.json",

    # Persona files
    "personas/personas_manual.json",
    "personas/personas_auto.json",
    "personas/personas_hybrid.json",

    # Specification files
    "spec/spec_manual.md",
    "spec/spec_auto.md",
    "spec/spec_hybrid.md",

    # Test files
    "tests/tests_manual.json",
    "tests/tests_auto.json",
    "tests/tests_hybrid.json",

    # Metric files
    "metrics/metrics_manual.json",
    "metrics/metrics_auto.json",
    "metrics/metrics_hybrid.json",

    # Prompt files
    "prompts/prompt_auto.json",

    # Source scripts
    "src/00_validate_repo.py",
    "src/01_collect_or_import.py",
    "src/02_clean.py",
    "src/04_personas_manual.py",
    "src/05_personas_auto.py",
    "src/06_spec_generate.py",
    "src/07_tests_generate.py",
    "src/08_metrics.py",
    "src/run_all.py",

    # Documentation
    "README.md",
    "reflection/reflection.md",
]


def main():
    print("Checking repository structure...")
    print()

    found_count = 0
    missing_count = 0

    for filepath in REQUIRED_FILES:
        full_path = PROJECT_ROOT / filepath
        if full_path.exists():
            print(f"  {filepath} found")
            found_count += 1
        else:
            print(f"  {filepath} MISSING")
            missing_count += 1

    print()
    print("-" * 50)
    if missing_count == 0:
        print(f"  All {found_count} required files found.")
        print("  Repository validation complete")
    else:
        print(f"  Found: {found_count}/{found_count + missing_count}")
        print(f"  Missing: {missing_count}")
        print("  Repository validation INCOMPLETE")
    print("-" * 50)


if __name__ == "__main__":
    main()