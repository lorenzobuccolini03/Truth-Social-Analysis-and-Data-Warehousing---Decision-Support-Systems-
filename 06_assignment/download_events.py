import json
from contextlib import suppress
from getpass import getpass
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep


SERVER = "131.114.50.57"
DATABASE = "ProjectAdditionalData2627"
USERNAME = "Group_ID_25"
BATCH_SIZE = 2000
MAX_ATTEMPTS = 3
RETRYABLE_STATES = {"08S01", "08001", "HYT00", "HYT01"}
OUTPUT = Path(__file__).with_name("events_sample.json")

COUNT_QUERY = """
SELECT COUNT_BIG(*), COUNT_BIG(DISTINCT event_id), MAX(event_id)
FROM dbo.events;
"""

FIRST_PAGE = """
SELECT TOP (?) *
FROM dbo.events
WHERE event_id <= ?
ORDER BY event_id;
"""

NEXT_PAGE = """
SELECT TOP (?) *
FROM dbo.events
WHERE event_id > ? AND event_id <= ?
ORDER BY event_id;
"""


def read_events(connect, odbc_error, output):
    connection = None

    def query(sql, parameters=()):
        nonlocal connection

        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                if connection is None:
                    connection = connect()
                cursor = connection.cursor()
                try:
                    cursor.execute(sql, parameters)
                    columns = [column[0] for column in cursor.description]
                    return columns, cursor.fetchall()
                finally:
                    with suppress(odbc_error):
                        cursor.close()
            except odbc_error as exc:
                if not exc.args or exc.args[0] not in RETRYABLE_STATES:
                    raise
                if attempt == MAX_ATTEMPTS:
                    raise
                if connection is not None:
                    with suppress(odbc_error):
                        connection.close()
                    connection = None
                print(f"Connessione interrotta ({exc.args[0]}). Riprovo la stessa query.", flush=True)
                sleep(2 * attempt)

    try:
        print("Conteggio degli eventi sul server...", flush=True)
        _, rows = query(COUNT_QUERY)
        total, distinct_ids, upper_id = rows[0]
        if total != distinct_ids:
            raise ValueError("event_id contiene valori mancanti o duplicati.")

        target = (total + 19) // 20
        print(f"Obiettivo: {target:,} eventi su {total:,}.", flush=True)
        last_id = None
        downloaded = 0

        with TemporaryDirectory(dir=output.parent) as folder:
            temporary_file = Path(folder) / output.name
            with temporary_file.open("w", encoding="utf-8", newline="\n") as file:
                file.write("[")
                while downloaded < target:
                    limit = min(BATCH_SIZE, target - downloaded)
                    if last_id is None:
                        columns, rows = query(FIRST_PAGE, (limit, upper_id))
                    else:
                        columns, rows = query(NEXT_PAGE, (limit, last_id, upper_id))
                    if len(rows) != limit:
                        raise RuntimeError("La sorgente è cambiata durante il download.")

                    id_column = next(i for i, name in enumerate(columns) if name.lower() == "event_id")
                    for row in rows:
                        file.write(",\n" if downloaded else "\n")
                        json.dump(dict(zip(columns, row)), file, ensure_ascii=False, default=str)
                        downloaded += 1
                    last_id = rows[-1][id_column]
                    if downloaded == len(rows) or downloaded % 20_000 == 0 or downloaded == target:
                        print(f"{downloaded:,} / {target:,} eventi scaricati.", flush=True)

                file.write("\n]\n")
            temporary_file.replace(output)
        return downloaded
    finally:
        if connection is not None:
            with suppress(odbc_error):
                connection.close()


def main():
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
        return pyodbc.connect(connection_string, autocommit=True, timeout=15)

    count = read_events(connect, pyodbc.Error, OUTPUT)
    print(f"{count:,} eventi salvati in {OUTPUT}.")


if __name__ == "__main__":
    main()
