"""Shared post-text features for the Truths notebooks.

Pass the final cleaned text, and run again after text recovery.
Missing or whitespace-only text produces missing features, not zeros.
This function does not decode HTML, clean content, or infer retruth status.
"""

import pandas as pd


TEXT_FEATURE_COLUMNS = [
    "text_length",
    "word_count",
    "hashtag_count",
    "mention_count",
    "url_count",
    "starts_with_rt",
]


# Keep the existing main-corpus patterns for comparable counts.
PATTERNS = {
    "word_count": r"\b\w+\b",
    "hashtag_count": r"(?<![\w/])#[A-Za-z0-9_]+",
    "mention_count": r"(?<![\w/])@[A-Za-z0-9_]+",
    "url_count": r"https?://[^\s<>\"']+",
}


def extract_text_features(text: pd.Series) -> pd.DataFrame:
    """Return six features, preserving the input index and leaving it unchanged.

    Length includes spaces and punctuation. Words are regex tokens (including
    numbers), not linguistic words. Hashtags and mentions use ASCII token
    characters and cannot immediately follow a word character or slash.
    Counts measure occurrences, not distinct values. starts_with_rt only
    detects an initial 'RT @' marker, case-insensitively; it is not is_retruth.
    Numeric features use nullable Int64; the marker uses nullable boolean.
    """
    if not isinstance(text, pd.Series):
        raise TypeError("text must be a pandas Series")

    values = text.astype("string")
    values = values.mask(values.str.strip().eq(""))

    result = pd.DataFrame(index=text.index)

    result["text_length"] = values.str.len().astype("Int64")

    for name, pattern in PATTERNS.items():
        result[name] = values.str.count(pattern).astype("Int64")

    result["starts_with_rt"] = values.str.match(
        r"(?i)^RT\s+@", na=pd.NA
    ).astype("boolean")

    return result[TEXT_FEATURE_COLUMNS]
