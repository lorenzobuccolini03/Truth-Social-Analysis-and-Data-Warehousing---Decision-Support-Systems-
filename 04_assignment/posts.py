import re
from pathlib import PurePosixPath
from urllib.parse import urlsplit


POST_COLUMNS = (
    "IntegratedPostID",
    "PublicationDate", "PublicationTime", "Category",
    "Is_Retruth", "Is_Reply", "RetruthedIntegratedPostID",
    "IsRetruthOfTrump", "TextLength", "WordCount", "PNGCount", "JPGCount", "GIFCount",
)

WORD_PATTERN = re.compile(r"\b\w+\b")
MEDIA_FORMAT_INDEX = {"PNG": 0, "JPG": 1, "GIF": 2}
BOOLEAN_VALUES = {"true": 1, "t": 1, "1": 1, "false": 0, "f": 0, "0": 0, "": ""}


def index_posts(rows):
    post_authors = {}
    retruth_references = {}

    for row in rows:
        integrated_id = row["id"]
        if not integrated_id or integrated_id in post_authors:
            raise ValueError(f"ID integrato mancante o duplicato: {integrated_id!r}")
        post_authors[integrated_id] = row["author"]
        if BOOLEAN_VALUES[row["is_retruth"].strip().lower()] == 1:
            retruth_references[integrated_id] = row["truth_retruthed"]

    return post_authors, retruth_references


def build_main_post_ids(post_ids, arff_rows, alias_rows):
    new_arff_ids = {
        row["integrated_truth_id"]
        for row in arff_rows
        if row["mapping_status"] == "new_post"
    }
    main_ids = {
        post_id: post_id
        for post_id in post_ids
        if post_id not in new_arff_ids
    }

    for row in alias_rows:
        canonical_id = main_ids[row["canonical_id"]]
        original_id = row["original_id"]
        existing_id = main_ids.setdefault(original_id, canonical_id)
        if existing_id != canonical_id:
            raise ValueError(f"Mapping incompatibile per il post {original_id}")

    return main_ids


def classify_retruths(retruth_references, main_ids, post_authors, trump_user_id):
    flags = {}

    for post_id in retruth_references:
        path = set()
        target = post_id
        while target in retruth_references and target not in flags and target not in path:
            path.add(target)
            target = main_ids.get(retruth_references[target])

        if target in flags:
            flag = flags[target]
        elif target in path:
            flag = None
        else:
            author = post_authors.get(target, "").strip()
            flag = int(int(author) == trump_user_id) if author.isdecimal() and int(author) > 0 else None
        flags.update(dict.fromkeys(path, flag))

    return flags


def count_media_by_post(rows, main_ids):
    format_by_media = {}
    seen_attachments = set()
    counts_by_post = {}
    unlinked = 0

    for row in rows:
        media_id = row["id_media"]
        if media_id not in format_by_media:
            extension = PurePosixPath(urlsplit(row["media_url"]).path).suffix.upper()
            media_format = "JPG" if extension == ".JPEG" else extension[1:]
            format_by_media[media_id] = MEDIA_FORMAT_INDEX.get(media_format)

        integrated_id = main_ids.get(row["truth_id"])
        if integrated_id is None:
            unlinked += 1
            continue

        format_index = format_by_media[media_id]
        attachment = (integrated_id, media_id)
        if format_index is not None and attachment not in seen_attachments:
            seen_attachments.add(attachment)
            counts = counts_by_post.setdefault(integrated_id, [0, 0, 0])
            counts[format_index] += 1

    return counts_by_post, unlinked


def post_rows(rows, main_ids, categories, media_counts, retruth_flags):
    yield ("", "", "", "Unknown", "", "", "", "", "", "", "", "", "")

    for row in rows:
        integrated_id = row["id"]
        timestamp = row["timestamp"]
        is_retruth = BOOLEAN_VALUES[row["is_retruth"].strip().lower()]
        is_reply = BOOLEAN_VALUES[row["is_reply"].strip().lower()]

        retruthed_id = ""
        if is_retruth == 1:
            retruthed_id = main_ids.get(row["truth_retruthed"], "")

        text = row["text"]
        has_text = bool(text.strip())

        yield (
            integrated_id,
            timestamp[:10],
            timestamp[11:],
            categories.get(integrated_id, "Unclassified"),
            is_retruth,
            is_reply,
            retruthed_id,
            retruth_flags.get(integrated_id),
            len(text) if has_text else "",
            len(WORD_PATTERN.findall(text)) if has_text else "",
            *media_counts.get(integrated_id, (0, 0, 0)),
        )
