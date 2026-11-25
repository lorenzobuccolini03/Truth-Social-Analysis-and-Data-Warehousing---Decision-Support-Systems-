from datetime import timedelta


DATE_COLUMNS = (
    "FullDate", "Day", "Month", "Year",
    "DayofWeek", "Season",
)
TIME_COLUMNS = ("Hour", "Minute", "DayPeriod")
USER_COLUMNS = (
    "SourceUserID", "Username", "FollowersCount",
    "FollowingCount", "AccountCreationDate", "IsDonaldTrump",
)

TRUMP_SOURCE_USER_ID = 27

SEASON_BY_MONTH = (
    "Winter", "Winter", "Spring", "Spring", "Spring", "Summer",
    "Summer", "Summer", "Autumn", "Autumn", "Autumn", "Winter",
)


def date_rows(start_date, end_date):
    yield ("", "", "", "", "", "Unknown")

    current = start_date
    while current <= end_date:
        weekday = current.isoweekday()  # Monday = 1, Sunday = 7

        yield (
            current.isoformat(),
            current.day,
            current.month,
            current.year,
            weekday,
            SEASON_BY_MONTH[current.month - 1],
        )
        current += timedelta(days=1)


def time_rows():
    yield ("", "", "Unknown")

    for hour in range(24):
        for minute in range(60):
            period = "Day" if 8 <= hour < 20 else "Night"
            yield (hour, minute, period)


def user_rows(source_rows):
    yield ("", "Unknown", "", "", "", 0)

    for row in source_rows:
        source_user_id = int(row["id_user"])
        yield (
            source_user_id,
            row["username"],
            row["follower_count"],
            row["following_count"],
            row["timestamp_user_creation"],
            int(source_user_id == TRUMP_SOURCE_USER_ID),
        )
