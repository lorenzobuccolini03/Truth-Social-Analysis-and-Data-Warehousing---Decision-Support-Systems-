import re
from pathlib import PurePosixPath
from urllib.parse import urlsplit


POST_COLUMNS = (
    "PostKey", "IntegratedPostID", "SourceAuthorID",
    "PublicationDate", "PublicationTime", "Category",
    "Is_Retruth", "Is_Reply", "RetruthedPostKey",
    "TextLength", "WordCount",
)
MEDIA_COLUMNS = (
    "MediaKey", "SourceMediaID", "MediaURL", "MediaFormat", "EstimatedSize",
)
BRIDGE_COLUMNS = ("PostKey", "MediaKey")

WORD_PATTERN = re.compile(r"\b\w+\b")
MENTION_PATTERN = re.compile(r"(?<![\w/])@[A-Za-z0-9_]+")
SIZE_KB = {"JPG": 400, "PNG": 2000, "GIF": 10000}
BOOLEAN_VALUES = {"true": 1, "t": 1, "1": 1, "false": 0, "f": 0, "0": 0, "": ""}


def build_post_keys(rows):
    post_keys = {}

    for post_key, row in enumerate(rows, start=1):
        integrated_id = row["id"]
        if not integrated_id or integrated_id in post_keys:
            raise ValueError(f"ID integrato mancante o duplicato: {integrated_id!r}")
        post_keys[integrated_id] = post_key

    return post_keys


def build_main_post_keys(post_keys, arff_rows, alias_rows):
    new_arff_ids = {
        row["integrated_truth_id"]
        for row in arff_rows
        if row["mapping_status"] == "new_post"
    }
    main_keys = {
        post_id: post_key
        for post_id, post_key in post_keys.items()
        if post_id not in new_arff_ids
    }

    for row in alias_rows:
        canonical_key = main_keys[row["canonical_id"]]
        original_id = row["original_id"]
        existing_key = main_keys.setdefault(original_id, canonical_key)
        if existing_key != canonical_key:
            raise ValueError(f"Mapping incompatibile per il post {original_id}")

    return main_keys


def linked_post_keys(rows, id_column, main_keys):
    return {
        main_keys[row[id_column]]
        for row in rows
        if row[id_column] in main_keys
    }


def build_media(rows, main_keys):
    media_by_id = {}
    attachments = set()
    unlinked = 0

    for row in rows:
        media_id = row["id_media"]
        url = row["media_url"]

        if media_id not in media_by_id:
            extension = PurePosixPath(urlsplit(url).path).suffix.upper()
            media_format = "JPG" if extension == ".JPEG" else extension[1:]
            size = SIZE_KB.get(media_format, "")
            media_key = len(media_by_id) + 1
            media_by_id[media_id] = (
                media_key, media_id, url, media_format if size else "Unknown", size,
            )

        post_key = main_keys.get(row["truth_id"])
        if post_key is None:
            unlinked += 1
        else:
            media_key = media_by_id[media_id][0]
            attachments.add((post_key, media_key))

    return media_by_id.values(), sorted(attachments), unlinked


def post_rows(rows, post_keys, main_keys, categories):
    yield (0, "", "", "", "", "Unknown", "", "", "", "", "")

    for row in rows:
        integrated_id = row["id"]
        post_key = post_keys[integrated_id]
        timestamp = row["timestamp"]
        is_retruth = BOOLEAN_VALUES[row["is_retruth"].strip().lower()]
        is_reply = BOOLEAN_VALUES[row["is_reply"].strip().lower()]

        retruthed_key = ""
        if is_retruth == 1:
            retruthed_key = main_keys.get(row["truth_retruthed"], "")

        text = row["text"]
        has_text = bool(text.strip())

        yield (
            post_key,
            integrated_id,
            row["author"],
            timestamp[:10],
            timestamp[11:],
            categories.get(integrated_id, "Unclassified"),
            is_retruth,
            is_reply,
            retruthed_key,
            len(text) if has_text else "",
            len(WORD_PATTERN.findall(text)) if has_text else "",
        )