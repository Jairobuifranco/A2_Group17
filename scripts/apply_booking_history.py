import sqlite3, pathlib, sys


CANDIDATES = [
    pathlib.Path("instance/sitedata.sqlite"),
    pathlib.Path("sitedata.sqlite"),
]
DB_PATH = next((p for p in CANDIDATES if p.exists()), CANDIDATES[0])

SQL_FILE = pathlib.Path("db/booking_history.sql")

def main():
    if not SQL_FILE.exists():
        print(f"Missing SQL file: {SQL_FILE}")
        sys.exit(1)
    if not DB_PATH.exists():
        print(f"Note: DB file not found, will create: {DB_PATH}")

    with sqlite3.connect(str(DB_PATH)) as db:
        db.execute("PRAGMA foreign_keys = ON;")
        db.executescript(SQL_FILE.read_text(encoding="utf-8"))
    print(f"✅ Booking history applied to {DB_PATH}")

if __name__ == "__main__":
    main()