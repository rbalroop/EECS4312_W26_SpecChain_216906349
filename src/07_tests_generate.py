"""
07_tests_generate.py — Automated Validation Test Generation

This script reads the automated specification (spec/spec_auto.md), parses
each requirement, and uses Groq to generate validation
test scenarios saved to tests/tests_auto.json.

Each test includes:
  - Unique test ID (T_auto_N)
  - Requirement ID it validates
  - Short scenario description
  - Steps for execution
  - Expected result

Dependencies: groq (pip install groq)
Requires: GROQ_API_KEY environment variable

"""

import json
import os
import time
from pathlib import Path
from groq import Groq

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
SEED = 4312
TESTS_PER_REQUIREMENT = 2   # at least 1 required; 2 gives stronger coverage
DELAY_BETWEEN_CALLS = 3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH  = PROJECT_ROOT / "spec" / "spec_auto.md"
TESTS_OUT  = PROJECT_ROOT / "tests" / "tests_auto.json"

client = Groq()


# ---------------------------------------------------------------------------
# Parse requirements from spec markdown 
# ---------------------------------------------------------------------------
def parse_spec(path):
    """Extract structured requirements from spec/spec_auto.md line by line."""
    lines = path.read_text(encoding="utf-8").splitlines()

    requirements = []
    current = None

    for line in lines:
        stripped = line.strip()

        # New requirement block
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

        # Skip lines until we have a current requirement
        if current is None:
            continue

        # Extract fields by prefix — strip the brackets from values
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

    #  last requirement
    if current:
        requirements.append(current)

    return requirements


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------
def call_llm(system, user, tag=""):
    """Single Groq API call with retry logic and rate-limit delay."""
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                temperature=0.3,
                seed=SEED,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
            )
            time.sleep(DELAY_BETWEEN_CALLS)
            content = resp.choices[0].message.content
            if content is None:
                raise ValueError("LLM returned empty response")
            return json.loads(content)
        except Exception as e:
            wait = DELAY_BETWEEN_CALLS * (attempt + 2)
            print(f"  [RETRY {attempt+1}] {tag}: {e} — waiting {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"Failed after 3 attempts: {tag}")


# ---------------------------------------------------------------------------
# Generate tests — batch requirements to reduce API calls
# ---------------------------------------------------------------------------
def generate_tests(requirements):
    """Send requirements in batches and generate test scenarios."""

    system = (
        "You are a software test engineer. Generate validation test scenarios "
        "for a meditation app based on functional requirements. "
        "Return only valid JSON."
    )

    all_tests = []

    # Batch 5 requirements per call to minimize API usage
    batch_size = 5
    batches = [
        requirements[i:i + batch_size]
        for i in range(0, len(requirements), batch_size)
    ]

    print(f"[INFO] Generating tests in {len(batches)} batches...\n")

    for batch_idx, batch in enumerate(batches):
        # Build the requirements block for this batch
        req_block = ""
        for req in batch:
            req_block += (
                f"\nRequirement: {req['requirement_id']}\n"
                f"  Description: {req['description']}\n"
                f"  Source Persona: {req['source_persona']}\n"
                f"  Acceptance Criteria: {req['acceptance_criteria']}\n"
            )

        user = f"""Generate exactly {TESTS_PER_REQUIREMENT} validation test scenarios for EACH of the following requirements.

{req_block}

Each test must contain:
- test_id: a unique ID (use T_auto_1, T_auto_2, etc. as placeholders)
- requirement_id: the requirement it validates (e.g. FR_auto_1)
- scenario: a short description of what is being tested
- steps: a list of 3-5 clear steps describing how the test would be executed
- expected_result: what should happen if the requirement is met

Make sure:
- Every requirement has exactly {TESTS_PER_REQUIREMENT} tests
- Steps are specific and actionable
- Expected results directly reflect the requirement being validated

Return JSON:
{{
  "tests": [
    {{
      "test_id": "T_auto_1",
      "requirement_id": "FR_auto_1",
      "scenario": "short description",
      "steps": ["step 1", "step 2", "step 3"],
      "expected_result": "what should happen"
    }}
  ]
}}"""

        result = call_llm(system, user, tag=f"batch-{batch_idx+1}/{len(batches)}")
        batch_tests = result.get("tests", [])
        all_tests.extend(batch_tests)
        print(f"  Batch {batch_idx+1}/{len(batches)}: "
              f"generated {len(batch_tests)} tests")

    # Reassign clean sequential IDs
    for i, test in enumerate(all_tests):
        test["test_id"] = f"T_auto_{i + 1}"

    return all_tests


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if not os.environ.get("GROQ_API_KEY"):
        print("[ERROR] GROQ_API_KEY environment variable not set.")
        return

    # Parse requirements from spec
    requirements = parse_spec(SPEC_PATH)
    print(f"[INFO] Parsed {len(requirements)} requirements from {SPEC_PATH}")

    if not requirements:
        print("[ERROR] No requirements found. Run 06_spec_generate.py first.")
        return

    # Generate tests
    all_tests = generate_tests(requirements)

    # Check coverage
    req_ids = {r["requirement_id"] for r in requirements}
    covered = {t["requirement_id"] for t in all_tests}
    missing = req_ids - covered
    if missing:
        print(f"\n  [WARN] {len(missing)} requirements lack tests: {missing}")

    # Save
    TESTS_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(TESTS_OUT, "w", encoding="utf-8") as f:
        json.dump({"tests": all_tests}, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 50}")
    print(f"  Test Generation Complete")
    print(f"{'=' * 50}")
    print(f"  Total tests generated: {len(all_tests)}")
    print(f"  Requirements covered:  {len(covered)}/{len(req_ids)}")
    print(f"  Output: {TESTS_OUT}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()