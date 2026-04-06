"""
run_all.py — Automated Pipeline Runner
EECS 4312 SpecChain Project — Task 7

This script executes the full automated pipeline from start to finish.
It does NOT run manual or hybrid steps, only the programmatic pipeline.

Execution order:
  Step 1: Clean raw reviews         → data/reviews_clean.jsonl
  Step 2: Group reviews + personas  → data/review_groups_auto.json
                                      personas/personas_auto.json
                                      prompts/prompt_auto.json
  Step 3: Generate specifications   → spec/spec_auto.md
  Step 4: Generate validation tests → tests/tests_auto.json
  Step 5: Compute metrics           → metrics/metrics_auto.json

Usage:
  python src/run_all.py
"""

import os
import sys
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

# ---------------------------------------------------------------------------
# Pipeline steps — each entry is (script name, description, outputs)
# ---------------------------------------------------------------------------
PIPELINE = [
    (
        "02_clean.py",
        "Step 1: Cleaning raw reviews",
        ["data/reviews_clean.jsonl"],
    ),
    (
        "05_personas_auto.py",
        "Step 2: Grouping reviews and generating personas (LLM)",
        ["data/review_groups_auto.json", "personas/personas_auto.json", "prompts/prompt_auto.json"],
    ),
    (
        "06_spec_generate.py",
        "Step 3: Generating specifications from personas (LLM)",
        ["spec/spec_auto.md"],
    ),
    (
        "07_tests_generate.py",
        "Step 4: Generating validation tests from specifications (LLM)",
        ["tests/tests_auto.json"],
    ),
    (
        "08_metrics.py",
        "Step 5: Computing metrics for the automated pipeline",
        ["metrics/metrics_auto.json"],
    ),
]


def prompt_for_api_key():
    """Prompt the user for their Groq API key and set it globally."""
    print("=" * 60)
    print("  EECS 4312 SpecChain — Automated Pipeline Runner")
    print("=" * 60)
    print()
    print("This script requires a Groq API key for Steps 2-4.")
    print("Get yours at: https://console.groq.com/keys")
    print()

    api_key = input("Enter your Groq API key: ").strip()

    if not api_key:
        print("[ERROR] No API key entered. Exiting.")
        sys.exit(1)

    # Set the key in the current process environment.
    # All child processes launched by subprocess will inherit this.
    os.environ["GROQ_API_KEY"] = api_key
    print("[OK] API key set for this session.\n")


def run_step(script_name, description, expected_outputs):
    """Run a single pipeline script as a subprocess."""
    script_path = SRC_DIR / script_name
    if not script_path.exists():
        print(f"  [ERROR] Script not found: {script_path}")
        return False

    print("-" * 60)
    print(f"  {description}")
    print(f"  Running: python src/{script_name}")
    print("-" * 60)

    # Run the script as a subprocess so it inherits the environment
    # (including GROQ_API_KEY) and runs in the project root directory.
    # For 08_metrics.py, pass "auto" as an argument.
    cmd = [sys.executable, str(script_path)]
    if script_name == "08_metrics.py":
        cmd.append("auto")

    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        env=os.environ.copy(),
    )

    if result.returncode != 0:
        print(f"\n  [ERROR] {script_name} exited with code {result.returncode}")
        return False

    # Verify expected outputs were created
    all_found = True
    for output_file in expected_outputs:
        full_path = PROJECT_ROOT / output_file
        if full_path.exists():
            print(f"  [OK] {output_file} created")
        else:
            print(f"  [MISSING] {output_file} was not created")
            all_found = False

    print()
    return all_found


def main():
    # --- Prompt for API key before anything runs ---
    prompt_for_api_key()

    # --- Verify raw data exists ---
    raw_path = PROJECT_ROOT / "data" / "reviews_raw.jsonl"
    if not raw_path.exists():
        print(f"[ERROR] Raw dataset not found: {raw_path}")
        print("  Please place reviews_raw.jsonl in the data/ folder first.")
        sys.exit(1)

    print(f"[OK] Raw dataset found: {raw_path}\n")

    # --- Run each step sequentially ---
    failed = False
    for script_name, description, outputs in PIPELINE:
        success = run_step(script_name, description, outputs)
        if not success:
            print(f"[ERROR] Pipeline stopped at: {description}")
            failed = True
            break

    # --- Final summary ---
    print("=" * 60)
    if failed:
        print("  Pipeline FAILED — see errors above.")
    else:
        print("  Automated Pipeline Complete")
        print()
        print("  Files produced:")
        for _, _, outputs in PIPELINE:
            for f in outputs:
                print(f"    {f}")
    print("=" * 60)


if __name__ == "__main__":
    main()