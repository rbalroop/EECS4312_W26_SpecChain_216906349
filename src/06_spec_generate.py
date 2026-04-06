"""
06_spec_generate.py — Automated Specification Generation

This script reads the automated personas (personas/personas_auto.json) and
review groups (data/review_groups_auto.json), then uses Groq to
generate system requirements saved to spec/spec_auto.md.

Each requirement includes:
  - Unique requirement ID (FR_auto_N)
  - Description of system behavior
  - Source persona
  - Traceability to review group
  - Acceptance criteria in Given/When/Then format

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
MIN_REQUIREMENTS = 10          # assignment minimum
REQUIREMENTS_PER_PERSONA = 3   # aim for 3 per persona (5 personas = 15 total)
DELAY_BETWEEN_CALLS = 3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PERSONAS_PATH = PROJECT_ROOT / "personas" / "personas_auto.json"
GROUPS_PATH   = PROJECT_ROOT / "data" / "review_groups_auto.json"
SPEC_OUT      = PROJECT_ROOT / "spec" / "spec_auto.md"

client = Groq()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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
# Generate requirements for one persona
# ---------------------------------------------------------------------------
def generate_requirements_for_persona(persona, group, start_id):
    """Ask the LLM to produce requirements for a single persona."""

    system = (
        "You are a software requirements engineer. "
        "Generate clear, testable functional requirements for a meditation app "
        "based on user persona data. Return only valid JSON."
    )

    user = f"""Based on the persona and review group below, generate exactly {REQUIREMENTS_PER_PERSONA} functional requirements for the Headspace meditation app.

Persona:
- Name: {persona.get("name", "Unknown")}
- Persona ID: {persona.get("persona_id", "")}
- Group ID: {persona.get("group_id", "")}
- Goals: {json.dumps(persona.get("goals", []))}
- Pain Points: {json.dumps(persona.get("pain_points", []))}
- Context: {persona.get("context", "")}

Review Group Theme: {group.get("theme", "")}
Review Group Description: {group.get("description", "")}
Number of reviews in group: {len(group.get("review_ids", []))}
Example reviews: {json.dumps(group.get("example_reviews", []))}

For each requirement:
- The description must start with "The system shall" and describe specific system behavior
- Acceptance criteria must use Given/When/Then format
- Requirements must be specific and testable (avoid vague words like "fast", "easy", "user-friendly")

Return JSON in this exact format:
{{
  "requirements": [
    {{
      "requirement_id": "FR_auto_{start_id}",
      "description": "The system shall ...",
      "source_persona": "{persona.get("name", "Unknown")}",
      "traceability": "Derived from review group {persona.get("group_id", "")}",
      "acceptance_criteria": "Given ..., When ..., Then ..."
    }},
    {{
      "requirement_id": "FR_auto_{start_id + 1}",
      "description": "The system shall ...",
      "source_persona": "{persona.get("name", "Unknown")}",
      "traceability": "Derived from review group {persona.get("group_id", "")}",
      "acceptance_criteria": "Given ..., When ..., Then ..."
    }},
    {{
      "requirement_id": "FR_auto_{start_id + 2}",
      "description": "The system shall ...",
      "source_persona": "{persona.get("name", "Unknown")}",
      "traceability": "Derived from review group {persona.get("group_id", "")}",
      "acceptance_criteria": "Given ..., When ..., Then ..."
    }}
  ]
}}"""

    result = call_llm(system, user, tag=f"spec-{persona.get('group_id', '?')}")
    return result.get("requirements", [])


# ---------------------------------------------------------------------------
# Format requirements into markdown
# ---------------------------------------------------------------------------
def format_spec_markdown(all_requirements, personas_data, groups_data):
    """Build the spec/spec_auto.md file content."""

    lines = [
        "# Automated Specification — Headspace: Meditation & Sleep",
        "",
        "**Generated by:** 06_spec_generate.py (LLM-assisted pipeline)",
        f"**Model:** {MODEL}",
        f"**Total requirements:** {len(all_requirements)}",
        f"**Personas used:** {len(personas_data.get('personas', []))}",
        "",
        "---",
        "",
    ]

    for req in all_requirements:
        lines.append(f"# Requirement ID: {req['requirement_id']}")
        lines.append(f"- Description: [{req['description']}]")
        lines.append("")
        lines.append(f"- Source Persona: [{req['source_persona']}]")
        lines.append(f"- Traceability: [{req['traceability']}]")
        lines.append(f"- Acceptance Criteria:[{req['acceptance_criteria']}]")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if not os.environ.get("GROQ_API_KEY"):
        print("[ERROR] GROQ_API_KEY environment variable not set.")
        return

    personas_data = load_json(PERSONAS_PATH)
    groups_data = load_json(GROUPS_PATH)

    # Build a lookup from group_id to group
    group_lookup = {
        g["group_id"]: g for g in groups_data.get("groups", [])
    }

    personas = personas_data.get("personas", [])
    print(f"[INFO] Loaded {len(personas)} personas and {len(group_lookup)} groups.")
    print(f"[INFO] Generating {REQUIREMENTS_PER_PERSONA} requirements per persona...\n")

    all_requirements = []
    req_counter = 1

    for persona in personas:
        gid = persona.get("group_id", "")
        group = group_lookup.get(gid, {"theme": "", "description": "", "review_ids": [], "example_reviews": []})

        print(f"  Generating for {persona.get('name', '?')} ({gid})...")
        reqs = generate_requirements_for_persona(persona, group, req_counter)

        # Ensure IDs are sequential and consistent
        for req in reqs:
            req["requirement_id"] = f"FR_auto_{req_counter}"
            req["source_persona"] = persona.get("name", "Unknown")
            req["traceability"] = f"Derived from review group {gid}"
            all_requirements.append(req)
            req_counter += 1

    # Write markdown spec
    spec_md = format_spec_markdown(all_requirements, personas_data, groups_data)
    SPEC_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(SPEC_OUT, "w", encoding="utf-8") as f:
        f.write(spec_md)

    print(f"\n{'=' * 50}")
    print(f"  Specification Generation Complete")
    print(f"{'=' * 50}")
    print(f"  Total requirements: {len(all_requirements)}")
    print(f"  Output: {SPEC_OUT}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()