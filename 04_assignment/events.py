FACT_COLUMNS = (
    "EventKey", "SourceEventID", "PostKey", "ActorUserKey", "PostAuthorUserKey",
    "EventDateKey", "EventTimeKey", "EventTypeKey",
)


def build_arff_post_keys(rows, post_keys):
    return {
        row["arff_truth_id"]: post_keys[row["integrated_truth_id"]]
        for row in rows
        if row["integrated_truth_id"]
    }


def fact_rows(rows, main_keys, arff_keys, user_keys, post_rows, event_type_rows):
    post_authors = {
        int(row["PostKey"]): user_keys.get(row["SourceAuthorID"], 0)
        for row in post_rows
    }
    event_types = {
        row["EventTypeCode"]: int(row["EventTypeKey"])
        for row in event_type_rows
    }

    seen_events = set()
    unknown_actors = 0
    unknown_posts = 0

    for event_key, row in enumerate(rows, start=1):
        source_event_id = row["event_id"]
        if not source_event_id or source_event_id in seen_events:
            raise ValueError(f"ID evento mancante o duplicato: {source_event_id!r}")
        seen_events.add(source_event_id)

        source_post_id = row["truth_id"]
        main_key = main_keys.get(source_post_id)
        arff_key = arff_keys.get(source_post_id)
        if main_key and arff_key and main_key != arff_key:
            raise ValueError(f"Riferimento ambiguo al post {source_post_id}")

        post_key = main_key or arff_key or 0
        actor_key = user_keys.get(row["user_id"], 0)
        unknown_posts += int(post_key == 0)
        unknown_actors += int(actor_key == 0)

        timestamp = row["timestamp"]
        date_key = int(timestamp[:10].replace("-", "")) if timestamp else 0
        time_key = -1
        if len(timestamp) >= 16:
            hour = int(timestamp[11:13])
            minute = int(timestamp[14:16])
            time_key = hour * 100 + minute

        yield (
            event_key,
            source_event_id,
            post_key,
            actor_key,
            post_authors[post_key],
            date_key,
            time_key,
            event_types[row["event_type"]],
        )

    print(f"Eventi con PostKey Unknown: {unknown_posts}")
    print(f"Eventi con ActorUserKey Unknown: {unknown_actors}")
