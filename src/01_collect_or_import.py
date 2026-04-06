from __future__ import annotations

import argparse
import json
import math
import os
import time
from collections import Counter, deque
from datetime import date, datetime
from typing import Any, Deque, Dict, Iterable, List, Optional, Tuple


DEFAULT_APP_ID = "com.getsomeheadspace.android"
DEFAULT_TARGET_COUNT = 2500
DEFAULT_CANDIDATE_COUNT = 5000
DEFAULT_OUTPUT_JSONL = os.path.join("data", "reviews_raw.jsonl")


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def project_root_from_script() -> str:
    """Resolve the project root assuming this file lives in src/."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(script_dir)


def resolve_project_path(path: str, project_root: str) -> str:
    """Resolve a path relative to the project root unless it is already absolute."""
    if os.path.isabs(path):
        return path
    return os.path.join(project_root, path)


def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def to_iso_string(value: Any) -> str:
    """Convert datetimes/dates/other values to a stable string form."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value).strip()


def to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def pick(record: Dict[str, Any], *keys: str, default: Any = "") -> Any:
    """Return the first present, non-None value from a record."""
    for key in keys:
        if key in record and record[key] is not None:
            return record[key]
    return default


def normalize_text_for_dedupe(text: str) -> str:
    """Normalize text just enough to catch obvious duplicate reviews."""
    text = (text or "").strip().lower()
    return " ".join(text.split())


# ---------------------------------------------------------------------------
# Review normalization
# ---------------------------------------------------------------------------

def normalize_scraped_review(
    raw: Dict[str, Any],
    *,
    app_name: str,
    app_id: str,
    collection_strategy: str,
    source_sort: str,
    source_rating_filter: Optional[int],
) -> Dict[str, Any]:
    """Map google-play-scraper review fields into the raw schema used by 02_clean.py."""
    review_id = str(raw.get("reviewId") or "").strip()
    text = str(raw.get("content") or "").strip()

    return {
        "review_id": review_id,
        "app_id": app_id,
        "app_name": app_name,
        "reviewer": str(raw.get("userName") or "").strip(),
        "rating": to_int(raw.get("score"), 0),
        "text": text,
        "date": to_iso_string(raw.get("at")),
        "thumbs_up": to_int(raw.get("thumbsUpCount"), 0),
        "app_version": str(raw.get("appVersion") or raw.get("reviewCreatedVersion") or "").strip(),
        #  extra fields for traceability/debugging
        "reply_content": str(raw.get("replyContent") or "").strip(),
        "reply_date": to_iso_string(raw.get("repliedAt")),
        "review_created_version": str(raw.get("reviewCreatedVersion") or "").strip(),
        "source": "google_play_scraper",
        "collection_strategy": collection_strategy,
        "source_sort": source_sort,
        "source_rating_filter": source_rating_filter,
    }


def normalize_imported_review(
    raw: Dict[str, Any],
    *,
    app_name: str,
    app_id: str,
    fallback_index: int,
) -> Dict[str, Any]:
    """Normalize a review imported from an arbitrary JSON/JSONL structure."""
    review_id = str(
        pick(raw, "review_id", "reviewId", "id", default=f"import_{fallback_index:05d}")
    ).strip() or f"import_{fallback_index:05d}"

    text = str(
        pick(raw, "text", "content", "review", "review_text", "body", default="")
    ).strip()

    return {
        "review_id": review_id,
        "app_id": str(pick(raw, "app_id", "appId", default=app_id)).strip() or app_id,
        "app_name": str(pick(raw, "app_name", "appName", default=app_name)).strip() or app_name,
        "reviewer": str(pick(raw, "reviewer", "userName", "author", "user", default="")).strip(),
        "rating": to_int(pick(raw, "rating", "score", "stars", default=0), 0),
        "text": text,
        "date": to_iso_string(pick(raw, "date", "at", "review_date", default="")),
        "thumbs_up": to_int(pick(raw, "thumbs_up", "thumbsUpCount", "likes", default=0), 0),
        "app_version": str(
            pick(raw, "app_version", "appVersion", "reviewCreatedVersion", default="")
        ).strip(),
        "reply_content": str(pick(raw, "reply_content", "replyContent", default="")).strip(),
        "reply_date": to_iso_string(pick(raw, "reply_date", "repliedAt", default="")),
        "review_created_version": str(pick(raw, "reviewCreatedVersion", default="")).strip(),
        "source": str(pick(raw, "source", default="import")).strip() or "import",
        "collection_strategy": str(pick(raw, "collection_strategy", default="import")).strip() or "import",
        "source_sort": str(pick(raw, "source_sort", default="")).strip(),
        "source_rating_filter": pick(raw, "source_rating_filter", default=None),
    }


# ---------------------------------------------------------------------------
# Input/output
# ---------------------------------------------------------------------------

def load_json_or_jsonl(path: str) -> List[Dict[str, Any]]:
    """Load a JSON array / wrapped JSON object / JSONL file into a list of dicts."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")

    _, ext = os.path.splitext(path.lower())

    if ext == ".jsonl":
        records: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    raise ValueError(f"JSONL line {line_no} is not a JSON object.")
                records.append(obj)
        return records

    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        for key in ("reviews", "items", "data", "results"):
            if isinstance(payload.get(key), list):
                records = payload[key]
                break
        else:
            raise ValueError(
                "JSON import file must be a list of review objects, or a dict containing "
                "a list under one of: reviews, items, data, results."
            )
    else:
        raise ValueError("Unsupported input format: expected JSON list/dict or JSONL.")

    if not all(isinstance(item, dict) for item in records):
        raise ValueError("Imported review collection must contain only JSON objects.")

    return records


def write_jsonl(records: Iterable[Dict[str, Any]], path: str) -> None:
    ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_json_array(records: List[Dict[str, Any]], path: str) -> None:
    ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Deduping and selection
# ---------------------------------------------------------------------------

def dedupe_records(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Remove duplicates using review_id when available, otherwise normalized review text.
    This is stricter than deduping only on review_id because the same review can appear
    in multiple collection passes (different sorts / rating filters).
    """
    seen_ids = set()
    seen_texts = set()
    deduped: List[Dict[str, Any]] = []
    duplicates_removed = 0

    for record in records:
        review_id = str(record.get("review_id") or "").strip()
        text_key = normalize_text_for_dedupe(str(record.get("text") or ""))

        duplicate = False
        if review_id and review_id in seen_ids:
            duplicate = True
        elif text_key and text_key in seen_texts:
            duplicate = True

        if duplicate:
            duplicates_removed += 1
            continue

        if review_id:
            seen_ids.add(review_id)
        if text_key:
            seen_texts.add(text_key)
        deduped.append(record)

    return deduped, duplicates_removed


def rating_distribution(records: List[Dict[str, Any]]) -> Dict[int, int]:
    counts: Dict[int, int] = Counter()
    for record in records:
        rating = to_int(record.get("rating"), 0)
        if rating:
            counts[rating] += 1
    return dict(sorted(counts.items()))


def print_rating_distribution(title: str, records: List[Dict[str, Any]]) -> None:
    counts = rating_distribution(records)
    total = len(records)
    print(f"[INFO] {title}")
    if total == 0:
        print("[INFO]   (no reviews)")
        return
    for rating in range(1, 6):
        count = counts.get(rating, 0)
        pct = (count / total) * 100 if total else 0.0
        print(f"[INFO]   {rating}-star: {count:4d} ({pct:5.1f}%)")


def sort_records_for_selection(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort by newest date first, then helpful votes descending."""
    return sorted(
        records,
        key=lambda r: (
            str(r.get("date") or ""),
            to_int(r.get("thumbs_up"), 0),
        ),
        reverse=True,
    )


def select_balanced_reviews(records: List[Dict[str, Any]], target_count: int) -> List[Dict[str, Any]]:
    """
    Soft-balance the final dataset by rating.
    Strategy:
    1. Split by rating.
    2. Take an even base quota across available star buckets.
    3. Fill any remaining slots round-robin from buckets with leftovers.

    This gives a more representative dataset for manual review work without
    discarding too much usable material.
    """
    if target_count <= 0 or not records:
        return []

    buckets: Dict[int, List[Dict[str, Any]]] = {rating: [] for rating in range(1, 6)}
    unrated: List[Dict[str, Any]] = []

    for record in records:
        rating = to_int(record.get("rating"), 0)
        if rating in buckets:
            buckets[rating].append(record)
        else:
            unrated.append(record)

    for rating in buckets:
        buckets[rating] = sort_records_for_selection(buckets[rating])
    unrated = sort_records_for_selection(unrated)

    available_ratings = [rating for rating in range(1, 6) if buckets[rating]]
    if not available_ratings:
        return sort_records_for_selection(records)[:target_count]

    selected: List[Dict[str, Any]] = []
    used_ids = set()

    base_quota = target_count // len(available_ratings)

    remainders: Dict[int, Deque[Dict[str, Any]]] = {}
    for rating in available_ratings:
        bucket = buckets[rating]
        take_n = min(base_quota, len(bucket))
        for record in bucket[:take_n]:
            review_id = str(record.get("review_id") or "")
            if review_id and review_id in used_ids:
                continue
            if review_id:
                used_ids.add(review_id)
            selected.append(record)
        remainders[rating] = deque(bucket[take_n:])

    # Fill remaining slots round-robin across star ratings.
    rating_order = [5, 4, 3, 2, 1]
    while len(selected) < target_count:
        progressed = False
        for rating in rating_order:
            queue = remainders.get(rating)
            if not queue:
                continue
            while queue:
                record = queue.popleft()
                review_id = str(record.get("review_id") or "")
                if review_id and review_id in used_ids:
                    continue
                if review_id:
                    used_ids.add(review_id)
                selected.append(record)
                progressed = True
                break
            if len(selected) >= target_count:
                break
        if not progressed:
            break

    # Final backfill from unrated / odd leftovers if target_count still not met.
    if len(selected) < target_count:
        leftovers: List[Dict[str, Any]] = []
        for queue in remainders.values():
            leftovers.extend(list(queue))
        leftovers.extend(unrated)
        leftovers = sort_records_for_selection(leftovers)
        for record in leftovers:
            review_id = str(record.get("review_id") or "")
            if review_id and review_id in used_ids:
                continue
            if review_id:
                used_ids.add(review_id)
            selected.append(record)
            if len(selected) >= target_count:
                break

    return selected[:target_count]


# ---------------------------------------------------------------------------
# Collection mode
# ---------------------------------------------------------------------------

def fetch_review_bucket(
    *,
    app_id: str,
    app_name: str,
    lang: str,
    country: str,
    sort_name: str,
    sort_value: Any,
    target_count: int,
    filter_score_with: Optional[int],
    sleep_milliseconds: int,
) -> List[Dict[str, Any]]:
    """Fetch one logical bucket of reviews from Google Play."""
    from google_play_scraper import reviews

    collected: List[Dict[str, Any]] = []
    continuation_token = None

    while len(collected) < target_count:
        remaining = target_count - len(collected)
        request_count = min(200, remaining)

        kwargs: Dict[str, Any] = {
            "lang": lang,
            "country": country,
            "sort": sort_value,
            "count": request_count,
        }
        if continuation_token is not None:
            kwargs["continuation_token"] = continuation_token
        if filter_score_with is not None:
            kwargs["filter_score_with"] = filter_score_with

        batch, continuation_token = reviews(app_id, **kwargs)
        if not batch:
            break

        normalized = [
            normalize_scraped_review(
                item,
                app_name=app_name,
                app_id=app_id,
                collection_strategy="balanced" if filter_score_with is not None else "single_sort",
                source_sort=sort_name,
                source_rating_filter=filter_score_with,
            )
            for item in batch
        ]
        collected.extend(normalized)

        if continuation_token is None:
            break

        if sleep_milliseconds > 0:
            time.sleep(sleep_milliseconds / 1000.0)

    return collected


def collect_single_sort(
    *,
    app_id: str,
    lang: str,
    country: str,
    sort_name: str,
    target_count: int,
    sleep_milliseconds: int,
    app_name_override: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], str]:
    """Original single-sort collection mode."""
    try:
        from google_play_scraper import Sort, app
    except ImportError as exc:
        raise SystemExit(
            "[ERROR] Collection mode requires the google-play-scraper package.\n"
            "Install it with: pip install google-play-scraper"
        ) from exc

    sort_map = {
        "newest": Sort.NEWEST,
        "most_relevant": Sort.MOST_RELEVANT,
    }
    sort_value = sort_map[sort_name]

    app_info = app(app_id, lang=lang, country=country)
    app_name = app_name_override or str(app_info.get("title") or app_id)

    print(f"[INFO] App ID:    {app_id}")
    print(f"[INFO] App name:  {app_name}")
    print(f"[INFO] Strategy:  single_sort")
    print(f"[INFO] Sort:      {sort_name}")
    print(f"[INFO] Target:    {target_count} reviews")

    records = fetch_review_bucket(
        app_id=app_id,
        app_name=app_name,
        lang=lang,
        country=country,
        sort_name=sort_name,
        sort_value=sort_value,
        target_count=target_count,
        filter_score_with=None,
        sleep_milliseconds=sleep_milliseconds,
    )
    return records, app_name


def collect_balanced(
    *,
    app_id: str,
    lang: str,
    country: str,
    candidate_count: int,
    target_count: int,
    sleep_milliseconds: int,
    app_name_override: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], str, List[Dict[str, Any]], int]:
    """
    Inspect a broader candidate pool across both sorts and all rating filters,
    then output a more balanced final dataset.
    """
    try:
        from google_play_scraper import Sort, app
    except ImportError as exc:
        raise SystemExit(
            "[ERROR] Collection mode requires the google-play-scraper package.\n"
            "Install it with: pip install google-play-scraper"
        ) from exc

    app_info = app(app_id, lang=lang, country=country)
    app_name = app_name_override or str(app_info.get("title") or app_id)

    sort_specs = [
        ("newest", Sort.NEWEST),
        ("most_relevant", Sort.MOST_RELEVANT),
    ]
    ratings = [5, 4, 3, 2, 1]
    bucket_count = len(sort_specs) * len(ratings)
    per_bucket_target = max(50, math.ceil(candidate_count / bucket_count))

    print(f"[INFO] App ID:            {app_id}")
    print(f"[INFO] App name:          {app_name}")
    print(f"[INFO] Strategy:          balanced")
    print(f"[INFO] Candidate target:  {candidate_count}")
    print(f"[INFO] Output target:     {target_count}")
    print(f"[INFO] Per-bucket target: {per_bucket_target}")
    print(f"[INFO] Language:          {lang}")
    print(f"[INFO] Country:           {country}")

    candidate_records: List[Dict[str, Any]] = []

    for sort_name, sort_value in sort_specs:
        for rating in ratings:
            print(f"[INFO] Collecting bucket: sort={sort_name}, rating={rating}")
            bucket = fetch_review_bucket(
                app_id=app_id,
                app_name=app_name,
                lang=lang,
                country=country,
                sort_name=sort_name,
                sort_value=sort_value,
                target_count=per_bucket_target,
                filter_score_with=rating,
                sleep_milliseconds=sleep_milliseconds,
            )
            print(f"[INFO]   fetched {len(bucket)} reviews")
            candidate_records.extend(bucket)

    # Backfill with an unfiltered newest pass if the candidate pool is still thin.
    if len(candidate_records) < candidate_count:
        deficit = candidate_count - len(candidate_records)
        print(f"[INFO] Backfilling with unfiltered newest reviews ({deficit} requested)")
        candidate_records.extend(
            fetch_review_bucket(
                app_id=app_id,
                app_name=app_name,
                lang=lang,
                country=country,
                sort_name="newest",
                sort_value=Sort.NEWEST,
                target_count=deficit,
                filter_score_with=None,
                sleep_milliseconds=sleep_milliseconds,
            )
        )

    deduped_candidates, candidate_duplicates_removed = dedupe_records(candidate_records)
    print(f"[INFO] Candidate duplicates removed: {candidate_duplicates_removed}")
    print_rating_distribution("Candidate rating distribution:", deduped_candidates)

    selected = select_balanced_reviews(deduped_candidates, target_count)
    print_rating_distribution("Selected rating distribution:", selected)

    return selected, app_name, deduped_candidates, candidate_duplicates_removed


# ---------------------------------------------------------------------------
# Import mode
# ---------------------------------------------------------------------------

def import_reviews(
    *,
    input_path: str,
    app_id: str,
    app_name: str,
) -> List[Dict[str, Any]]:
    imported = load_json_or_jsonl(input_path)
    normalized: List[Dict[str, Any]] = []
    for idx, raw in enumerate(imported):
        normalized.append(
            normalize_imported_review(
                raw,
                app_name=app_name,
                app_id=app_id,
                fallback_index=idx,
            )
        )
    return normalized


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Collect Google Play reviews or import an existing review file, then write "
            "the normalized raw dataset to data/reviews_raw.jsonl."
        )
    )

    parser.add_argument(
        "--mode",
        choices=["collect", "import"],
        default="collect",
        help="Use 'collect' to scrape Google Play, or 'import' to normalize an existing file.",
    )
    parser.add_argument(
        "--collection-strategy",
        choices=["balanced", "single_sort"],
        default="balanced",
        help=(
            "balanced: inspect a larger candidate pool across rating buckets and both review sorts, "
            "then output a softer-balanced dataset. "
            "single_sort: collect one stream only (legacy behavior)."
        ),
    )
    parser.add_argument(
        "--app-id",
        default=DEFAULT_APP_ID,
        help="Google Play package name. Default is Headspace.",
    )
    parser.add_argument(
        "--app-name",
        default="",
        help=(
            "Optional app display name override. Leave blank to use the Play Store title in "
            "collection mode, or the app ID in import mode."
        ),
    )
    parser.add_argument(
        "--target-count",
        type=int,
        default=DEFAULT_TARGET_COUNT,
        help="How many reviews to write to the final raw dataset.",
    )
    parser.add_argument(
        "--candidate-count",
        type=int,
        default=DEFAULT_CANDIDATE_COUNT,
        help=(
            "How many reviews to inspect internally in balanced collection mode before "
            "selecting the final output set."
        ),
    )
    parser.add_argument(
        "--lang",
        default="en",
        help="Language code for Google Play collection mode.",
    )
    parser.add_argument(
        "--country",
        default="us",
        help="Country code for Google Play collection mode.",
    )
    parser.add_argument(
        "--sort",
        choices=["newest", "most_relevant"],
        default="newest",
        help="Review ordering for single_sort collection mode.",
    )
    parser.add_argument(
        "--sleep-milliseconds",
        type=int,
        default=0,
        help="Delay between Google Play requests. Increase this if you want gentler scraping.",
    )
    parser.add_argument(
        "--input",
        default=None,
        help="Path to an existing JSON or JSONL file when using --mode import.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_JSONL,
        help="Output JSONL path. Relative paths are resolved from the project root.",
    )
    parser.add_argument(
        "--also-write-json",
        default=None,
        help="Optional extra JSON-array output path, e.g. data/reviews_raw.json",
    )
    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.target_count <= 0:
        raise SystemExit("[ERROR] --target-count must be a positive integer.")
    if args.candidate_count <= 0:
        raise SystemExit("[ERROR] --candidate-count must be a positive integer.")
    if args.mode == "collect" and args.collection_strategy == "balanced":
        if args.candidate_count < args.target_count:
            raise SystemExit("[ERROR] In balanced mode, --candidate-count must be >= --target-count.")

    project_root = project_root_from_script()
    output_jsonl = resolve_project_path(args.output, project_root)
    output_json = (
        resolve_project_path(args.also_write_json, project_root)
        if args.also_write_json
        else None
    )

    candidate_pool_size: Optional[int] = None
    duplicates_removed = 0

    if args.mode == "import":
        if not args.input:
            raise SystemExit("[ERROR] --input is required when --mode import is used.")
        input_path = resolve_project_path(args.input, project_root)
        print(f"[INFO] Importing reviews from: {input_path}")
        import_app_name = args.app_name.strip() or args.app_id
        records = import_reviews(
            input_path=input_path,
            app_id=args.app_id,
            app_name=import_app_name,
        )
        records, duplicates_removed = dedupe_records(records)
        app_name_used = import_app_name
    else:
        if args.collection_strategy == "balanced":
            records, app_name_used, candidate_pool, duplicates_removed = collect_balanced(
                app_id=args.app_id,
                lang=args.lang,
                country=args.country,
                candidate_count=args.candidate_count,
                target_count=args.target_count,
                sleep_milliseconds=args.sleep_milliseconds,
                app_name_override=args.app_name.strip() or None,
            )
            candidate_pool_size = len(candidate_pool)
        else:
            raw_records, app_name_used = collect_single_sort(
                app_id=args.app_id,
                lang=args.lang,
                country=args.country,
                sort_name=args.sort,
                target_count=args.target_count,
                sleep_milliseconds=args.sleep_milliseconds,
                app_name_override=args.app_name.strip() or None,
            )
            records, duplicates_removed = dedupe_records(raw_records)

    write_jsonl(records, output_jsonl)
    if output_json is not None:
        write_json_array(records, output_json)

    print("\n" + "=" * 64)
    print("Raw Review Collection / Import Summary")
    print("=" * 64)
    print(f"Mode:                     {args.mode}")
    if args.mode == "collect":
        print(f"Collection strategy:      {args.collection_strategy}")
    print(f"App name:                 {app_name_used}")
    print(f"App ID:                   {args.app_id}")
    if candidate_pool_size is not None:
        print(f"Candidate pool inspected: {candidate_pool_size}")
    print(f"Reviews written:          {len(records)}")
    print(f"Duplicates removed:       {duplicates_removed}")
    print(f"JSONL output:             {output_jsonl}")
    if output_json is not None:
        print(f"JSON output:              {output_json}")
    print("=" * 64)
    print_rating_distribution("Final output rating distribution:", records)

    if args.mode == "collect" and len(records) < args.target_count:
        print(
            "[WARN] Fewer reviews were written than requested. This can happen because of "
            "Google Play availability, pagination limits, rating-bucket sparsity, or duplicates."
        )


if __name__ == "__main__":
    main()