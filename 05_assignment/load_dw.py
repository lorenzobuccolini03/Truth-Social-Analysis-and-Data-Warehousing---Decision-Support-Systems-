import argparse
import csv
from contextlib import suppress
from datetime import date, time
from getpass import getpass
from itertools import islice
from pathlib import Path
from time import sleep


SERVER = "131.114.50.57"
DATABASE = "Group_ID_25_DB"
USERNAME = "Group_ID_25"
CSV_DIR = Path(__file__).resolve().parents[1] / "04_assignment" / "output"
BATCH_SIZE = 2000
MAX_LOAD_ATTEMPTS = 3
RETRYABLE_SQL_STATES = {"08S01", "08001", "HYT00", "HYT01"}

TABLES = (
    "DimDate", "DimTime", "DimUser",
    "DimPost", "FactEvent",
)
TEXT_COLUMNS = {
    "Season", "DayPeriod", "EventTypeCode",
    "Username", "Category",
}
DATE_COLUMNS = {"FullDate", "AccountCreationDate", "PublicationDate", "EventDate"}


def convert_value(column, value):
    if value == "":
        return None
    if column in TEXT_COLUMNS:
        return value
    if column in DATE_COLUMNS:
        return date.fromisoformat(value)
    if column == "PublicationTime":
        return time.fromisoformat(value)
    return int(value)


def execute_batches(cursor, sql, rows):
    rows = iter(rows)
    total = 0

    while batch := list(islice(rows, BATCH_SIZE)):
        cursor.executemany(sql, batch)
        total += len(batch)

    return total


def insert_rows(cursor, table, columns, rows):
    names = ", ".join(f"[{name.replace(']', ']]')}]" for name in columns)
    parameters = ", ".join("?" for _ in columns)
    sql = f"INSERT INTO dbo.[{table}_python] ({names}) VALUES ({parameters})"
    return execute_batches(cursor, sql, rows)


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            yield {name: convert_value(name, value) for name, value in row.items()}


def load_dimension(cursor, table, path):
    # SQL Server generates the primary key. DimPost references are resolved after the insert.
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        columns = tuple(name for name in reader.fieldnames if name != "RetruthedIntegratedPostID")
        rows = (tuple(convert_value(col, row[col]) for col in columns) for row in reader)
        return insert_rows(cursor, table, columns, rows)


def read_key_map(cursor, table, key, *source_columns):
    columns = ", ".join(f"[{name}]" for name in source_columns)
    cursor.execute(f"SELECT {columns}, [{key}] FROM dbo.[{table}_python]")
    return {tuple(row[:-1]): row[-1] for row in cursor}


def link_retruths(cursor, path, post_keys):
    updates = (
        (post_keys[(row["RetruthedIntegratedPostID"],)], post_keys[(row["IntegratedPostID"],)])
        for row in read_rows(path)
        if row["RetruthedIntegratedPostID"] is not None
    )
    return execute_batches(
        cursor, "UPDATE dbo.DimPost_python SET RetruthedPostKey = ? WHERE PostKey = ?", updates
    )


def load_events(cursor, path, post_keys):
    user_keys = read_key_map(cursor, "DimUser", "UserKey", "SourceUserID")
    date_keys = read_key_map(cursor, "DimDate", "DateKey", "FullDate")
    time_keys = read_key_map(cursor, "DimTime", "TimeKey", "Hour", "Minute")
    unknown_user = user_keys[(None,)]

    columns = (
        "SourceEventID", "PostKey", "ActorUserKey", "PostAuthorUserKey",
        "EventDateKey", "EventTimeKey", "EventTypeCode",
    )
    rows = (
        (
            row["SourceEventID"],
            post_keys[(row["IntegratedPostID"],)],
            user_keys.get((row["ActorSourceUserID"],), unknown_user),
            user_keys.get((row["PostAuthorSourceUserID"],), unknown_user),
            date_keys[(row["EventDate"],)],
            time_keys[(row["EventHour"], row["EventMinute"])],
            row["EventTypeCode"],
        )
        for row in read_rows(path)
    )
    return insert_rows(cursor, "FactEvent", columns, rows)


def verify_identity_columns(cursor):
    for table in TABLES:
        key = table.removeprefix("Dim").removeprefix("Fact") + "Key"
        cursor.execute("SELECT COLUMNPROPERTY(OBJECT_ID(?), ?, 'IsIdentity')", f"dbo.{table}_python", key)
        if cursor.fetchone()[0] != 1:
            raise RuntimeError(f"Schema da aggiornare: dbo.{table}_python.{key} deve essere IDENTITY.")


def load_warehouse(cursor, csv_dir):
    cursor.execute("SET XACT_ABORT ON")
    verify_identity_columns(cursor)
    cursor.execute("SELECT COL_LENGTH(N'dbo.FactEvent_python', N'EventTypeCode')")
    if cursor.fetchone()[0] is None:
        raise RuntimeError("Aggiorna dbo.FactEvent_python con il DDL dell'Assignment 3.")

    for table in TABLES:
        cursor.execute(
            f"SELECT TOP (1) 1 FROM dbo.[{table}_python] WITH (TABLOCKX, HOLDLOCK)"
        )
        if cursor.fetchone() is not None:
            raise RuntimeError(f"{table}_python contiene gia dati. Caricamento interrotto.")

    cursor.fast_executemany = True

    for table in TABLES:
        print(f"Caricamento di {table}_python...", flush=True)
        path = csv_dir / f"{table}.csv"
        if table == "FactEvent":
            post_keys = read_key_map(cursor, "DimPost", "PostKey", "IntegratedPostID")
            link_retruths(cursor, csv_dir / "DimPost.csv", post_keys)
            count = load_events(cursor, path, post_keys)
        else:
            count = load_dimension(cursor, table, path)
        print(f"{count:,} righe inviate.", flush=True)


def load_with_retries(connect, odbc_error, csv_dir):
    for attempt in range(1, MAX_LOAD_ATTEMPTS + 1):
        connection = None
        try:
            connection = connect()
            cursor = connection.cursor()
            cursor.execute("SELECT DB_NAME()")
            print(f"Connesso a {cursor.fetchone()[0]}.", flush=True)
            load_warehouse(cursor, csv_dir)
            try:
                connection.commit()
            except odbc_error as exc:
                raise RuntimeError(
                    "Esito del commit da verificare in SSMS prima di rilanciare il caricamento."
                ) from exc
        except (Exception, KeyboardInterrupt) as exc:
            if connection is not None:
                with suppress(odbc_error):
                    connection.rollback()
            if (
                attempt == MAX_LOAD_ATTEMPTS
                or not isinstance(exc, odbc_error)
                or not exc.args
                or exc.args[0] not in RETRYABLE_SQL_STATES
            ):
                raise
        else:
            print("Caricamento confermato.", flush=True)
            return
        finally:
            if connection is not None:
                with suppress(odbc_error):
                    connection.close()

        delay = 15 * attempt
        print(
            f"Connessione interrotta. Nuovo tentativo da zero tra {delay} secondi "
            f"({attempt + 1}/{MAX_LOAD_ATTEMPTS}).",
            flush=True,
        )
        sleep(delay)


def main():
    parser = argparse.ArgumentParser(description="Assignment 5 - caricamento del DW")
    parser.add_argument("--csv-dir", type=Path, default=CSV_DIR)
    parser.add_argument("--load", action="store_true", help="Esegui il caricamento.")
    args = parser.parse_args()

    import pyodbc

    available = pyodbc.drivers()
    drivers = ("ODBC Driver 17 for SQL Server", "ODBC Driver 18 for SQL Server")
    driver = next((name for name in drivers if name in available), None)
    if driver is None:
        raise RuntimeError("Microsoft ODBC Driver 17 o 18 per SQL Server mancante.")

    password = getpass("Password SQL del gruppo: ").replace("}", "}}")
    connection_string = (
        f"DRIVER={{{driver}}};SERVER=tcp:{SERVER};DATABASE={DATABASE};"
        f"UID={USERNAME};PWD={{{password}}};Encrypt=yes;TrustServerCertificate=yes;"
    )
    def connect():
        return pyodbc.connect(connection_string, autocommit=False, timeout=15)

    if args.load:
        load_with_retries(connect, pyodbc.Error, args.csv_dir)
        return

    connection = connect()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DB_NAME()")
        print(f"Connesso a {cursor.fetchone()[0]}.", flush=True)
        print("Connessione riuscita. Aggiungi --load per caricare i CSV.")
    finally:
        with suppress(pyodbc.Error):
            connection.close()


if __name__ == "__main__":
    main()
