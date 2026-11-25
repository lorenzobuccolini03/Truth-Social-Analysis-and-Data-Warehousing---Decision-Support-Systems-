FACT_COLUMNS = (
    "SourceEventID", "IntegratedPostID", "ActorSourceUserID", "PostAuthorSourceUserID",
    "EventDate", "EventHour", "EventMinute", "EventTypeCode",
)

EVENT_TYPE_CODES = {"CR", "LI", "RET", "REP"}


def build_arff_post_ids(rows, post_ids):
    arff_ids = {}
    for row in rows:
        integrated_id = row["integrated_truth_id"]
        if not integrated_id:
            continue
        if integrated_id not in post_ids:
            raise ValueError(f"ID integrato ARFF assente dai post: {integrated_id}")
        arff_ids[row["arff_truth_id"]] = integrated_id
    return arff_ids


def fact_rows(rows, main_ids, arff_ids, post_authors):
    seen_events = set()
    unknown_posts = 0

    for row in rows:
        source_event_id = row["event_id"]
        if not source_event_id or source_event_id in seen_events:
            raise ValueError(f"ID evento mancante o duplicato: {source_event_id!r}")
        seen_events.add(source_event_id)

        source_post_id = row["truth_id"]
        main_id = main_ids.get(source_post_id)
        arff_id = arff_ids.get(source_post_id)
        if main_id and arff_id and main_id != arff_id:
            raise ValueError(f"Riferimento ambiguo al post {source_post_id}")

        integrated_id = main_id or arff_id
        unknown_posts += int(integrated_id is None)
        event_type = row["event_type"]
        if event_type not in EVENT_TYPE_CODES:
            raise ValueError(f"Tipo evento sconosciuto: {event_type!r}")

        timestamp = row["timestamp"]
        hour, minute = (timestamp[11:13], timestamp[14:16]) if len(timestamp) >= 16 else ("", "")

        yield (
            source_event_id,
            integrated_id,
            row["user_id"],
            post_authors.get(integrated_id),
            timestamp[:10],
            hour,
            minute,
            event_type,
        )

    print(f"Eventi con post non risolto: {unknown_posts}")
