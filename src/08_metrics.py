"""
08_metrics.py — Pipeline Metrics Computation
EECS 4312 SpecChain Project — Tasks 3.5, 4.5, 5.5, and 6

This script computes evaluation metrics for any pipeline (manual, automated,
or hybrid) and saves the results as JSON. It also generates a combined
summary file (metrics/metrics_summary.json) when all three exist.

Metrics computed:
  - dataset_size:        Total cleaned reviews
  - persona_count:       Number of personas
  - requirements_count:  Number of requirements in the spec
  - tests_count:         Number of test scenarios
  - traceability_links:  Explicit links between artifacts in the pipeline
  - review_coverage:     Ratio of reviews assigned to groups vs total
  - traceability_ratio:  Proportion of requirements traceable to a persona
  - testability_rate:    Proportion of requirements with at least one test
  - ambiguity_ratio:     Proportion of requirements containing vague language

Dependencies: None (uses only the Python standard library)

Usage:
  python src/08_metrics.py manual
  python src/08_metrics.py auto
  python src/08_metrics.py hybrid
  python src/08_metrics.py all       # runs all three + generates summary
"""

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# File path mapping for each pipeline
# ---------------------------------------------------------------------------
PIPELINE_FILES = {
    "manual": {
        "reviews":  PROJECT_ROOT / "data" / "reviews_clean.jsonl",
        "groups":   PROJECT_ROOT / "data" / "review_groups_manual.json",
        "personas": PROJECT_ROOT / "personas" / "personas_manual.json",
        "spec":     PROJECT_ROOT / "spec" / "spec_manual.md",
        "tests":    PROJECT_ROOT / "tests" / "tests_manual.json",
        "output":   PROJECT_ROOT / "metrics" / "metrics_manual.json",
    },
    "auto": {
        "reviews":  PROJECT_ROOT / "data" / "reviews_clean.jsonl",
        "groups":   PROJECT_ROOT / "data" / "review_groups_auto.json",
        "personas": PROJECT_ROOT / "personas" / "personas_auto.json",
        "spec":     PROJECT_ROOT / "spec" / "spec_auto.md",
        "tests":    PROJECT_ROOT / "tests" / "tests_auto.json",
        "output":   PROJECT_ROOT / "metrics" / "metrics_auto.json",
    },
    "hybrid": {
        "reviews":  PROJECT_ROOT / "data" / "reviews_clean.jsonl",
        "groups":   PROJECT_ROOT / "data" / "review_groups_hybrid.json",
        "personas": PROJECT_ROOT / "personas" / "personas_hybrid.json",
        "spec":     PROJECT_ROOT / "spec" / "spec_hybrid.md",
        "tests":    PROJECT_ROOT / "tests" / "tests_hybrid.json",
        "output":   PROJECT_ROOT / "metrics" / "metrics_hybrid.json",
    },
}

SUMMARY_PATH = PROJECT_ROOT / "metrics" / "metrics_summary.json"

# Words that indicate vague or ambiguous requirements
AMBIGUOUS_TERMS = [
    "fast", "quick", "quickly", "slow", "easy", "easily", "simple",
    "simply", "better", "good", "nice", "user-friendly", "user friendly",
    "intuitive", "intuitively", "efficient", "efficiently", "smooth",
    "smoothly", "responsive", "appropriate", "appropriately", "adequate",
    "reasonable", "reasonably", "flexible", "seamless", "seamlessly",
    "minimal", "sufficient", "optimal", "optimally", "improved",
    "enhanced", "robust", "reliable", "high-quality", "high quality",
    "performant", "lightweight", "friendly", "smart", "intelligent",
    "modern", "clean", "proper", "properly", "enough", "various",
    "several", "many", "few", "some", "most", "often", "sometimes",
]


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_jsonl(path):
    """Load a JSONL file and return a list of dicts."""
    items = []
    if not path.exists():
        return items
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def load_json(path):
    """Load a JSON file and return the parsed object."""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_requirements_from_spec(path):
    """Parse requirements from a spec markdown file (no regex)."""
    if not path.exists():
        return []

    lines = path.read_text(encoding="utf-8").splitlines()
    requirements = []
    current = None

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("# Requirement ID:"):
            if current:
                requirements.append(current)
            req_id = stripped.replace("# Requirement ID:", "").strip()
            current = {
                "requirement_id": req_id,
                "description": "",
                "source_persona": "",
                "traceability": "",
                "acceptance_criteria": "",
            }

        if current is None:
            continue

        if stripped.startswith("- Description:"):
            value = stripped.replace("- Description:", "").strip()
            current["description"] = value.strip("[]")

        elif stripped.startswith("- Source Persona:"):
            value = stripped.replace("- Source Persona:", "").strip()
            current["source_persona"] = value.strip("[]")

        elif stripped.startswith("- Traceability:"):
            value = stripped.replace("- Traceability:", "").strip()
            current["traceability"] = value.strip("[]")

        elif stripped.startswith("- Acceptance Criteria:"):
            value = stripped.replace("- Acceptance Criteria:", "").strip()
            current["acceptance_criteria"] = value.strip("[]")

    if current:
        requirements.append(current)

    return requirements


# ---------------------------------------------------------------------------
# Metric computations
# ---------------------------------------------------------------------------
def compute_review_coverage(reviews, groups_data):
    """Ratio of reviews assigned to at least one group vs total reviews."""
    total = len(reviews)
    if total == 0:
        return 0.0

    assigned_ids = set()
    for group in groups_data.get("groups", []):
        for rid in group.get("review_ids", []):
            assigned_ids.add(rid)

    return round(len(assigned_ids) / total, 4)


def compute_traceability_ratio(requirements):
    """Proportion of requirements that reference a persona."""
    if not requirements:
        return 0.0

    traceable = 0
    for req in requirements:
        persona = req.get("source_persona", "").strip()
        if persona and persona.lower() not in ("", "none", "n/a", "unknown"):
            traceable += 1

    return round(traceable / len(requirements), 4)


def compute_testability_rate(requirements, tests_data):
    """Proportion of requirements with at least one test scenario."""
    if not requirements:
        return 0.0

    tested_reqs = set()
    for test in tests_data.get("tests", []):
        rid = test.get("requirement_id", "")
        if rid:
            tested_reqs.add(rid)

    req_ids = {r["requirement_id"] for r in requirements}
    covered = req_ids.intersection(tested_reqs)

    return round(len(covered) / len(req_ids), 4)


def compute_ambiguity_ratio(requirements):
    """Proportion of requirements containing vague or non-measurable language."""
    if not requirements:
        return 0.0

    ambiguous_count = 0
    for req in requirements:
        # Check both description and acceptance criteria
        text = (
            req.get("description", "") + " " + req.get("acceptance_criteria", "")
        ).lower()

        for term in AMBIGUOUS_TERMS:
            if term in text:
                ambiguous_count += 1
                break  # count each requirement only once

    return round(ambiguous_count / len(requirements), 4)


def count_traceability_links(groups_data, personas_data, requirements, tests_data):
    """Count explicit traceable links between pipeline artifacts.

    Links counted:
      - Each persona linked to a group          (persona -> group)
      - Each requirement linked to a persona     (requirement -> persona)
      - Each requirement linked to a group        (requirement -> group)
      - Each test linked to a requirement         (test -> requirement)
    """
    links = 0

    # Persona -> group links
    for persona in personas_data.get("personas", []):
        if persona.get("group_id", ""):
            links += 1

    # Requirement -> persona links
    for req in requirements:
        if req.get("source_persona", "").strip():
            links += 1

    # Requirement -> group links (via traceability field)
    for req in requirements:
        trace = req.get("traceability", "").strip()
        if trace and trace.lower() not in ("", "none", "n/a"):
            links += 1

    # Test -> requirement links
    for test in tests_data.get("tests", []):
        if test.get("requirement_id", "").strip():
            links += 1

    return links


# ---------------------------------------------------------------------------
# Main metric computation for a single pipeline
# ---------------------------------------------------------------------------
def compute_metrics(pipeline_name):
    """Compute all metrics for the given pipeline and save to JSON."""

    files = PIPELINE_FILES.get(pipeline_name)
    if not files:
        print(f"[ERROR] Unknown pipeline: {pipeline_name}")
        return None

    print(f"\n[INFO] Computing metrics for '{pipeline_name}' pipeline...")

    # Load artifacts
    reviews = load_jsonl(files["reviews"])
    groups_data = load_json(files["groups"])
    personas_data = load_json(files["personas"])
    requirements = parse_requirements_from_spec(files["spec"])
    tests_data = load_json(files["tests"])

    # Compute
    dataset_size = len(reviews)
    persona_count = len(personas_data.get("personas", []))
    requirements_count = len(requirements)
    tests_count = len(tests_data.get("tests", []))
    traceability_links = count_traceability_links(
        groups_data, personas_data, requirements, tests_data
    )
    review_coverage = compute_review_coverage(reviews, groups_data)
    traceability_ratio = compute_traceability_ratio(requirements)
    testability_rate = compute_testability_rate(requirements, tests_data)
    ambiguity_ratio = compute_ambiguity_ratio(requirements)

    metrics = {
        "pipeline": pipeline_name if pipeline_name != "auto" else "automated",
        "dataset_size": dataset_size,
        "persona_count": persona_count,
        "requirements_count": requirements_count,
        "tests_count": tests_count,
        "traceability_links": traceability_links,
        "review_coverage": review_coverage,
        "traceability_ratio": traceability_ratio,
        "testability_rate": testability_rate,
        "ambiguity_ratio": ambiguity_ratio,
    }

    # Save
    output_path = files["output"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    # Print
    print(f"  Dataset size:        {dataset_size}")
    print(f"  Persona count:       {persona_count}")
    print(f"  Requirements count:  {requirements_count}")
    print(f"  Tests count:         {tests_count}")
    print(f"  Traceability links:  {traceability_links}")
    print(f"  Review coverage:     {review_coverage}")
    print(f"  Traceability ratio:  {traceability_ratio}")
    print(f"  Testability rate:    {testability_rate}")
    print(f"  Ambiguity ratio:     {ambiguity_ratio}")
    print(f"  [SAVED] {output_path}")

    return metrics


# ---------------------------------------------------------------------------
# Summary across all pipelines
# ---------------------------------------------------------------------------
def generate_summary():
    """Load all three metrics files and produce metrics_summary.json."""
    summary = {}
    all_present = True

    for name in ["manual", "auto", "hybrid"]:
        path = PIPELINE_FILES[name]["output"]
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                summary[name] = json.load(f)
        else:
            all_present = False
            print(f"  [SKIP] {path} not found")

    if summary:
        SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"  [SAVED] {SUMMARY_PATH}")

    if not all_present:
        print("  [NOTE] Summary is partial — not all pipelines computed yet.")

    return summary


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else ["auto"]
    target = args[0].lower()

    if target == "all":
        for name in ["manual", "auto", "hybrid"]:
            compute_metrics(name)
        print(f"\n{'=' * 50}")
        print("  Generating summary...")
        generate_summary()
    elif target in PIPELINE_FILES:
        compute_metrics(target)
        print(f"\n{'=' * 50}")
        print("  Checking for summary generation...")
        generate_summary()
    else:
        print(f"[ERROR] Unknown target: {target}")
        print("  Usage: python src/08_metrics.py [manual|auto|hybrid|all]")
        return

    print(f"{'=' * 50}")
    print("  Metrics computation complete.")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()