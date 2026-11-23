import csv
import gzip
from datetime import date
from pathlib import Path

import dimensions
import events
import posts


ASSIGNMENT_DIR = Path(__file__).resolve().parent
SOURCE_DIR = ASSIGNMENT_DIR.parent / "01_assignment"
OUTPUT_DIR = ASSIGNMENT_DIR / "output"

POSTS_FILE = SOURCE_DIR / "output_additional_truths" / "truths_integrated.csv.gz"
EVENTS_FILE = SOURCE_DIR / "output_events" / "events_integrated.csv.gz"
USERS_FILE = SOURCE_DIR / "output_users" / "users_clean.csv"
ARFF_MAPPING_FILE = SOURCE_DIR / "output_additional_truths" / "arff_truth_id_mapping.csv"


def read_csv(path):
    open_file = gzip.open if path.suffix == ".gz" else open

    with open_file(path, "rt", encoding="utf-8-sig", newline="") as file:
        yield from csv.DictReader(file)


def calendar_bounds(*paths):
    earliest = date.max
    latest = date.min

    for path in paths:
        for row in read_csv(path):
            timestamp = row["timestamp"]
            if timestamp:
                current = date.fromisoformat(timestamp[:10])
                earliest = min(earliest, current)
                latest = max(latest, current)

    if earliest > latest:
        raise ValueError("Non ci sono date nei file di input.")

    return date(earliest.year, 1, 1), date(latest.year, 12, 31)


def write_csv(path, header, rows):
    count = 0
    temporary_path = path.with_suffix(".tmp")

    with temporary_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(header)

        for count, row in enumerate(rows, start=1):
            writer.writerow(row)

    temporary_path.replace(path)
    print(f"{path.name}: {count} righe")


def export_posts_and_media():
    post_keys = posts.build_post_keys(read_csv(POSTS_FILE))
    alias_file = SOURCE_DIR / "truth_id_map.csv"

    aliases = read_csv(alias_file) if alias_file.is_file() else ()
    if not alias_file.is_file():
        print("Mappa degli alias assente: uso i collegamenti main diretti.")

    main_keys = posts.build_main_post_keys(post_keys, read_csv(ARFF_MAPPING_FILE), aliases)

    user_keys = {
        row["SourceUserID"]: int(row["UserKey"])
        for row in read_csv(OUTPUT_DIR / "DimUser.csv")
        if row["SourceUserID"]
    }

    category_file = ASSIGNMENT_DIR.parent / "02_assignment" / "output" / "post_categories.csv"
    categories = {}
    if category_file.is_file():
        categories = {
            row["IntegratedPostID"]: row["Category"].strip()
            for row in read_csv(category_file)
            if row["Category"].strip()
        }
    else:
        print("Categorie dell'Assignment 2 assenti: Category = Unclassified.")

    media_file = SOURCE_DIR / "output_media" / "media_clean.csv.gz"
    media_rows, attachments, unlinked = posts.build_media(read_csv(media_file), main_keys)


    write_csv(
        OUTPUT_DIR / "DimPost.csv",
        posts.POST_COLUMNS,
        posts.post_rows(
            read_csv(POSTS_FILE), post_keys, main_keys, categories
        ),
    )
    write_csv(OUTPUT_DIR / "DimMedia.csv", posts.MEDIA_COLUMNS, media_rows)
    write_csv(OUTPUT_DIR / "BridgePostMedia.csv", posts.BRIDGE_COLUMNS, attachments)
    print(f"Associazioni media senza post risolto: {unlinked}")
    return post_keys, main_keys, user_keys


def main():
    start_date, end_date = calendar_bounds(POSTS_FILE, EVENTS_FILE)
    OUTPUT_DIR.mkdir(exist_ok=True)

    write_csv(
        OUTPUT_DIR / "DimDate.csv",
        dimensions.DATE_COLUMNS,
        dimensions.date_rows(start_date, end_date),
    )
    write_csv(
        OUTPUT_DIR / "DimTime.csv",
        dimensions.TIME_COLUMNS,
        dimensions.time_rows(),
    )
    write_csv(
        OUTPUT_DIR / "DimEventType.csv",
        dimensions.EVENT_TYPE_COLUMNS,
        dimensions.event_type_rows(),
    )
    write_csv(
        OUTPUT_DIR / "DimUser.csv",
        dimensions.USER_COLUMNS,
        dimensions.user_rows(read_csv(USERS_FILE)),
    )

    post_keys, main_keys, user_keys = export_posts_and_media()
    arff_keys = events.build_arff_post_keys(read_csv(ARFF_MAPPING_FILE), post_keys)

    write_csv(
        OUTPUT_DIR / "FactEvent.csv",
        events.FACT_COLUMNS,
        events.fact_rows(
            rows=read_csv(EVENTS_FILE),
            main_keys=main_keys,
            arff_keys=arff_keys,
            user_keys=user_keys,
            post_rows=read_csv(OUTPUT_DIR / "DimPost.csv"),
            event_type_rows=read_csv(OUTPUT_DIR / "DimEventType.csv"),
        ),
    )


if __name__ == "__main__":
    main()
