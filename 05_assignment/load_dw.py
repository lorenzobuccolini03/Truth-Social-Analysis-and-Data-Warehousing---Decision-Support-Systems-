import argparse
import csv
from datetime import date, time
from getpass import getpass
from itertools import islice
from pathlib import Path


SERVER = "131.114.50.57"
DATABASE = "Group_ID_25_DB"
USERNAME = "Group_ID_25"
CSV_DIR = Path(__file__).resolve().parents[1] / "04_assignment" / "output"
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


def load_table(cursor, table, path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        columns = reader.fieldnames

        names = ", ".join(f"[{name.replace(']', ']]')}]" for name in columns)
        parameters = ", ".join("?" for _ in columns)
        sql = f"INSERT INTO dbo.[{table}_python] ({names}) VALUES ({parameters})"

        rows = (
            tuple(convert_value(column, row[column]) for column in columns)
            for row in reader
        )
        return execute_batches(cursor, sql, rows)


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
        f"UID={USERNAME};PWD={{{password}}};Encrypt=yes;TrustServerCertificate=no;"
    )
    connection = pyodbc.connect(connection_string, autocommit=False)

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DB_NAME()")
        print(f"Connesso a {cursor.fetchone()[0]}.", flush=True)

        if not args.load:
            print("Connessione riuscita. Aggiungi --load per caricare i CSV.")
            return

        cursor.execute("SET XACT_ABORT ON")

        for table in TABLES:
            cursor.execute(
                f"SELECT TOP (1) 1 FROM dbo.[{table}_python] WITH (TABLOCKX, HOLDLOCK)"
            )
            if cursor.fetchone() is not None:
                raise RuntimeError(f"{table}_python contiene gia dati. Caricamento interrotto.")

        cursor.fast_executemany = True

        for table in TABLES:
            print(f"Caricamento di {table}_python...", flush=True)
            path = args.csv_dir / f"{table}.csv"
            count = load_table(cursor, table, path)
            print(f"{count:,} righe inviate.", flush=True)

        connection.commit()
        print("Caricamento confermato.")

    except (Exception, KeyboardInterrupt):
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()