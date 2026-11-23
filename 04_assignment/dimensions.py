from datetime import timedelta


DATE_COLUMNS = (
    "DateKey", "FullDate", "Day", "Month", "Year",
    "DayofWeek", "Season",
)
TIME_COLUMNS = ("TimeKey", "Hour", "Minute", "DayPeriod")
EVENT_TYPE_COLUMNS = ("EventTypeKey", "EventTypeCode", "EventTypeName")
USER_COLUMNS = (
    "UserKey", "SourceUserID", "Username", "FollowersCount",
    "FollowingCount", "AccountCreationDate", "IsDonaldTrump",
)

SEASON_BY_MONTH = (
    "Winter", "Winter", "Spring", "Spring", "Spring", "Summer",
    "Summer", "Summer", "Autumn", "Autumn", "Autumn", "Winter",
)


def date_rows(start_date, end_date):
    yield (0, "", "", "", "", "", "Unknown")

    current = start_date
    while current <= end_date:
        date_key = int(current.strftime("%Y%m%d"))
        weekday = current.isoweekday()  # Monday = 1, Sunday = 7

        yield (
            date_key,
            current.isoformat(),
            current.day,
            current.month,
            current.year,
            weekday,
            SEASON_BY_MONTH[current.month - 1],
        )
        current += timedelta(days=1)


def time_rows():
    yield (-1, "", "", "Unknown")

    for hour in range(24):
        for minute in range(60):
            time_key = hour * 100 + minute
            period = "Day" if 8 <= hour < 20 else "Night"
            yield (time_key, hour, minute, period)


def event_type_rows():
    yield (1, "CR", "Creation")
    yield (2, "LI", "Like")
    yield (3, "RET", "Retruth")
    yield (4, "REP", "Reply")


def user_rows(source_rows):
    yield (0, "", "Unknown", "", "", "", 0)

    for user_key, row in enumerate(source_rows, start=1):
        source_user_id = int(row["id_user"])
        yield (
            user_key,
            source_user_id,
            row["username"],
            row["follower_count"],
            row["following_count"],
            row["timestamp_user_creation"],
            int(source_user_id == 27),
        )