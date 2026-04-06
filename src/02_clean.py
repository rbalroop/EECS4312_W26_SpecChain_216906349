"""
Cleaning steps
--------------
1. Remove duplicate reviews (by normalized text content)
2. Remove empty or whitespace-only entries
3. Remove extremely short reviews (fewer than 3 informative words after cleaning)
4. Expand common contractions before punctuation removal
5. Remove punctuation
6. Remove special characters and emojis
7. Convert numbers to words
8. Collapse extra whitespace
9. Convert text to lowercase
10. Remove only light / safe stop words
11. Apply conservative lemmatization

"""

import json
import os
import re


# ---------------------------------------------------------------------------
# Light stop words
# ---------------------------------------------------------------------------
# We intentionally keep negation words such as "not", "no", "never", "nor",
# as well as many descriptive words, because the cleaned text is intended to
# remain useful as primary evidence for Task 3.
LIGHT_STOP_WORDS = {
    "a", "an", "the",
    "and", "or", "but", "if", "because",
    "am", "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "doing",
    "have", "has", "had", "having",
    "i", "me", "my", "myself",
    "we", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself",
    "she", "her", "hers", "herself",
    "it", "its", "itself",
    "they", "them", "their", "theirs", "themselves",
    "this", "that", "these", "those",
}


# ---------------------------------------------------------------------------
# Conservative irregular lemmatization
# ---------------------------------------------------------------------------

_IRREGULAR = {
    # common app-review nouns
    "apps": "app",
    "reviews": "review",
    "features": "feature",
    "issues": "issue",
    "problems": "problem",
    "bugs": "bug",
    "notifications": "notification",
    "reminders": "reminder",
    "sessions": "session",
    "courses": "course",
    "stories": "story",
    "meditations": "meditation",
    "exercises": "exercise",
    "updates": "update",
    "payments": "payment",
    "refunds": "refund",
    "subscriptions": "subscription",
    "videos": "video",
    "audios": "audio",
    # common app-review verbs
    "works": "work",
    "worked": "work",
    "working": "work",
    "crashes": "crash",
    "crashed": "crash",
    "crashing": "crash",
    "loads": "load",
    "loaded": "load",
    "loading": "load",
    "opens": "open",
    "opened": "open",
    "opening": "open",
    "starts": "start",
    "started": "start",
    "starting": "start",
    "stops": "stop",
    "stopped": "stop",
    "stopping": "stop",
    "plays": "play",
    "played": "play",
    "playing": "play",
    "uses": "use",
    "used": "use",
    "using": "use",
    "tries": "try",
    "tried": "try",
    "trying": "try",
    "helps": "help",
    "helped": "help",
    "helping": "help",
    "recommends": "recommend",
    "recommended": "recommend",
    "recommending": "recommend",
    "sleeps": "sleep",
    "sleeping": "sleep",
    "slept": "sleep",
    "meditated": "meditate",
    "meditating": "meditate",
    "breathing": "breathe",
    "cannot": "cannot",
}


# ---------------------------------------------------------------------------
# Number-to-word conversion (covers 0 through 999,999)
# ---------------------------------------------------------------------------
_ONES = [
    "", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen",
]
_TENS = [
    "", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
    "eighty", "ninety",
]


def _number_to_words(n):
    """Convert an integer to its English word form."""
    if n < 0:
        return "negative " + _number_to_words(-n)
    if n == 0:
        return "zero"
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ("" if n % 10 == 0 else " " + _ONES[n % 10])
    if n < 1000:
        remainder = _number_to_words(n % 100)
        return _ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + remainder)
    if n < 1000000:
        remainder = _number_to_words(n % 1000)
        return (_number_to_words(n // 1000) + " thousand"
                + ("" if n % 1000 == 0 else " " + remainder))
    return str(n)


def numbers_to_text(text):
    """Replace standalone numbers in the text with their word equivalents."""
    def _replace(match):
        try:
            return _number_to_words(int(match.group(0)))
        except (ValueError, OverflowError):
            return match.group(0)
    return re.sub(r"\b\d+\b", _replace, text)


# ---------------------------------------------------------------------------
# Text normalization helpers
# ---------------------------------------------------------------------------
_CONTRACTIONS = [
    (re.compile(r"\bcan't\b", flags=re.IGNORECASE), "can not"),
    (re.compile(r"\bwon't\b", flags=re.IGNORECASE), "will not"),
    (re.compile(r"\bshan't\b", flags=re.IGNORECASE), "shall not"),
    (re.compile(r"\bain't\b", flags=re.IGNORECASE), "is not"),
    (re.compile(r"n't\b", flags=re.IGNORECASE), " not"),
    (re.compile(r"'re\b", flags=re.IGNORECASE), " are"),
    (re.compile(r"'ve\b", flags=re.IGNORECASE), " have"),
    (re.compile(r"'ll\b", flags=re.IGNORECASE), " will"),
    (re.compile(r"'d\b", flags=re.IGNORECASE), " would"),
    (re.compile(r"'m\b", flags=re.IGNORECASE), " am"),
]

_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000026FF"
    "\U0000FE00-\U0000FE0F"
    "\U0000200D"
    "\U00002194-\U000021AA"
    "\U0000203C-\U00003299"
    "]+",
    flags=re.UNICODE,
)


def expand_contractions(text):
    """Expand common English contractions before punctuation removal."""
    for pattern, replacement in _CONTRACTIONS:
        text = pattern.sub(replacement, text)
    return text


def remove_emojis(text):
    """Strip emoji and special Unicode symbols from text."""
    return _EMOJI_PATTERN.sub(" ", text)


def strip_html(text):
    """Remove very simple HTML tags if any are present."""
    return re.sub(r"<[^>]+>", " ", text)


def normalize_for_dedupe(text):
    """
    Normalize raw review text for duplicate detection only.
    We keep this lightweight because deduping should not depend on downstream cleaning.
    """
    text = (text or "").strip().lower()
    text = expand_contractions(text)
    text = re.sub(r"\s+", " ", text)
    return text


# ---------------------------------------------------------------------------
# Conservative lemmatization
# ---------------------------------------------------------------------------
def conservative_lemmatize(word):
    """
    Apply only safe, limited normalization.
    This avoids over-stemming words like 'daily' -> 'dai' or
    'everything' -> 'everyth'.
    """
    if not word:
        return word

    if word in _IRREGULAR:
        return _IRREGULAR[word]

    if len(word) <= 4:
        return word

    # plural nouns ending in -ies: stories -> story
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"

    # common plural endings: classes -> class, watches -> watch
    if word.endswith(("sses", "shes", "ches", "xes", "zes")) and len(word) > 5:
        return word[:-2]

    # general plural nouns: reviews -> review, sessions -> session
    # protect endings where stripping would usually be wrong
    if word.endswith("s") and len(word) > 4 and not word.endswith(("ss", "us", "is")):
        return word[:-1]

    return word


# ---------------------------------------------------------------------------
# Main cleaning function
# ---------------------------------------------------------------------------
def clean_text(text):
    """Apply the text-cleaning pipeline while preserving useful phrasing."""
    if not text or not text.strip():
        return ""

    text = text.lower()
    text = strip_html(text)
    text = expand_contractions(text)
    text = numbers_to_text(text)
    text = remove_emojis(text)

    # Remove URLs / emails / leftover markup-like fragments.
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"\b\S+@\S+\b", " ", text)

    # Remove punctuation / special characters.
    # Keep letters, digits, and whitespace only.
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Collapse extra whitespace early.
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""

    tokens = []
    for token in text.split():
        if token in LIGHT_STOP_WORDS:
            continue
        token = conservative_lemmatize(token)
        if token:
            tokens.append(token)

    return " ".join(tokens)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    raw_path = os.path.join(project_root, "data", "reviews_raw.jsonl")
    clean_path = os.path.join(project_root, "data", "reviews_clean.jsonl")

    if not os.path.exists(raw_path):
        print(f"[ERROR] Raw dataset not found at {raw_path}")
        return

    # Load raw reviews
    raw_reviews = []
    with open(raw_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                raw_reviews.append(json.loads(line))

    total_raw = len(raw_reviews)
    print(f"[INFO] Loaded {total_raw} raw reviews.")

    # --- Step 1: Remove duplicates (by normalized review text) ---
    seen_texts = set()
    unique_reviews = []
    duplicates_removed = 0
    for review in raw_reviews:
        text = review.get("text", "")
        norm = normalize_for_dedupe(text)
        if not norm:
            unique_reviews.append(review)
            continue
        if norm in seen_texts:
            duplicates_removed += 1
            continue
        seen_texts.add(norm)
        unique_reviews.append(review)
    print(f"[INFO] Removed {duplicates_removed} duplicate reviews.")

    # --- Step 2: Remove empty / whitespace-only entries ---
    non_empty = []
    empty_removed = 0
    for review in unique_reviews:
        text = (review.get("text", "") or "").strip()
        if not text or text in {".", "..", "..."}:
            empty_removed += 1
            continue
        non_empty.append(review)
    print(f"[INFO] Removed {empty_removed} empty/whitespace entries.")

    # --- Steps 3-11: Clean text and filter short reviews ---
    cleaned_reviews = []
    short_removed = 0
    min_word_count = 3

    for review in non_empty:
        original_text = review.get("text", "")
        cleaned = clean_text(original_text)

        word_count = len(cleaned.split()) if cleaned else 0
        if word_count < min_word_count:
            short_removed += 1
            continue

        cleaned_reviews.append({
            "review_id": f"clean_{len(cleaned_reviews):05d}",
            "original_review_id": review.get("review_id", ""),
            "app_name": review.get("app_name", ""),
            "reviewer": review.get("reviewer", ""),
            "rating": review.get("rating", 0),
            "original_text": original_text,
            "cleaned_text": cleaned,
            "date": review.get("date", ""),
            "thumbs_up": review.get("thumbs_up", 0),
            "app_version": review.get("app_version", ""),
        })

    print(f"[INFO] Removed {short_removed} short reviews "
          f"(< {min_word_count} words after cleaning).")

    # --- Write cleaned dataset ---
    os.makedirs(os.path.dirname(clean_path), exist_ok=True)
    with open(clean_path, "w", encoding="utf-8") as f:
        for review in cleaned_reviews:
            f.write(json.dumps(review, ensure_ascii=False) + "\n")

    # --- Print summary ---
    total_clean = len(cleaned_reviews)
    retention = (total_clean / total_raw * 100.0) if total_raw else 0.0

    print(f"\n{'=' * 50}")
    print("  Cleaning Summary")
    print(f"{'=' * 50}")
    print(f"  Raw reviews loaded:      {total_raw}")
    print(f"  Duplicates removed:      {duplicates_removed}")
    print(f"  Empty entries removed:   {empty_removed}")
    print(f"  Short reviews removed:   {short_removed}")
    print(f"  Final cleaned reviews:   {total_clean}")
    print(f"  Retention rate:          {retention:.1f}%")
    print(f"{'=' * 50}")
    print(f"  Output saved to: {clean_path}")


if __name__ == "__main__":
    main()