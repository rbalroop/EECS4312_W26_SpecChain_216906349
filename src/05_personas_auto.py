"""
05_personas_auto.py — Automated Review Grouping & Persona Generation

This script:
  Phase 1 — Samples reviews to discover 5 distinct user-situation themes (1 API call)
  Phase 2 — Chunks ALL cleaned reviews and classifies each into a theme (multiple calls)
  Phase 3 — Generates a structured persona for each group (1 API call)

Dependencies: groq (pip install groq)
Requires: GROQ_API_KEY environment variable

"""

import json
import os
import time
import random
from pathlib import Path
from groq import Groq

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
SEED = 4312
NUM_GROUPS = 5
CHUNK_SIZE = 100          # reviews per classification call
DELAY_BETWEEN_CALLS = 3   # seconds — keeps us under Groq free-tier rate limits
SAMPLE_SIZE_PER_RATING = 30  # for theme discovery only (Phase 1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEAN_PATH      = PROJECT_ROOT / "data" / "reviews_clean.jsonl"
GROUPS_OUT      = PROJECT_ROOT / "data" / "review_groups_auto.json"
PERSONAS_OUT    = PROJECT_ROOT / "personas" / "personas_auto.json"
PROMPT_OUT      = PROJECT_ROOT / "prompts" / "prompt_auto.json"

client = Groq()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_reviews(path):
    """Load all cleaned reviews from JSONL."""
    reviews = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                reviews.append(json.loads(line))
    print(f"[INFO] Loaded {len(reviews)} cleaned reviews.")
    return reviews


def call_llm(system, user, tag=""):
    """Single Groq API call with retry logic and rate-limit delay."""
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                temperature=0.2,
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


def save_json(path, data):
    """Write JSON to file, creating parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[SAVED] {path}")


# ---------------------------------------------------------------------------
# Phase 1 — Discover themes from a stratified sample
# ---------------------------------------------------------------------------
def discover_themes(reviews):
    """Send a sample of reviews to the LLM and ask it to identify 5 themes."""
    rng = random.Random(SEED)
    buckets = {1: [], 2: [], 3: [], 4: [], 5: []}
    for r in reviews:
        rating = r.get("rating")
        if rating in buckets:
            buckets[rating].append(r)

    sample = []
    for rating in sorted(buckets):
        pool = buckets[rating]
        rng.shuffle(pool)
        sample.extend(pool[:SAMPLE_SIZE_PER_RATING])
    rng.shuffle(sample)

    review_block = "\n".join(
        f'{r["review_id"]} | rating={r["rating"]} | {r["cleaned_text"]}'
        for r in sample
    )

    system = (
        "You are a software requirements analyst. "
        "Identify distinct user-situation themes from app reviews. "
        "Return only valid JSON."
    )
    user = f"""Below are sample user reviews for the Headspace meditation app.

Identify exactly {NUM_GROUPS} distinct themes that represent different types of users
or user situations. Each theme should be broad enough to capture many reviews.

Return JSON in this exact format:
{{
  "themes": [
    {{"group_id": "G1", "theme": "short descriptive theme name", "description": "one sentence explaining this user group"}},
    {{"group_id": "G2", "theme": "...", "description": "..."}},
    {{"group_id": "G3", "theme": "...", "description": "..."}},
    {{"group_id": "G4", "theme": "...", "description": "..."}},
    {{"group_id": "G5", "theme": "...", "description": "..."}}
  ]
}}

Reviews:
{review_block}"""

    print("[Phase 1] Discovering themes from sample...")
    result = call_llm(system, user, tag="theme-discovery")
    themes = result.get("themes", [])
    print(f"  Found {len(themes)} themes:")
    for t in themes:
        print(f"    {t['group_id']}: {t['theme']}")
    return themes


# ---------------------------------------------------------------------------
# Phase 2 — Classify ALL reviews into themes in chunks
# ---------------------------------------------------------------------------
def classify_all_reviews(reviews, themes):
    """Send reviews in chunks and ask the LLM to assign each to a theme."""
    theme_block = "\n".join(
        f'{t["group_id"]}: {t["theme"]} — {t["description"]}'
        for t in themes
    )

    # Initialize group buckets
    groups = {t["group_id"]: [] for t in themes}
    unassigned = []

    chunks = [reviews[i:i + CHUNK_SIZE] for i in range(0, len(reviews), CHUNK_SIZE)]
    print(f"\n[Phase 2] Classifying {len(reviews)} reviews in {len(chunks)} chunks...")

    system = (
        "You are classifying app reviews into predefined themes. "
        "Return only valid JSON."
    )

    for idx, chunk in enumerate(chunks):
        review_block = "\n".join(
            f'{r["review_id"]} | {r["cleaned_text"]}'
            for r in chunk
        )

        user = f"""Assign each review below to exactly one of these themes:

{theme_block}

For each review, return its review_id and the group_id it best fits.
If a review does not clearly fit any theme, assign it to the closest one.

Return JSON in this format:
{{
  "assignments": [
    {{"review_id": "clean_00001", "group_id": "G1"}},
    {{"review_id": "clean_00002", "group_id": "G3"}}
  ]
}}

Reviews:
{review_block}"""

        result = call_llm(system, user, tag=f"chunk-{idx+1}/{len(chunks)}")
        assignments = result.get("assignments", [])

        for a in assignments:
            gid = a.get("group_id", "")
            rid = a.get("review_id", "")
            if gid in groups:
                groups[gid].append(rid)
            else:
                unassigned.append(rid)

        print(f"  Chunk {idx+1}/{len(chunks)}: classified {len(assignments)} reviews")

    # Report
    for gid, ids in groups.items():
        print(f"  {gid}: {len(ids)} reviews")
    if unassigned:
        print(f"  Unassigned: {len(unassigned)} (distributed to smallest group)")
        smallest = min(groups, key=lambda g: len(groups[g]))
        groups[smallest].extend(unassigned)

    return groups


# ---------------------------------------------------------------------------
# Phase 2b — Build the output structure with example reviews
# ---------------------------------------------------------------------------
def build_group_output(reviews, themes, groups):
    """Assemble the final review_groups_auto.json structure."""
    review_lookup = {r["review_id"]: r for r in reviews}

    output_groups = []
    for theme in themes:
        gid = theme["group_id"]
        ids = groups.get(gid, [])

        # Pick 2 example reviews from the group
        examples = []
        for rid in ids[:2]:
            if rid in review_lookup:
                examples.append(review_lookup[rid].get("original_text", ""))

        output_groups.append({
            "group_id": gid,
            "theme": theme["theme"],
            "description": theme["description"],
            "review_ids": ids,
            "example_reviews": examples,
        })

    return {"groups": output_groups}


# ---------------------------------------------------------------------------
# Phase 3 — Generate personas from groups
# ---------------------------------------------------------------------------
def generate_personas(reviews, group_data):
    """Generate one persona per group using the LLM."""
    review_lookup = {r["review_id"]: r for r in reviews}

    system = (
        "You are a software requirements analyst creating user personas "
        "from app review data. Return only valid JSON."
    )

    personas = []
    print(f"\n[Phase 3] Generating {len(group_data['groups'])} personas...")

    for group in group_data["groups"]:
        # Collect sample review texts for this group (up to 15 for context)
        sample_texts = []
        for rid in group["review_ids"][:15]:
            if rid in review_lookup:
                sample_texts.append(review_lookup[rid].get("original_text", ""))

        reviews_block = "\n".join(f"- {t}" for t in sample_texts)

        user = f"""Based on the following review group, create one detailed user persona.

Group: {group["group_id"]} — {group["theme"]}
Description: {group["description"]}
Number of reviews in group: {len(group["review_ids"])}

Sample reviews:
{reviews_block}

Return JSON in this exact format:
{{
  "persona_id": "{group["group_id"]}_persona",
  "group_id": "{group["group_id"]}",
  "name": "A realistic first name",
  "age_range": "e.g. 25-35",
  "occupation": "realistic occupation",
  "goals": ["goal 1", "goal 2", "goal 3"],
  "pain_points": ["pain point 1", "pain point 2", "pain point 3"],
  "context": "A 2-3 sentence description of this persona's situation and how they use the app",
  "review_group_theme": "{group["theme"]}",
  "review_count": {len(group["review_ids"])}
}}"""

        result = call_llm(system, user, tag=f"persona-{group['group_id']}")
        # Ensure required fields are present
        result["group_id"] = group["group_id"]
        result["review_group_theme"] = group["theme"]
        result["review_count"] = len(group["review_ids"])
        personas.append(result)
        print(f"  Created persona: {result.get('name', '?')} ({group['group_id']})")

    return {"personas": personas}


# ---------------------------------------------------------------------------
# Save prompts for reproducibility
# ---------------------------------------------------------------------------
def save_prompts(themes):
    """Save the prompting strategy for the submission requirement."""
    prompt_record = {
        "model": MODEL,
        "seed": SEED,
        "temperature": 0.2,
        "strategy": "Three-phase LLM pipeline: (1) theme discovery from stratified "
                     "sample, (2) chunk-based classification of all reviews into "
                     "themes, (3) persona generation per group.",
        "phase_1_prompt_summary": "Given a stratified sample of reviews, identify "
                                  f"exactly {NUM_GROUPS} distinct user-situation themes.",
        "phase_2_prompt_summary": f"For each chunk of {CHUNK_SIZE} reviews, assign "
                                  "every review to the closest theme by group_id.",
        "phase_3_prompt_summary": "For each group, generate a structured persona with "
                                  "name, goals, pain points, and context.",
        "discovered_themes": themes,
    }
    save_json(PROMPT_OUT, prompt_record)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if not os.environ.get("GROQ_API_KEY"):
        print("[ERROR] GROQ_API_KEY environment variable not set.")
        print("  Get your key at https://console.groq.com/keys")
        print("  Then run: export GROQ_API_KEY=\"gsk_your_key_here\"")
        return

    reviews = load_reviews(CLEAN_PATH)

    # Phase 1: Discover themes
    themes = discover_themes(reviews)

    # Phase 2: Classify all reviews
    groups = classify_all_reviews(reviews, themes)
    group_data = build_group_output(reviews, themes, groups)
    save_json(GROUPS_OUT, group_data)

    # Phase 3: Generate personas
    persona_data = generate_personas(reviews, group_data)
    save_json(PERSONAS_OUT, persona_data)

    # Save prompts
    save_prompts(themes)

    # Summary
    print(f"\n{'=' * 50}")
    print(f"  Pipeline Complete")
    print(f"{'=' * 50}")
    total_assigned = sum(len(g["review_ids"]) for g in group_data["groups"])
    print(f"  Reviews classified: {total_assigned}/{len(reviews)}")
    print(f"  Groups: {len(group_data['groups'])}")
    print(f"  Personas: {len(persona_data['personas'])}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()