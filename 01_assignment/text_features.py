"""Shared post-text features for the Truths notebooks.

Pass the final cleaned text, and run again after text recovery.
Missing or whitespace-only text produces missing features, not zeros.
This module does not decode HTML, clean content, or infer retruth status.

Entity extraction uses spaCy English NER (GPE/LOC/FAC for locations,
ORG for organizations). Entity lists are JSON strings for reliable CSV export.
"""

import json
from functools import lru_cache

import pandas as pd


TEXT_FEATURE_COLUMNS = [
    "text_length",
    "word_count",
    "hashtag_count",
    "mention_count",
    "url_count",
    "starts_with_rt",
    "mentioned_locations",
    "mentioned_organizations",
    "locations_count",
    "organizations_count",
    "has_location",
    "has_organization",
]


# Keep the existing main-corpus patterns for comparable counts.
PATTERNS = {
    "word_count": r"\b\w+\b",
    "hashtag_count": r"(?<![\w/])#[A-Za-z0-9_]+",
    "mention_count": r"(?<![\w/])@[A-Za-z0-9_]+",
    "url_count": r"https?://[^\s<>\"']+",
}


@lru_cache(maxsize=1)
def _get_ner_model():
    """Load the NER model only once, when the extraction is first requested."""
    try:
        import spacy
    except ImportError as exc:
        raise ImportError(
            "spaCy is required for named entity extraction. Install it with: "
            "pip install spacy"
        ) from exc

    try:
        nlp = spacy.load("en_core_web_sm", exclude=[
            "parser", "tagger", "lemmatizer", "attribute_ruler"
        ])
    except OSError as exc:
        raise RuntimeError(
            "English spaCy model not installed. Run: "
            "python -m spacy download en_core_web_sm"
        ) from exc
    return nlp


def extract_text_features(text: pd.Series, *, ner_batch_size: int = 128) -> pd.DataFrame:
    """Return regex and NER features, preserving the input index.

    Original six features retain their prior definitions and nullable dtypes.
    NER lists are stored as JSON arrays (strings) to survive CSV round-trips.
    Duplicate entity names within the same post are counted just once, with
    order preserved. Missing/blank text produces NA, while text containing
    no recognized entities produces '[]', zero counts, and False flags.
    """
    if not isinstance(text, pd.Series):
        raise TypeError("text must be a pandas Series")
    if not isinstance(ner_batch_size, int) or ner_batch_size < 1:
        raise ValueError("ner_batch_size must be a positive integer")

    values = text.astype("string")
    values = values.mask(values.str.strip().eq(""))

    result = pd.DataFrame(index=text.index)
    result["text_length"] = values.str.len().astype("Int64")

    for name, pattern in PATTERNS.items():
        result[name] = values.str.count(pattern).astype("Int64")

    result["starts_with_rt"] = values.str.match(
        r"(?i)^RT\s+@", na=pd.NA
    ).astype("boolean")

    size = len(values)
    locations = [pd.NA] * size
    organizations = [pd.NA] * size
    location_counts = [pd.NA] * size
    organization_counts = [pd.NA] * size
    has_locations = [pd.NA] * size
    has_organizations = [pd.NA] * size

    if values.notna().any():
        nlp = _get_ner_model()
        # Pass (text, row position) to retain alignment even with repeated indices.
        valid_texts = (
            (str(value), position)
            for position, value in enumerate(values.array)
            if not pd.isna(value)
        )
        for doc, position in nlp.pipe(
            valid_texts, as_tuples=True, batch_size=ner_batch_size
        ):
            locs = list(dict.fromkeys(
                ent.text.strip()
                for ent in doc.ents
                if ent.label_ in {"GPE", "LOC", "FAC"} and ent.text.strip()
            ))
            orgs = list(dict.fromkeys(
                ent.text.strip()
                for ent in doc.ents
                if ent.label_ == "ORG" and ent.text.strip()
            ))
            locations[position] = json.dumps(locs, ensure_ascii=False)
            organizations[position] = json.dumps(orgs, ensure_ascii=False)
            location_counts[position] = len(locs)
            organization_counts[position] = len(orgs)
            has_locations[position] = bool(locs)
            has_organizations[position] = bool(orgs)

    # Assign by position, not by index label (indices may contain duplicates).
    result["mentioned_locations"] = pd.array(locations, dtype="string")
    result["mentioned_organizations"] = pd.array(organizations, dtype="string")
    result["locations_count"] = pd.array(location_counts, dtype="Int64")
    result["organizations_count"] = pd.array(organization_counts, dtype="Int64")
    result["has_location"] = pd.array(has_locations, dtype="boolean")
    result["has_organization"] = pd.array(has_organizations, dtype="boolean")

    return result[TEXT_FEATURE_COLUMNS]
