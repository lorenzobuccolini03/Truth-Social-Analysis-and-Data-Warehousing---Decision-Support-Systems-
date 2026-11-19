import json
from getpass import getpass
from pathlib import Path
from tempfile import TemporaryDirectory


SERVER = "131.114.50.57"
DATABASE = "ProjectAdditionalData2627"
USERNAME = "Group_ID_25"
BATCH_SIZE = 2000
OUTPUT = Path(__file__).with_name("events_sample.json")

QUERY = """
SELECT TOP (5) PERCENT *
FROM dbo.events
ORDER BY NEWID();
"""


def save_events(cursor, output):
    columns = [column[0] for column in cursor.description]
    count = 0

    with TemporaryDirectory(dir=output.parent) as folder:
        temporary_file = Path(folder) / output.name
        with temporary_file.open("w", encoding="utf-8", newline="\n") as file:
            file.write("[")
            while rows := cursor.fetchmany(BATCH_SIZE):
                for row in rows:
                    file.write(",\n" if count else "\n")
                    event = dict(zip(columns, row))
                    json.dump(event, file, ensure_ascii=False, default=str)
                    count += 1

                if count % 100_000 == 0:
                    print(f"{count:,} eventi scaricati.", flush=True)

            file.write("\n]\n")
        temporary_file.replace(output)

    return count


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
        f"UID={USERNAME};PWD={{{password}}};Encrypt=yes;TrustServerCertificate=no;"
    )
    connection = pyodbc.connect(connection_string, autocommit=True)
    try:
        cursor = connection.cursor()
        print("Richiesta del campione del 5% a SQL Server...", flush=True)
        cursor.execute(QUERY)
        count = save_events(cursor, OUTPUT)
        print(f"{count:,} eventi salvati in {OUTPUT}.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
