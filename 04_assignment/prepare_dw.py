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
    post_authors, retruth_references = posts.index_posts(read_csv(POSTS_FILE))
    alias_file = SOURCE_DIR / "truth_id_map.csv"

    aliases = read_csv(alias_file) if alias_file.is_file() else ()
    if not alias_file.is_file():
        print("Mappa degli alias assente: uso i collegamenti main diretti.")

    main_ids = posts.build_main_post_ids(post_authors, read_csv(ARFF_MAPPING_FILE), aliases)
    retruth_flags = posts.classify_retruths(
        retruth_references, main_ids, post_authors, dimensions.TRUMP_SOURCE_USER_ID
    )

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
    media_counts, unlinked = posts.count_media_by_post(read_csv(media_file), main_ids)

    write_csv(
        OUTPUT_DIR / "DimPost.csv",
        posts.POST_COLUMNS,
        posts.post_rows(
            read_csv(POSTS_FILE), main_ids, categories, media_counts, retruth_flags
        ),
    )
    print(f"Associazioni media senza post risolto: {unlinked}")
    return main_ids, post_authors


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
        OUTPUT_DIR / "DimUser.csv",
        dimensions.USER_COLUMNS,
        dimensions.user_rows(read_csv(USERS_FILE)),
    )

    main_ids, post_authors = export_posts_and_media()
    arff_ids = events.build_arff_post_ids(read_csv(ARFF_MAPPING_FILE), post_authors)

    write_csv(
        OUTPUT_DIR / "FactEvent.csv",
        events.FACT_COLUMNS,
        events.fact_rows(
            rows=read_csv(EVENTS_FILE),
            main_ids=main_ids,
            arff_ids=arff_ids,
            post_authors=post_authors,
        ),
    )


if __name__ == "__main__":
    main()
