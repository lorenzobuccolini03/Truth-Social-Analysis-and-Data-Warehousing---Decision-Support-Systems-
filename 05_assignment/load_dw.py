import argparse
import csv
from datetime import date, time
from getpass import getpass
from itertools import islice
from pathlib import Path


SERVER = "131.114.50.57"
DATABASE = "Group_ID_25_DB"
LOGIN = "Group_ID_25"
DEFAULT_CSV_DIR = Path(__file__).resolve().parents[1] / "04_assignment" / "output"
BATCH_SIZE = 2000

TABLES = (
    "DimDate", "DimTime", "DimEventType", "DimUser",
    "DimMedia", "DimPost", "BridgePostMedia", "FactEvent",
)
TEXT_COLUMNS = {
    "Season", "DayPeriod", "EventTypeCode", "EventTypeName",
    "Username", "Category", "MediaURL", "MediaFormat",
}
DATE_COLUMNS = {"FullDate", "AccountCreationDate", "PublicationDate"}


def read_header(path):
    with path.open(encoding="utf-8-sig", newline="") as source:
        return next(csv.reader(source))


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


def batches(rows):
    rows = iter(rows)
    while batch := list(islice(rows, BATCH_SIZE)):
        yield batch


def load_table(cursor, table, path, columns):
    column_names = ", ".join(f"[{name}]" for name in columns)
    placeholders = ", ".join("?" for _ in columns)
    query = f"INSERT INTO dbo.[{table}_python] ({column_names}) VALUES ({placeholders})"
    count = 0
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != columns:
            raise ValueError(f"Intestazione modificata in {path.name}.")
        for batch in batches(reader):
            values = []
            for row in batch:
                if table == "DimPost":
                    row["RetruthedPostKey"] = ""
                values.append(tuple(convert_value(col, row[col]) for col in columns))
            cursor.executemany(query, values)
            count += len(values)
    return count


def load_retruth_references(cursor, path):
    query = "UPDATE dbo.DimPost_python SET RetruthedPostKey = ? WHERE PostKey = ?"
    count = 0
    with path.open(encoding="utf-8-sig", newline="") as source:
        rows = (
            (int(row["RetruthedPostKey"]), int(row["PostKey"]))
            for row in csv.DictReader(source)
            if row["RetruthedPostKey"]
        )
        for batch in batches(rows):
            cursor.executemany(query, batch)
            count += len(batch)
    return count


def check_destination(cursor, files, headers, load):
    cursor.execute("SELECT DB_NAME()")
    database = cursor.fetchone()[0]
    if database != DATABASE:
        raise RuntimeError(f"Database corrente: {database}. Atteso: {DATABASE}.")
    print(f"Connesso a {database}.", flush=True)

    for table, path in files.items():
        destination = f"dbo.[{table}_python]"
        cursor.execute(f"SELECT TOP (0) * FROM {destination}")
        actual = [field[0] for field in cursor.description]
        if headers[table] != actual:
            raise ValueError(f"Le colonne di {path.name} differiscono da {destination}.")
        lock = " WITH (TABLOCKX, HOLDLOCK)" if load else ""
        cursor.execute(f"SELECT COUNT_BIG(*) FROM {destination}{lock}")
        count = cursor.fetchone()[0]
        print(f"{table}_python: {count:,} righe gia presenti.", flush=True)
        if load and count != 0:
            raise RuntimeError(f"{table}_python contiene gia dati.")


def main():
    parser = argparse.ArgumentParser(description="Assignment 5 - caricamento del DW")
    parser.add_argument("--csv-dir", type=Path, default=DEFAULT_CSV_DIR)
    parser.add_argument("--load", action="store_true", help="Esegui il caricamento.")
    args = parser.parse_args()

    files = {name: args.csv_dir / f"{name}.csv" for name in TABLES}
    headers = {name: read_header(path) for name, path in files.items()}

    from mssql_python import connect

    password = "{" + getpass("Password SQL del gruppo: ").replace("}", "}}") + "}"
    connection = connect(
        f"Server={SERVER};Database={DATABASE};UID={LOGIN};PWD={password};"
        "Encrypt=yes;TrustServerCertificate=no;",
        autocommit=False,
    )
    try:
        cursor = connection.cursor()
        cursor.execute("SET XACT_ABORT ON")
        check_destination(cursor, files, headers, args.load)
        if not args.load:
            print("Controllo completato. Esegui con --load per caricare i dati.")
            return

        expected = {}
        for table, path in files.items():
            print(f"Caricamento di {table}_python...", flush=True)
            expected[table] = load_table(cursor, table, path, headers[table])
            print(f"{expected[table]:,} righe inviate.", flush=True)

            if table == "DimPost":
                references = load_retruth_references(cursor, path)
                cursor.execute(
                    "SELECT COUNT_BIG(*) FROM dbo.DimPost_python "
                    "WHERE RetruthedPostKey IS NOT NULL"
                )
                if cursor.fetchone()[0] != references:
                    raise RuntimeError("Il numero di riferimenti ai repost non coincide.")
                print(f"{references:,} riferimenti ai repost impostati.", flush=True)

        for table, count in expected.items():
            cursor.execute(f"SELECT COUNT_BIG(*) FROM dbo.[{table}_python]")
            if cursor.fetchone()[0] != count:
                raise RuntimeError(f"Il conteggio di {table}_python non coincide con il CSV.")

        connection.commit()
        print("Caricamento confermato. Le otto tabelle _python sono popolate.")
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
